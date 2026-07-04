# -*- coding: utf-8 -*-
"""
Database ORM models
"""
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

from app.database.db import query_db, execute_db, get_db


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{uuid.uuid4().hex[:12]}"


@dataclass
class AuditTask:
    """审计任务模型"""
    id: Optional[int] = None
    task_id: str = ""
    name: Optional[str] = None
    url: str = ""
    status: str = "pending"
    options: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str = None, url: str = "", name: str = None,
               options: dict = None, **kwargs) -> 'AuditTask':
        """Create new task"""
        if task_id is None:
            task_id = generate_task_id()

        options_json = json.dumps(options) if options else None

        execute_db(
            '''INSERT INTO audit_tasks (task_id, name, url, status, options)
               VALUES (?, ?, ?, ?, ?)''',
            (task_id, name, url, 'pending', options_json)
        )

        return cls.get_by_task_id(task_id)

    @classmethod
    def get_by_task_id(cls, task_id: str) -> Optional['AuditTask']:
        """Get task by task_id"""
        row = query_db(
            'SELECT * FROM audit_tasks WHERE task_id = ?',
            (task_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def get_all(cls, status: str = None, limit: int = 100) -> List['AuditTask']:
        """Get all tasks, optionally filtered by status"""
        if status:
            rows = query_db(
                'SELECT * FROM audit_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?',
                (status, limit)
            )
        else:
            rows = query_db(
                'SELECT * FROM audit_tasks ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row) -> 'AuditTask':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            name=row['name'],
            url=row['url'],
            status=row['status'],
            options=row['options'],
            error_message=row['error_message'],
            created_at=row['created_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at']
        )

    def update_status(self, status: str, error_message: str = None):
        """Update task status"""
        now = datetime.now().isoformat()

        if status == 'running':
            execute_db(
                'UPDATE audit_tasks SET status = ?, started_at = ? WHERE task_id = ?',
                (status, now, self.task_id)
            )
        elif status in ('completed', 'failed', 'stopped'):
            execute_db(
                'UPDATE audit_tasks SET status = ?, completed_at = ?, error_message = ? WHERE task_id = ?',
                (status, now, error_message, self.task_id)
            )
        else:
            execute_db(
                'UPDATE audit_tasks SET status = ?, error_message = ? WHERE task_id = ?',
                (status, error_message, self.task_id)
            )

        self.status = status
        self.error_message = error_message

    def get_options(self) -> dict:
        """Parse options JSON"""
        return json.loads(self.options) if self.options else {}

    def update_options(self, options: dict):
        """Update task options"""
        options_json = json.dumps(options) if options else None
        execute_db(
            'UPDATE audit_tasks SET options = ? WHERE task_id = ?',
            (options_json, self.task_id)
        )
        self.options = options_json

    def delete(self):
        """Delete task"""
        execute_db('DELETE FROM audit_tasks WHERE task_id = ?', (self.task_id,))

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        def _to_dt(val):
            if not val:
                return None
            if isinstance(val, datetime):
                return val
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
                try:
                    return datetime.strptime(str(val), fmt)
                except ValueError:
                    continue
            return None

        elapsed = 0
        start_dt = _to_dt(self.started_at)
        if start_dt:
            try:
                end_dt = _to_dt(self.completed_at) or datetime.now()
                elapsed = max(0, (end_dt - start_dt).total_seconds())
            except Exception:
                elapsed = 0

        def _fmt(dt):
            return dt.strftime('%Y-%m-%d %H:%M:%S') if isinstance(dt, datetime) else dt

        return {
            'id': self.id,
            'task_id': self.task_id,
            'name': self.name,
            'url': self.url,
            'target_url': self.url,  # 兼容前端
            'status': self.status,
            'options': self.get_options(),
            'error_message': self.error_message,
            'created_at': _fmt(self.created_at),
            'started_at': _fmt(self.started_at),
            'completed_at': _fmt(self.completed_at),
            'elapsed_time': elapsed
        }


@dataclass
class PageAnalysis:
    """页面分析结果模型"""
    id: Optional[int] = None
    task_id: str = ""
    url: str = ""
    username_selector: Optional[str] = None
    password_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    has_captcha: bool = False
    captcha_type: Optional[str] = None
    captcha_selector: Optional[str] = None
    captcha_input_selector: Optional[str] = None
    failed_dom_length: Optional[int] = None
    success_keywords: Optional[str] = None
    failure_keywords: Optional[str] = None
    screenshot_path: Optional[str] = None
    analysis_json: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str, url: str, **kwargs) -> 'PageAnalysis':
        """Create page analysis record"""
        execute_db(
            '''INSERT INTO page_analyses
               (task_id, url, username_selector, password_selector, submit_selector,
                has_captcha, captcha_type, captcha_selector, captcha_input_selector,
                failed_dom_length, success_keywords, failure_keywords, screenshot_path, analysis_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (task_id, url,
             kwargs.get('username_selector'),
             kwargs.get('password_selector'),
             kwargs.get('submit_selector'),
             1 if kwargs.get('has_captcha') else 0,
             kwargs.get('captcha_type'),
             kwargs.get('captcha_selector'),
             kwargs.get('captcha_input_selector'),
             kwargs.get('failed_dom_length'),
             kwargs.get('success_keywords'),
             kwargs.get('failure_keywords'),
             kwargs.get('screenshot_path'),
             kwargs.get('analysis_json'))
        )

        return cls.get_by_task_id(task_id)

    @classmethod
    def get_by_task_id(cls, task_id: str) -> Optional['PageAnalysis']:
        """Get analysis by task_id"""
        row = query_db(
            'SELECT * FROM page_analyses WHERE task_id = ?',
            (task_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def _from_row(cls, row) -> 'PageAnalysis':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            url=row['url'],
            username_selector=row['username_selector'],
            password_selector=row['password_selector'],
            submit_selector=row['submit_selector'],
            has_captcha=bool(row['has_captcha']),
            captcha_type=row['captcha_type'],
            captcha_selector=row['captcha_selector'],
            captcha_input_selector=row['captcha_input_selector'],
            failed_dom_length=row['failed_dom_length'],
            success_keywords=row['success_keywords'],
            failure_keywords=row['failure_keywords'],
            screenshot_path=row['screenshot_path'],
            analysis_json=row['analysis_json'],
            created_at=row['created_at']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'username_selector': self.username_selector,
            'password_selector': self.password_selector,
            'submit_selector': self.submit_selector,
            'has_captcha': self.has_captcha,
            'captcha_type': self.captcha_type,
            'captcha_selector': self.captcha_selector,
            'captcha_input_selector': self.captcha_input_selector,
            'failed_dom_length': self.failed_dom_length,
            'screenshot_path': self.screenshot_path
        }


@dataclass
class TestResult:
    """测试结果模型"""
    id: Optional[int] = None
    task_id: str = ""
    url: str = ""
    username: str = ""
    password: str = ""
    success: bool = False
    dom_length: Optional[int] = None
    response_time_ms: Optional[int] = None
    captcha_solved: Optional[bool] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str, url: str, username: str, password: str,
               success: bool = False, **kwargs) -> 'TestResult':
        """Create test result"""
        execute_db(
            '''INSERT INTO test_results
               (task_id, url, username, password, success, dom_length,
                response_time_ms, captcha_solved, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (task_id, url, username, password, 1 if success else 0,
             kwargs.get('dom_length'),
             kwargs.get('response_time_ms'),
             1 if kwargs.get('captcha_solved') else 0,
             kwargs.get('error_message'))
        )

        return cls.get_last_by_task(task_id)

    @classmethod
    def get_last_by_task(cls, task_id: str) -> Optional['TestResult']:
        """Get last test result for task"""
        row = query_db(
            'SELECT * FROM test_results WHERE task_id = ? ORDER BY id DESC LIMIT 1',
            (task_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def get_by_task(cls, task_id: str) -> List['TestResult']:
        """Get all test results for task"""
        rows = query_db(
            'SELECT * FROM test_results WHERE task_id = ? ORDER BY created_at',
            (task_id,)
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_successful_by_task(cls, task_id: str) -> List['TestResult']:
        """Get successful test results for task"""
        rows = query_db(
            'SELECT * FROM test_results WHERE task_id = ? AND success = 1',
            (task_id,)
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row) -> 'TestResult':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            url=row['url'],
            username=row['username'],
            password=row['password'],
            success=bool(row['success']),
            dom_length=row['dom_length'],
            response_time_ms=row['response_time_ms'],
            captcha_solved=bool(row['captcha_solved']) if row['captcha_solved'] is not None else None,
            error_message=row['error_message'],
            created_at=row['created_at']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'username': self.username,
            'password': self.password,
            'success': self.success,
            'dom_length': self.dom_length,
            'response_time_ms': self.response_time_ms,
            'captcha_solved': self.captcha_solved,
            'error_message': self.error_message,
            'created_at': self.created_at
        }


@dataclass
class SecurityFinding:
    """安全发现模型"""
    id: Optional[int] = None
    task_id: str = ""
    url: str = ""
    finding_type: str = ""
    severity: str = ""
    title: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str, url: str, finding_type: str,
               severity: str, **kwargs) -> 'SecurityFinding':
        """Create security finding"""
        execute_db(
            '''INSERT INTO security_findings
               (task_id, url, finding_type, severity, title, description, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (task_id, url, finding_type, severity,
             kwargs.get('title'),
             kwargs.get('description'),
             kwargs.get('recommendation'))
        )

        return cls.get_by_task(task_id)[-1] if cls.get_by_task(task_id) else None

    @classmethod
    def get_by_task(cls, task_id: str) -> List['SecurityFinding']:
        """Get all findings for task"""
        rows = query_db(
            'SELECT * FROM security_findings WHERE task_id = ? ORDER BY severity',
            (task_id,)
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row) -> 'SecurityFinding':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            url=row['url'],
            finding_type=row['finding_type'],
            severity=row['severity'],
            title=row['title'],
            description=row['description'],
            recommendation=row['recommendation'],
            created_at=row['created_at']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'finding_type': self.finding_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'recommendation': self.recommendation
        }


@dataclass
class SecurityScore:
    """安全评分模型"""
    id: Optional[int] = None
    task_id: str = ""
    url: str = ""
    overall_score: Optional[int] = None
    weak_password_score: Optional[int] = None
    captcha_score: Optional[int] = None
    lockout_score: Optional[int] = None
    rate_limit_score: Optional[int] = None
    enumeration_score: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str, url: str, **kwargs) -> 'SecurityScore':
        """Create security score"""
        execute_db(
            '''INSERT INTO security_scores
               (task_id, url, overall_score, weak_password_score, captcha_score,
                lockout_score, rate_limit_score, enumeration_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (task_id, url,
             kwargs.get('overall_score'),
             kwargs.get('weak_password_score'),
             kwargs.get('captcha_score'),
             kwargs.get('lockout_score'),
             kwargs.get('rate_limit_score'),
             kwargs.get('enumeration_score'))
        )

        return cls.get_by_task_id(task_id)

    @classmethod
    def get_by_task_id(cls, task_id: str) -> Optional['SecurityScore']:
        """Get score by task_id"""
        row = query_db(
            'SELECT * FROM security_scores WHERE task_id = ?',
            (task_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def _from_row(cls, row) -> 'SecurityScore':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            url=row['url'],
            overall_score=row['overall_score'],
            weak_password_score=row['weak_password_score'],
            captcha_score=row['captcha_score'],
            lockout_score=row['lockout_score'],
            rate_limit_score=row['rate_limit_score'],
            enumeration_score=row['enumeration_score'],
            created_at=row['created_at']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'overall_score': self.overall_score,
            'weak_password_score': self.weak_password_score,
            'captcha_score': self.captcha_score,
            'lockout_score': self.lockout_score,
            'rate_limit_score': self.rate_limit_score,
            'enumeration_score': self.enumeration_score
        }


@dataclass
class Provider:
    """LLM 提供商配置模型"""
    id: Optional[int] = None
    name: str = ""
    display_name: Optional[str] = None
    api_type: str = "openai"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[str] = None
    default_model: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    connected: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, name: str, **kwargs) -> 'Provider':
        """Create provider"""
        execute_db(
            '''INSERT INTO providers (name, display_name, api_type, api_key, base_url, models, default_model, is_active, is_default)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name,
             kwargs.get('display_name'),
             kwargs.get('api_type', 'openai'),
             kwargs.get('api_key'),
             kwargs.get('base_url'),
             kwargs.get('models'),
             kwargs.get('default_model'),
             1 if kwargs.get('is_active', True) else 0,
             1 if kwargs.get('is_default', False) else 0)
        )

        return cls.get_by_name(name)

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Provider']:
        """Get provider by name"""
        row = query_db(
            'SELECT * FROM providers WHERE name = ?',
            (name,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def get_all(cls, active_only: bool = False) -> List['Provider']:
        """Get all providers"""
        if active_only:
            rows = query_db('SELECT * FROM providers WHERE is_active = 1')
        else:
            rows = query_db('SELECT * FROM providers')
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_active(cls) -> Optional['Provider']:
        """Get first active provider"""
        row = query_db(
            'SELECT * FROM providers WHERE is_active = 1 LIMIT 1',
            one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def _from_row(cls, row) -> 'Provider':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            display_name=row['display_name'],
            api_type=row['api_type'],
            api_key=row['api_key'],
            base_url=row['base_url'],
            models=row['models'],
            default_model=row['default_model'],
            is_active=bool(row['is_active']),
            is_default=bool(row['is_default']) if 'is_default' in row.keys() else False,
            connected=bool(row['connected']) if 'connected' in row.keys() else False,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def update(self, **kwargs):
        """Update provider"""
        now = datetime.now().isoformat()
        fields = []
        values = []

        for key in ['display_name', 'api_type', 'api_key', 'base_url', 'models', 'default_model', 'is_active', 'is_default', 'connected']:
            if key in kwargs:
                fields.append(f'{key} = ?')
                if key in ('is_active', 'is_default', 'connected'):
                    values.append(1 if kwargs[key] else 0)
                else:
                    values.append(kwargs[key])

        if fields:
            fields.append('updated_at = ?')
            values.extend([now, self.id])
            execute_db(
                f"UPDATE providers SET {', '.join(fields)} WHERE id = ?",
                values
            )

    def get_models_list(self) -> List[str]:
        """Get list of models"""
        return json.loads(self.models) if self.models else []

    def to_dict(self, include_key: bool = True) -> dict:
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'api_type': self.api_type,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'models': self.get_models_list(),
            'default_model': self.default_model,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'connected': self.connected
        }
        return result

    @classmethod
    def set_default(cls, name: str) -> Optional['Provider']:
        """Set a provider as default (and unset others)"""
        provider = cls.get_by_name(name)
        if not provider:
            return None

        # Unset all other defaults
        execute_db('UPDATE providers SET is_default = 0')
        # Set this one as default
        execute_db('UPDATE providers SET is_default = 1 WHERE name = ?', (name,))

        return cls.get_by_name(name)

    @classmethod
    def get_default(cls) -> Optional['Provider']:
        """Get the default provider"""
        row = query_db(
            'SELECT * FROM providers WHERE is_default = 1 LIMIT 1',
            one=True
        )
        if row:
            return cls._from_row(row)
        # Fallback to first active provider
        return cls.get_active()


@dataclass
class Dictionary:
    """字典模型"""
    id: Optional[int] = None
    name: str = ""
    type: str = ""  # 'username' or 'password'
    file_path: Optional[str] = None
    count: int = 0
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, name: str, type: str, file_path: str = None, count: int = 0) -> 'Dictionary':
        """Create dictionary"""
        execute_db(
            'INSERT INTO dictionaries (name, type, file_path, count) VALUES (?, ?, ?, ?)',
            (name, type, file_path, count)
        )

        return cls.get_by_name(name)

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Dictionary']:
        """Get dictionary by name"""
        row = query_db(
            'SELECT * FROM dictionaries WHERE name = ?',
            (name,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def get_by_id(cls, dict_id: int) -> Optional['Dictionary']:
        """Get dictionary by ID"""
        row = query_db(
            'SELECT * FROM dictionaries WHERE id = ?',
            (dict_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def get_all(cls, type: str = None) -> List['Dictionary']:
        """Get all dictionaries"""
        if type:
            rows = query_db(
                'SELECT * FROM dictionaries WHERE type = ?',
                (type,)
            )
        else:
            rows = query_db('SELECT * FROM dictionaries')
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row) -> 'Dictionary':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            file_path=row['file_path'],
            count=row['count'],
            created_at=row['created_at']
        )

    def get_entries(self) -> List[str]:
        """Get dictionary entries from file"""
        if not self.file_path:
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'file_path': self.file_path,
            'count': self.count,
            'created_at': self.created_at
        }


@dataclass
class TaskLog:
    """任务日志模型"""
    id: Optional[int] = None
    task_id: str = ""
    level: str = "info"
    message: str = ""
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, task_id: str, message: str, level: str = 'info') -> 'TaskLog':
        """Create task log"""
        execute_db(
            'INSERT INTO task_logs (task_id, level, message) VALUES (?, ?, ?)',
            (task_id, level, message)
        )
        return cls.get_last_by_task(task_id)

    @classmethod
    def get_by_task(cls, task_id: str, limit: int = 500) -> List['TaskLog']:
        """Get logs for task"""
        rows = query_db(
            'SELECT * FROM task_logs WHERE task_id = ? ORDER BY created_at DESC LIMIT ?',
            (task_id, limit)
        )
        logs = [cls._from_row(row) for row in rows]
        return list(reversed(logs))  # Return in chronological order

    @classmethod
    def get_last_by_task(cls, task_id: str) -> Optional['TaskLog']:
        """Get last log for task"""
        row = query_db(
            'SELECT * FROM task_logs WHERE task_id = ? ORDER BY id DESC LIMIT 1',
            (task_id,), one=True
        )
        return cls._from_row(row) if row else None

    @classmethod
    def delete_by_task(cls, task_id: str):
        """Delete all logs for task"""
        execute_db('DELETE FROM task_logs WHERE task_id = ?', (task_id,))

    @classmethod
    def _from_row(cls, row) -> 'TaskLog':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            level=row['level'],
            message=row['message'],
            created_at=row['created_at']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'level': self.level,
            'message': self.message,
            'created_at': self.created_at
        }


@dataclass
class SystemConfig:
    """系统配置模型"""
    id: Optional[int] = None
    key: str = ""
    value: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def get(cls, key: str, default: str = None) -> Optional[str]:
        """Get config value by key"""
        row = query_db(
            'SELECT value FROM system_config WHERE key = ?',
            (key,), one=True
        )
        return row['value'] if row else default

    @classmethod
    def set(cls, key: str, value: str, description: str = None):
        """Set config value"""
        existing = query_db(
            'SELECT id FROM system_config WHERE key = ?',
            (key,), one=True
        )

        now = datetime.now().isoformat()

        if existing:
            execute_db(
                'UPDATE system_config SET value = ?, description = ?, updated_at = ? WHERE key = ?',
                (value, description, now, key)
            )
        else:
            execute_db(
                'INSERT INTO system_config (key, value, description, updated_at) VALUES (?, ?, ?, ?)',
                (key, value, description, now)
            )

    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """Get all config values"""
        rows = query_db('SELECT key, value FROM system_config')
        return {row['key']: row['value'] for row in rows}