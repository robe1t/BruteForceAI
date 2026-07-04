# -*- coding: utf-8 -*-
"""
API blueprints registration
"""
from flask import Blueprint


def register_blueprints(app):
    """Register all API blueprints"""
    from app.api.task import task_bp
    from app.api.config_api import config_bp
    from app.api.report import report_bp
    from app.api.dictionary import dict_bp
    from app.api.analyze import analyze_bp

    # Register with proper URL prefixes
    app.register_blueprint(task_bp, url_prefix='/api/v1')
    app.register_blueprint(config_bp, url_prefix='/api/v1')
    app.register_blueprint(report_bp, url_prefix='/api/v1')
    app.register_blueprint(dict_bp, url_prefix='/api/v1')
    app.register_blueprint(analyze_bp, url_prefix='/api/v1')