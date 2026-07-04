# -*- coding: utf-8 -*-
"""
WebSocket event handlers
"""
from datetime import datetime
from flask_socketio import emit, join_room, leave_room


def register_websocket_events(socketio):
    """注册WebSocket事件处理"""

    @socketio.on('connect')
    def handle_connect():
        """连接事件"""
        emit('connected', {
            'message': 'WebSocket已连接',
            'timestamp': datetime.now().isoformat()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """断开连接事件"""
        print('Client disconnected')

    @socketio.on('subscribe')
    def handle_subscribe(data):
        """订阅任务更新"""
        task_id = data.get('task_id')
        if task_id:
            join_room(task_id)
            emit('subscribed', {
                'task_id': task_id,
                'message': f'已订阅任务 {task_id}'
            })

    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """取消订阅"""
        task_id = data.get('task_id')
        if task_id:
            leave_room(task_id)
            emit('unsubscribed', {'task_id': task_id})


def push_task_progress(socketio, task_id, data):
    """推送任务进度"""
    socketio.emit('task_progress', data, room=task_id)


def push_task_status(socketio, task_id, status):
    """推送任务状态"""
    socketio.emit('task_status', {
        'task_id': task_id,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }, room=task_id)


def push_credential_found(socketio, task_id, username, password):
    """推送弱口令发现"""
    socketio.emit('credential_found', {
        'task_id': task_id,
        'username': username,
        'password': password,
        'timestamp': datetime.now().isoformat()
    }, room=task_id)


def push_log(socketio, task_id, message, level='info'):
    """推送日志"""
    socketio.emit('log', {
        'task_id': task_id,
        'level': level,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, room=task_id)


def push_task_completed(socketio, task_id, summary):
    """推送任务完成"""
    socketio.emit('task_completed', {
        'task_id': task_id,
        'summary': summary,
        'timestamp': datetime.now().isoformat()
    }, room=task_id)