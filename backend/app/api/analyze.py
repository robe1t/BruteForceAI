# -*- coding: utf-8 -*-
"""
Analyze API endpoints
"""
from flask import Blueprint, request, jsonify

from app.database.models import AuditTask, PageAnalysis
from app.core.browser_pool import BrowserPool
from app.core.page_analyzer import PageAnalyzer
from app.llm import create_llm_client


analyze_bp = Blueprint('analyze', __name__)


@analyze_bp.route('/analyze', methods=['POST'])
def analyze_page():
    """
    Analyze a login page without creating a task

    Request body:
    {
        "url": "https://example.com/login",
        "provider_id": 1  // Optional: use specific LLM provider
    }
    """
    data = request.get_json()

    url = data.get('url')
    if not url:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_URL',
                'message': 'URL 不能为空'
            }
        }), 400

    if not url.startswith(('http://', 'https://')):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_URL',
                'message': 'URL 格式无效'
            }
        }), 400

    try:
        import asyncio

        # Get LLM client
        from app.database.models import Provider

        provider_id = data.get('provider_id')
        if provider_id:
            provider = Provider.get_by_name(provider_id) or Provider.get_active()
        else:
            provider = Provider.get_active()

        llm_client = None
        if provider:
            llm_client = create_llm_client({
                'api_type': provider.api_type,
                'api_key': provider.api_key,
                'base_url': provider.base_url,
                'default_model': provider.default_model
            })

        # Run analysis
        async def run_analysis():
            browser_pool = BrowserPool()
            analyzer = PageAnalyzer(
                llm_client=llm_client,
                browser_pool=browser_pool
            )
            result = await analyzer.analyze(url, 'temp_analysis')
            await browser_pool.cleanup()
            return result

        result = asyncio.run(run_analysis())

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ANALYSIS_FAILED',
                    'message': '页面分析失败，请检查 URL 是否可访问'
                }
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYSIS_ERROR',
                'message': str(e)
            }
        }), 500


@analyze_bp.route('/analyze/<task_id>', methods=['GET'])
def get_analysis(task_id):
    """Get analysis result for a task"""
    analysis = PageAnalysis.get_by_task_id(task_id)

    if not analysis:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYSIS_NOT_FOUND',
                'message': '分析结果不存在'
            }
        }), 404

    return jsonify({
        'success': True,
        'data': analysis.to_dict()
    })


@analyze_bp.route('/analyze/reanalyze/<task_id>', methods=['POST'])
def reanalyze_task(task_id):
    """Re-analyze a task's URL"""
    task = AuditTask.get_by_task_id(task_id)

    if not task:
        return jsonify({
            'success': False,
            'error': {
                'code': 'TASK_NOT_FOUND',
                'message': '任务不存在'
            }
        }), 404

    try:
        import asyncio

        # Get LLM client
        from app.database.models import Provider
        provider = Provider.get_active()

        llm_client = None
        if provider:
            llm_client = create_llm_client({
                'api_type': provider.api_type,
                'api_key': provider.api_key,
                'base_url': provider.base_url,
                'default_model': provider.default_model
            })

        # Run analysis
        async def run_analysis():
            browser_pool = BrowserPool()
            analyzer = PageAnalyzer(
                llm_client=llm_client,
                browser_pool=browser_pool
            )
            result = await analyzer.analyze(task.url, task_id)
            await browser_pool.cleanup()
            return result

        result = asyncio.run(run_analysis())

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ANALYSIS_FAILED',
                    'message': '页面分析失败'
                }
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYSIS_ERROR',
                'message': str(e)
            }
        }), 500