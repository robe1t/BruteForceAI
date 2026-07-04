# -*- coding: utf-8 -*-
"""
Configuration API endpoints
"""
import json
from flask import Blueprint, request, jsonify

from app.database.models import Provider
from app.llm import get_llm_client

config_bp = Blueprint('config', __name__)


@config_bp.route('/config/providers', methods=['GET'])
def get_providers():
    """获取所有提供商配置"""
    try:
        providers = Provider.get_all()
        return jsonify({
            'success': True,
            'data': {
                'items': [p.to_dict() for p in providers]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/providers', methods=['POST'])
def add_provider():
    """添加提供商"""
    try:
        data = request.get_json() or {}

        name = data.get('name')
        if not name:
            return jsonify({
                'success': False,
                'error': {'code': 'INVALID_NAME', 'message': '提供商名称不能为空'}
            }), 400

        # 检查是否已存在
        existing = Provider.get_by_name(name)
        if existing:
            return jsonify({
                'success': False,
                'error': {'code': 'PROVIDER_EXISTS', 'message': '提供商已存在'}
            }), 400

        provider = Provider.create(
            name=name,
            display_name=data.get('display_name', name),
            api_type=data.get('api_type') or name,
            api_key=data.get('api_key'),
            base_url=data.get('base_url'),
            models=json.dumps(data.get('models', [])),
            default_model=data.get('default_model'),
            is_active=data.get('is_active', True)
        )

        return jsonify({
            'success': True,
            'data': provider.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'CREATE_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/providers/<name>', methods=['PUT'])
def update_provider(name):
    """更新提供商"""
    try:
        provider = Provider.get_by_name(name)
        if not provider:
            return jsonify({
                'success': False,
                'error': {'code': 'PROVIDER_NOT_FOUND', 'message': '提供商不存在'}
            }), 404

        data = request.get_json() or {}
        provider.update(**data)

        return jsonify({
            'success': True,
            'data': provider.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'UPDATE_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/providers/<name>/default', methods=['PUT'])
def set_default_provider(name):
    """设置默认提供商"""
    try:
        provider = Provider.get_by_name(name)
        if not provider:
            return jsonify({
                'success': False,
                'error': {'code': 'PROVIDER_NOT_FOUND', 'message': '提供商不存在'}
            }), 404

        Provider.set_default(name)

        return jsonify({
            'success': True,
            'message': f'{name} 已设置为默认提供商'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'SET_DEFAULT_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/providers/<name>', methods=['DELETE'])
def delete_provider(name):
    """删除提供商"""
    try:
        provider = Provider.get_by_name(name)
        if not provider:
            return jsonify({
                'success': False,
                'error': {'code': 'PROVIDER_NOT_FOUND', 'message': '提供商不存在'}
            }), 404

        # 直接删除
        from app.database.db import execute_db
        execute_db('DELETE FROM providers WHERE name = ?', (name,))

        return jsonify({
            'success': True,
            'message': '提供商已删除'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'DELETE_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/providers/<name>/test', methods=['POST'])
def test_provider(name):
    """测试提供商连接"""
    try:
        provider = Provider.get_by_name(name)
        if not provider:
            return jsonify({
                'success': False,
                'error': {'code': 'PROVIDER_NOT_FOUND', 'message': '提供商不存在'}
            }), 404

        # 检查模型名称是否已配置
        if not provider.default_model:
            return jsonify({
                'success': False,
                'error': {'code': 'MODEL_NOT_SET', 'message': '请先配置模型名称'}
            }), 400

        # 创建LLM客户端并测试
        client = get_llm_client(
            api_type=provider.api_type,
            api_key=provider.api_key,
            base_url=provider.base_url,
            model=provider.default_model
        )

        result = client.test_connection()

        return jsonify({
            'success': result.get('success', False),
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'TEST_ERROR', 'message': str(e)}
        }), 500


# 示例模型名称参考（仅供前端展示参考，用户可自行输入任意模型名称）
EXAMPLE_MODELS = {
    'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o'],
    'anthropic': ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001', 'claude-3-5-sonnet-20241022'],
    'groq': ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'],
    'ollama': ['llama3.2:3b', 'llama3.1:8b', 'mistral:7b'],
}


@config_bp.route('/config/test-llm', methods=['POST'])
def test_llm_connection():
    """
    直接测试LLM连接（不需要保存到数据库）

    请求体:
    {
        "api_type": "openai" | "anthropic",
        "api_key": "xxx",
        "base_url": "https://api.xxx.com",  // 可选
        "model": "gpt-4"  // 必填
    }
    """
    try:
        data = request.get_json() or {}

        api_type = data.get('api_type', 'openai')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        model = data.get('model')

        print(f"[TestLLM] Request data: api_type={api_type}, base_url={base_url}, model={model}, api_key={'*' * 8 if api_key else 'None'}")

        # 参数验证
        if not api_key:
            return jsonify({
                'success': False,
                'error': {'code': 'MISSING_API_KEY', 'message': 'API Key不能为空'}
            }), 400

        if not model:
            return jsonify({
                'success': False,
                'error': {'code': 'MISSING_MODEL', 'message': '模型名称不能为空'}
            }), 400

        # 创建LLM客户端并测试
        client = get_llm_client(
            api_type=api_type,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        print(f"[TestLLM] Client created: {type(client).__name__}")
        result = client.test_connection()
        print(f"[TestLLM] Test result: {result}")

        return jsonify({
            'success': result.get('success', False),
            'data': result
        })

    except Exception as e:
        import traceback
        print(f"[TestLLM] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': {'code': 'TEST_ERROR', 'message': str(e)}
        }), 500


@config_bp.route('/config/example-models', methods=['GET'])
def get_example_models():
    """
    获取示例模型名称列表（仅供参考）

    注意：模型名称由用户自行输入，此接口仅提供常见模型的参考名称
    """
    return jsonify({
        'success': True,
        'data': {
            'models': EXAMPLE_MODELS,
            'note': '模型名称由用户自行输入，以上仅为常见模型的参考名称'
        }
    })