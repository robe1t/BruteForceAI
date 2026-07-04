# -*- coding: utf-8 -*-
"""
Task manager for handling audit task queue and execution
"""
import asyncio
import json
from typing import Optional, List, Dict, Callable, TYPE_CHECKING
from datetime import datetime
import traceback

from app.core.browser_pool import BrowserPool
from app.core.page_analyzer import PageAnalyzer
from app.core.evaluator import Evaluator
from app.database.models import AuditTask, PageAnalysis, TestResult
from app.llm import create_llm_client
from app.captcha.ocr_solver import OCRSolver

if TYPE_CHECKING:
    from app.core.attacker import Attacker


class TaskManager:
    """
    任务管理器 - 队列调度

    Manages task queue and sequential execution of audit tasks.
    """

    def __init__(self, browser_pool: BrowserPool = None, socketio=None):
        """
        Initialize task manager

        Args:
            browser_pool: BrowserPool instance
            socketio: SocketIO instance for real-time updates
        """
        self.browser_pool = browser_pool or BrowserPool()
        self.socketio = socketio

        self.task_queue: List[str] = []  # Queue of task_ids
        self.current_task: Optional[str] = None
        self.running = False
        self.stop_flag = False
        self.pause_flag = False
        self._stopping_task_id: Optional[str] = None  # Track which task is being stopped

        self.llm_client = None
        self.captcha_solver = OCRSolver()

        # Callbacks
        self._on_progress: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

    def set_llm_client(self, provider_config: dict):
        """
        Set LLM client from provider configuration

        Args:
            provider_config: Provider configuration dict
        """
        self.llm_client = create_llm_client(provider_config)

    def add_task(self, task_id: str) -> int:
        """
        Add task to queue

        Args:
            task_id: Task ID to add

        Returns:
            Queue position (1-based)
        """
        if task_id not in self.task_queue and task_id != self.current_task:
            self.task_queue.append(task_id)

        return self.get_queue_position(task_id)

    def remove_task(self, task_id: str) -> bool:
        """
        Remove task from queue

        Args:
            task_id: Task ID to remove

        Returns:
            True if removed, False otherwise
        """
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
            return True
        return False

    def get_queue_position(self, task_id: str) -> int:
        """
        Get task position in queue

        Args:
            task_id: Task ID

        Returns:
            Position in queue (0 if current task, -1 if not found)
        """
        if task_id == self.current_task:
            return 0
        if task_id in self.task_queue:
            return self.task_queue.index(task_id) + 1
        return -1

    def get_status(self) -> dict:
        """
        Get current status

        Returns:
            Status dict with queue info
        """
        return {
            'running': self.running,
            'current_task': self.current_task,
            'queue_length': len(self.task_queue),
            'queue': self.task_queue.copy()
        }

    def stop_task(self, task_id: str):
        """
        Stop a specific task

        Args:
            task_id: Task ID to stop
        """
        if task_id == self.current_task:
            self.stop_flag = True
            # Store the task_id for status update
            self._stopping_task_id = task_id
        elif task_id in self.task_queue:
            self.task_queue.remove(task_id)
            # Update task status in database
            task = AuditTask.get_by_task_id(task_id)
            if task:
                task.update_status('stopped')

    def pause_task(self, task_id: str):
        """Pause current task"""
        if task_id == self.current_task:
            self.pause_flag = True

    def resume_task(self, task_id: str):
        """Resume paused task"""
        if task_id == self.current_task:
            self.pause_flag = False

    async def start_processing(self):
        """Start processing the task queue"""
        if self.running:
            return

        self.running = True
        self.stop_flag = False

        print(f"[TaskManager] Starting processing in event loop: {id(asyncio.get_running_loop())}")
        print(f"[TaskManager] Browser pool event_loop_id: {self.browser_pool._event_loop_id}")

        while self.task_queue and not self.stop_flag:
            # Wait if paused
            while self.pause_flag and not self.stop_flag:
                await asyncio.sleep(1)

            if self.stop_flag:
                break

            # Get next task
            self.current_task = self.task_queue.pop(0)

            try:
                await self._process_task(self.current_task)
            except Exception as e:
                print(f"Error processing task {self.current_task}: {e}")
                traceback.print_exc()
                task = AuditTask.get_by_task_id(self.current_task)
                if task:
                    task.update_status('failed', str(e))

            self.current_task = None

        # If stopped, update the task status that was being stopped
        if self.stop_flag and self._stopping_task_id:
            task = AuditTask.get_by_task_id(self._stopping_task_id)
            if task:
                task.update_status('stopped')
                print(f"[TaskManager] Task {self._stopping_task_id} marked as stopped")
            self._stopping_task_id = None
            self.current_task = None

        self.running = False

    async def _process_task(self, task_id: str):
        """
        Process a single task

        Args:
            task_id: Task ID to process
        """
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return

        # Get options and check show_browser setting
        options = task.get_options()
        show_browser = options.get('show_browser', False)

        # Set browser headless mode based on show_browser option
        if show_browser:
            self._push_log(task_id, "Running in visible browser mode (debug)", "info")
            self.browser_pool.set_headless(False)
        else:
            self.browser_pool.set_headless(True)

        # Update status to analyzing
        task.update_status('analyzing')
        self._push_log(task_id, f"Starting analysis for {task.url}", "info")

        try:
            # Step 1: Analyze page
            analyzer = PageAnalyzer(
                llm_client=self.llm_client,
                browser_pool=self.browser_pool,
                log_callback=self._push_log
            )

            try:
                analysis = await analyzer.analyze(task.url, task_id)
            except Exception as e:
                # Propagate the specific error message
                raise Exception(f"页面分析失败: {str(e)}")

            if not analysis:
                raise Exception("页面分析失败: 无法识别登录表单元素，请确认目标URL是有效的登录页面")

            # Update status to running
            task.update_status('running')

            # Step 2: Execute attack
            # Load dictionaries - support both dict_id and list
            usernames = None
            passwords = None

            # Debug: print all options
            self._push_log(task_id, f"Task options: {options}", "info")

            # Try username_list first (directly provided)
            if options.get('username_list'):
                usernames = options.get('username_list')
                if isinstance(usernames, str):
                    # Handle string format (JSON or newline-separated)
                    try:
                        usernames = json.loads(usernames)
                    except Exception:
                        usernames = usernames.split('\n')
                usernames = [u.strip() for u in usernames if u.strip()]
                self._push_log(task_id, f"Using username_list: {len(usernames)} entries", "info")
            # Try username_dict_id (from database dictionary by ID)
            elif options.get('username_dict_id'):
                from app.database.models import Dictionary
                dict_id = options.get('username_dict_id')
                self._push_log(task_id, f"Looking for username dict with ID: {dict_id} (type: {type(dict_id)})", "info")
                dict_obj = Dictionary.get_by_id(dict_id)
                if dict_obj:
                    usernames = dict_obj.get_entries()
                    self._push_log(task_id, f"Loaded username dict '{dict_obj.name}': {len(usernames)} entries from {dict_obj.file_path}", "info")
                else:
                    self._push_log(task_id, f"Username dict ID {dict_id} not found in database", "warning")
            else:
                usernames = self._load_dictionary(options.get('username_dict'))

            # Try password_list first (directly provided)
            if options.get('password_list'):
                passwords = options.get('password_list')
                if isinstance(passwords, str):
                    # Handle string format (JSON or newline-separated)
                    try:
                        passwords = json.loads(passwords)
                    except Exception:
                        passwords = passwords.split('\n')
                passwords = [p.strip() for p in passwords if p.strip()]
                self._push_log(task_id, f"Using password_list: {len(passwords)} entries", "info")
            # Try password_dict_id (from database dictionary by ID)
            elif options.get('password_dict_id'):
                from app.database.models import Dictionary
                dict_id = options.get('password_dict_id')
                self._push_log(task_id, f"Looking for password dict with ID: {dict_id} (type: {type(dict_id)})", "info")
                dict_obj = Dictionary.get_by_id(dict_id)
                if dict_obj:
                    passwords = dict_obj.get_entries()
                    self._push_log(task_id, f"Loaded password dict '{dict_obj.name}': {len(passwords)} entries from {dict_obj.file_path}", "info")
                else:
                    self._push_log(task_id, f"Password dict ID {dict_id} not found in database", "warning")
            else:
                passwords = self._load_dictionary(options.get('password_dict'))

            # Use defaults if still empty
            if not usernames:
                usernames = ['admin', 'root', 'test', 'user', 'administrator']
                self._push_log(task_id, f"Using default usernames: {usernames}", "warning")
            if not passwords:
                passwords = ['admin', '123456', 'password', 'admin123', 'root', 'test']
                self._push_log(task_id, f"Using default passwords: {passwords}", "warning")

            # Import Attacker here to avoid circular import
            from app.core.attacker import Attacker
            attacker = Attacker(
                browser_pool=self.browser_pool,
                captcha_solver=self.captcha_solver,
                llm_client=self.llm_client,
                task_manager=self
            )

            # 计算并存储总尝试次数
            total_attempts = len(usernames) * len(passwords)
            self._push_log(task_id, f"Starting attack with {len(usernames)} usernames and {len(passwords)} passwords ({total_attempts} total attempts)", "info")

            # 更新任务选项中的总尝试次数
            options['total_attempts'] = total_attempts
            task.update_options(options)

            result = await attacker.execute(
                task_id=task_id,
                url=task.url,
                usernames=usernames,
                passwords=passwords,
                analysis=analysis,
                options=options
            )

            self._push_log(task_id, f"Attack completed. Found {result['success_count']} valid credentials", "info")

            # Step 3: Evaluate security
            evaluator = Evaluator()
            score = evaluator.evaluate(task_id, task.url, analysis, result)

            self._push_log(task_id, f"Security score: {score['overall_score']}/100", "info")

            # Complete task
            task.update_status('completed')

            # Push completion notification
            self._push_event(task_id, 'task_completed', {
                'task_id': task_id,
                'success_count': result['success_count'],
                'overall_score': score['overall_score']
            })

        except Exception as e:
            task.update_status('failed', str(e))
            self._push_log(task_id, f"Task failed: {str(e)}", "error")
            raise

    def _load_dictionary(self, dict_name: str) -> List[str]:
        """
        Load dictionary entries

        Args:
            dict_name: Dictionary name or file path

        Returns:
            List of entries
        """
        if not dict_name:
            # Default dictionaries
            return ['admin', 'root', 'test', 'user']

        # Try to load from file
        try:
            with open(dict_name, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return [dict_name]

    def _push_log(self, task_id: str, message: str, level: str = 'info'):
        """Push log message via WebSocket and save to database"""
        from app.database.models import TaskLog

        # Save to database
        try:
            TaskLog.create(task_id, message, level)
        except Exception as e:
            print(f"[WARNING] Failed to save log to database: {e}")

        # Push via WebSocket
        if self.socketio:
            self.socketio.emit('log', {
                'task_id': task_id,
                'level': level,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, room=task_id)

        print(f"[{level.upper()}] {task_id}: {message}")

    def _push_event(self, task_id: str, event: str, data: dict):
        """Push event via WebSocket"""
        if self.socketio:
            self.socketio.emit(event, data, room=task_id)

    def _push_progress(self, task_id: str, current: int, total: int,
                       username: str = None, password: str = None):
        """Push progress update via WebSocket"""
        data = {
            'task_id': task_id,
            'current': current,
            'total': total,
            'percent': round(current / total * 100, 1) if total > 0 else 0,
            'username': username,
            'password': password
        }

        if self.socketio:
            self.socketio.emit('task_progress', data, room=task_id)


# Global task manager instance
_task_manager_instance = None


def get_task_manager() -> TaskManager:
    """Get or create global task manager instance"""
    global _task_manager_instance

    if _task_manager_instance is None:
        _task_manager_instance = TaskManager(browser_pool=BrowserPool())

    return _task_manager_instance


# Export for convenience
task_manager = get_task_manager()