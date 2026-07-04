# -*- coding: utf-8 -*-
"""
Configuration management
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'brute-force-ai-secret-key-2024'

    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or str(BASE_DIR / 'data' / 'bruteforce.db')

    # Upload and data directories
    UPLOAD_FOLDER = str(BASE_DIR / 'data' / 'uploads')
    SCREENSHOT_FOLDER = str(BASE_DIR / 'data' / 'screenshots')

    # Browser settings
    BROWSER_HEADLESS = True
    BROWSER_TIMEOUT = 30000  # 30 seconds

    # Task settings
    MAX_CONCURRENT_TASKS = 1
    TASK_TIMEOUT = 3600  # 1 hour

    # LLM settings
    LLM_TIMEOUT = 120  # 2 minutes
    LLM_MAX_TOKENS = 4096

    # WebSocket
    SOCKETIO_MESSAGE_QUEUE = None

    # API settings
    API_PREFIX = '/api/v1'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    BROWSER_HEADLESS = False  # Show browser in development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    BROWSER_HEADLESS = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = str(BASE_DIR / 'data' / 'test_bruteforce.db')


config = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}