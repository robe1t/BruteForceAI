# -*- coding: utf-8 -*-
"""
Task API endpoints
"""
import json
import asyncio
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from app.database.models import AuditTask, PageAnalysis, TestResult, Provider, TaskLog
from app.core.task_manager import task_manager

task_bp = Blueprint('task', __name__)


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.get_json() or {}
        print(f'[CreateTask] Received: {data}')

        # 参数验证
        url = data.get('target_url') or data.get('url')
        if not url:
            return jsonify({
                'success': False,
                'error': {'code': 'INVALID_URL', 'message': 'URL不能为空'}
            }), 400

        # 创建任务
        task = AuditTask.create(
            url=url,
            name=data.get('name'),
            options={
                'threads': data.get('threads', 5),
                'delay': data.get('delay', 0),
                'jitter': data.get('jitter', 0),
                'stop_on_success': data.get('stop_on_success', True),
                'enable_captcha': data.get('enable_captcha', True),
                'show_browser': data.get('show_browser', False),
                'username_dict_id': data.get('username_dict_id'),
                'password_dict_id': data.get('password_dict_id'),
                'username_list': data.get('username_list', []),
                'password_list': data.get('password_list', [])
            }
        )

        return jsonify({
            'success': True,
            'data': task.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'CREATE_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        tasks = AuditTask.get_all(status=status, limit=page_size)

        # 构建返回数据，添加进度信息
        items = []
        for t in tasks:
            task_dict = t.to_dict()

            # 获取测试结果计算进度
            results = TestResult.get_by_task(t.task_id)
            current = len(results)
            success_count = sum(1 for r in results if r.success)

            # 从选项中获取总尝试次数
            options = t.get_options()
            total_attempts = options.get('total_attempts', 0)

            # 计算进度百分比
            if t.status == 'completed':
                progress = 100
            elif total_attempts > 0:
                progress = min(100, int((current / total_attempts) * 100))
            else:
                progress = 0

            task_dict['current_index'] = current
            task_dict['total_count'] = total_attempts
            task_dict['progress'] = progress
            task_dict['success_count'] = success_count

            items.append(task_dict)

        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': len(tasks),
                'page': page,
                'page_size': page_size
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        result = task.to_dict()

        # 获取页面分析结果
        analysis = PageAnalysis.get_by_task_id(task_id)
        if analysis:
            result['analysis'] = analysis.to_dict()

        # 获取测试结果统计
        all_results = TestResult.get_by_task(task_id)
        success_results = [r for r in all_results if r.success]
        current = len(all_results)

        # 从options获取总数（优先用预存的total_combinations）
        options = task.get_options() or {}
        total_planned = options.get('total_combinations') or (
            (len(options.get('username_list', [])) or 1) *
            (len(options.get('password_list', [])) or 1)
        )

        # 计算进度百分比
        if task.status == 'completed':
            progress = 100
        elif total_planned > 0 and current > 0:
            progress = min(99, int((current / total_planned) * 100))
        else:
            progress = 0

        # 添加进度信息
        result['current_index'] = current
        result['total_count'] = total_planned
        result['progress'] = progress
        result['success_count'] = len(success_results)
        result['failed_count'] = current - len(success_results)

        # 计算平均响应时间
        if all_results:
            total_time = sum(r.response_time_ms or 0 for r in all_results)
            result['avg_response_time'] = int(total_time / len(all_results))
        else:
            result['avg_response_time'] = 0

        # 获取发现的凭证
        result['credentials'] = [c.to_dict() for c in success_results]

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动任务"""
    try:
        print(f'[StartTask] task_id={task_id}')
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        if task.status == 'running':
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_ALREADY_RUNNING', 'message': '任务已在运行'}
            }), 400

        # 初始化 LLM 客户端（使用默认提供商配置）
        provider = Provider.get_default()
        if provider:
            from app.llm import get_llm_client
            print(f"[TaskAPI] Found default provider: {provider.name}, type: {provider.api_type}, model: {provider.default_model}")
            task_manager.llm_client = get_llm_client(
                api_type=provider.api_type,
                api_key=provider.api_key,
                base_url=provider.base_url,
                model=provider.default_model
            )
            print(f"[TaskAPI] LLM client initialized: {task_manager.llm_client is not None}")
        else:
            print("[TaskAPI] Warning: No default provider configured, will use heuristic analysis only")
            task_manager.llm_client = None

        # 更新任务状态为 pending
        task.update_status('pending')

        # 添加到任务队列
        position = task_manager.add_task(task_id)

        # 获取当前Flask应用实例（不在后台线程中创建new app，避免socketio重新初始化）
        app = current_app._get_current_object()

        def run_processing():
            with app.app_context():
                # Reset browser pool state for the new thread/event loop
                print("[TaskAPI] Resetting browser pool for background thread...")
                task_manager.browser_pool.browser = None
                task_manager.browser_pool.contexts = {}
                task_manager.browser_pool.playwright = None
                task_manager.browser_pool._lock = None
                task_manager.browser_pool._event_loop_id = None

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(task_manager.start_processing())
                except Exception as e:
                    print(f"Task processing error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    loop.close()

        # 只有不在线程中运行时才启动新线程
        if not task_manager.running:
            thread = threading.Thread(target=run_processing, daemon=True)
            thread.start()

        return jsonify({
            'success': True,
            'data': {'queue_position': position, 'message': '任务已加入队列'}
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': {'code': 'START_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        # Stop the task in task manager
        task_manager.stop_task(task_id)

        # Immediately update task status in database
        task.update_status('stopped')

        return jsonify({
            'success': True,
            'message': '任务已停止',
            'data': task.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'STOP_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        if task.status == 'running':
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_RUNNING', 'message': '无法删除运行中的任务'}
            }), 400

        task.delete()

        return jsonify({
            'success': True,
            'message': '任务已删除'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'DELETE_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>/progress', methods=['GET'])
def get_task_progress(task_id):
    """获取任务进度"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        results = TestResult.get_by_task(task_id)
        current = len(results)
        success_count = sum(1 for r in results if r.success)

        # 从options获取总数（优先用预存的total_combinations）
        options = task.get_options() or {}
        total_planned = options.get('total_combinations') or (
            (len(options.get('username_list', [])) or 1) *
            (len(options.get('password_list', [])) or 1)
        )

        # 计算进度百分比
        if task.status == 'completed':
            progress = 100
        elif total_planned > 0 and current > 0:
            progress = min(99, int((current / total_planned) * 100))
        else:
            progress = 0

        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': task.status,
                'total': total_planned,
                'current': current,
                'success_count': success_count,
                'progress': progress
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        limit = int(request.args.get('limit', 500))
        logs = TaskLog.get_by_task(task_id, limit)

        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'logs': [log.to_dict() for log in logs]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@task_bp.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """获取概览统计"""
    try:
        all_tasks = AuditTask.get_all(limit=1000)

        total = len(all_tasks)
        running = sum(1 for t in all_tasks if t.status == 'running')
        completed = sum(1 for t in all_tasks if t.status == 'completed')

        # 统计发现的弱口令数量
        weak_credentials = 0
        for task in all_tasks:
            if task.status == 'completed':
                creds = TestResult.get_successful_by_task(task.task_id)
                weak_credentials += len(creds)

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'running': running,
                'completed': completed,
                'weak_credentials': weak_credentials
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500