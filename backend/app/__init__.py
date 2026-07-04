# -*- coding: utf-8 -*-
"""
Flask application factory
"""
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

# Initialize extensions
# Use threading mode for better Python 3.13 compatibility
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


def create_app(config_name='default'):
    """
    Application factory pattern

    Args:
        config_name: Configuration name ('default', 'development', 'production')

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize extensions
    socketio.init_app(app)

    # Inject socketio into task_manager for real-time push
    from app.core.task_manager import task_manager
    task_manager.socketio = socketio
    print('[Init] socketio injected into task_manager')

    # Initialize database
    from app.database.db import init_db
    init_db(app)

    # Register blueprints
    from app.api import register_blueprints
    register_blueprints(app)

    # Register WebSocket events
    from app.api.websocket import register_websocket_events
    register_websocket_events(socketio)

    return app