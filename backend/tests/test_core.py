# -*- coding: utf-8 -*-
"""
Core module tests
"""
import pytest
import asyncio


@pytest.fixture
def app():
    """Create test app"""
    from app import create_app
    app = create_app(config_name='testing')
    return app


class TestBrowserPool:
    """Browser pool tests"""

    @pytest.mark.asyncio
    async def test_browser_pool_singleton(self):
        """Test browser pool singleton pattern"""
        from app.core.browser_pool import BrowserPool

        pool1 = BrowserPool()
        pool2 = BrowserPool()

        assert pool1 is pool2

    @pytest.mark.asyncio
    async def test_normalize_domain(self):
        """Test domain normalization"""
        from app.core.browser_pool import BrowserPool

        pool = BrowserPool()

        assert pool._normalize_domain('https://example.com/login') == 'example.com'
        assert pool._normalize_domain('http://test.com') == 'test.com'
        assert pool._normalize_domain('plain.domain') == 'plain.domain'


class TestEvaluator:
    """Security evaluator tests"""

    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        from app.core.evaluator import Evaluator

        evaluator = Evaluator()

        scores = {
            'weak_password_score': 80,
            'captcha_score': 60,
            'lockout_score': 70,
            'rate_limit_score': 50,
            'enumeration_score': 90
        }

        overall = evaluator._calculate_overall(scores)

        assert 0 <= overall <= 100

    def test_evaluate_weak_password(self, app):
        """Test weak password evaluation"""
        from app.core.evaluator import Evaluator

        evaluator = Evaluator()

        with app.app_context():
            # No weak passwords
            result = evaluator._evaluate_weak_password('task_1', 'http://test.com', {
                'total': 100,
                'success_count': 0,
                'credentials_found': []
            })
            assert result == 100

            # Many weak passwords
            result = evaluator._evaluate_weak_password('task_1', 'http://test.com', {
                'total': 100,
                'success_count': 50,
                'credentials_found': list(range(50))
            })
            assert result < 50


class TestTaskManager:
    """Task manager tests"""

    def test_add_task(self):
        """Test adding task to queue"""
        from app.core.task_manager import TaskManager
        from app.core.browser_pool import BrowserPool

        tm = TaskManager(browser_pool=BrowserPool())

        position = tm.add_task('test_task_1')

        assert position >= 0

    def test_get_status(self):
        """Test getting status"""
        from app.core.task_manager import TaskManager
        from app.core.browser_pool import BrowserPool

        tm = TaskManager(browser_pool=BrowserPool())

        status = tm.get_status()

        assert 'running' in status
        assert 'queue_length' in status
        assert 'queue' in status