# -*- coding: utf-8 -*-
"""
Core business modules
"""
from app.core.browser_pool import BrowserPool
from app.core.page_analyzer import PageAnalyzer
from app.core.evaluator import Evaluator

# Lazy imports to avoid circular dependencies
# TaskManager and Attacker should be imported directly when needed

__all__ = [
    'BrowserPool', 'PageAnalyzer', 'Evaluator'
]