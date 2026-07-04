# -*- coding: utf-8 -*-
"""
API tests
"""
import pytest
import json
from app import create_app


@pytest.fixture
def app():
    """Create test app"""
    app = create_app(config_name='testing')
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestTaskAPI:
    """Task API tests"""

    def test_create_task(self, client):
        """Test creating a task"""
        response = client.post('/api/v1/tasks', json={
            'url': 'https://example.com/login',
            'name': 'Test Task'
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'task_id' in data['data']

    def test_create_task_missing_url(self, client):
        """Test creating task without URL"""
        response = client.post('/api/v1/tasks', json={
            'name': 'Test Task'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_get_tasks(self, client):
        """Test getting task list"""
        response = client.get('/api/v1/tasks')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_task_not_found(self, client):
        """Test getting non-existent task"""
        response = client.get('/api/v1/tasks/nonexistent_task')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestConfigAPI:
    """Config API tests"""

    def test_get_providers(self, client):
        """Test getting providers"""
        response = client.get('/api/v1/config/providers')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_add_provider(self, client):
        """Test adding a provider"""
        response = client.post('/api/v1/config/providers', json={
            'name': 'test_provider',
            'api_type': 'openai',
            'api_key': 'test_key'
        })

        assert response.status_code in [201, 400]  # 400 if already exists


class TestDictionaryAPI:
    """Dictionary API tests"""

    def test_get_dictionaries(self, client):
        """Test getting dictionaries"""
        response = client.get('/api/v1/dictionaries')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestReportAPI:
    """Report API tests"""

    def test_get_report_not_found(self, client):
        """Test getting non-existent report"""
        response = client.get('/api/v1/reports/nonexistent_task')

        assert response.status_code == 404