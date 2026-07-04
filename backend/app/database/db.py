# -*- coding: utf-8 -*-
"""
Database connection and initialization
"""
import sqlite3
import json
from pathlib import Path
from flask import g, current_app
from datetime import datetime


def get_db():
    """Get database connection for current request context"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    """
    Initialize database with schema

    Args:
        app: Flask application instance
    """
    # Ensure data directory exists
    db_path = Path(app.config['DATABASE_PATH'])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db = get_db()
        db.executescript(get_schema())
        db.commit()

        # 添加缺失的列（迁移）
        try:
            # 检查 providers 表是否有 connected 列
            cursor = db.execute("PRAGMA table_info(providers)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'connected' not in columns:
                db.execute('ALTER TABLE providers ADD COLUMN connected INTEGER DEFAULT 0')
                db.commit()
        except Exception as e:
            print(f"Migration warning: {e}")

    # Register close_db to be called after each request
    app.teardown_appcontext(close_db)


def get_schema():
    """Return database schema SQL"""
    return '''
    -- =====================
    -- 审计任务表
    -- =====================
    CREATE TABLE IF NOT EXISTS audit_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        name TEXT,
        url TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        options TEXT,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME
    );

    -- =====================
    -- 页面分析结果表
    -- =====================
    CREATE TABLE IF NOT EXISTS page_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        url TEXT NOT NULL,
        username_selector TEXT,
        password_selector TEXT,
        submit_selector TEXT,
        has_captcha INTEGER DEFAULT 0,
        captcha_type TEXT,
        captcha_selector TEXT,
        captcha_input_selector TEXT,
        failed_dom_length INTEGER,
        success_keywords TEXT,
        failure_keywords TEXT,
        screenshot_path TEXT,
        analysis_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
    );

    -- =====================
    -- 测试结果表
    -- =====================
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        url TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        success INTEGER DEFAULT 0,
        dom_length INTEGER,
        response_time_ms INTEGER,
        captcha_solved INTEGER,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
    );

    -- =====================
    -- 安全发现表
    -- =====================
    CREATE TABLE IF NOT EXISTS security_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        url TEXT NOT NULL,
        finding_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT,
        description TEXT,
        recommendation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
    );

    -- =====================
    -- 安全评分表
    -- =====================
    CREATE TABLE IF NOT EXISTS security_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        url TEXT NOT NULL,
        overall_score INTEGER,
        weak_password_score INTEGER,
        captcha_score INTEGER,
        lockout_score INTEGER,
        rate_limit_score INTEGER,
        enumeration_score INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
    );

    -- =====================
    -- LLM 提供商配置表
    -- =====================
    CREATE TABLE IF NOT EXISTS providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT,
        api_type TEXT DEFAULT 'openai',
        api_key TEXT,
        base_url TEXT,
        models TEXT,
        default_model TEXT,
        is_active INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        connected INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- =====================
    -- 字典表
    -- =====================
    CREATE TABLE IF NOT EXISTS dictionaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        file_path TEXT,
        count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- =====================
    -- 系统配置表
    -- =====================
    CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        description TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- =====================
    -- 任务日志表
    -- =====================
    CREATE TABLE IF NOT EXISTS task_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        level TEXT DEFAULT 'info',
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES audit_tasks(task_id) ON DELETE CASCADE
    );

    -- =====================
    -- 索引
    -- =====================
    CREATE INDEX IF NOT EXISTS idx_task_status ON audit_tasks(status);
    CREATE INDEX IF NOT EXISTS idx_task_url ON audit_tasks(url);
    CREATE INDEX IF NOT EXISTS idx_result_task ON test_results(task_id);
    CREATE INDEX IF NOT EXISTS idx_result_success ON test_results(success);
    CREATE INDEX IF NOT EXISTS idx_finding_task ON security_findings(task_id);
    CREATE INDEX IF NOT EXISTS idx_log_task ON task_logs(task_id);
    '''


def query_db(query, args=(), one=False):
    """
    Query database and return results

    Args:
        query: SQL query string
        args: Query parameters
        one: Return single result if True

    Returns:
        Query results
    """
    cursor = get_db().execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=()):
    """
    Execute database query (INSERT, UPDATE, DELETE)

    Args:
        query: SQL query string
        args: Query parameters

    Returns:
        Last row id
    """
    db = get_db()
    cursor = db.execute(query, args)
    db.commit()
    return cursor.lastrowid