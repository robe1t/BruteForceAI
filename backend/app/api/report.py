# -*- coding: utf-8 -*-
"""
Report API endpoints
"""
from flask import Blueprint, request, jsonify, send_file
import io

from app.database.models import AuditTask, TestResult, SecurityFinding, SecurityScore, PageAnalysis

report_bp = Blueprint('report', __name__)


@report_bp.route('/reports/<task_id>', methods=['GET'])
def get_report(task_id):
    """获取测试报告"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        # 获取页面分析
        analysis = PageAnalysis.get_by_task_id(task_id)

        # 获取测试结果
        results = TestResult.get_by_task(task_id)
        successful = [r for r in results if r.success]

        # 获取安全发现
        findings = SecurityFinding.get_by_task(task_id)

        # 获取安全评分
        score = SecurityScore.get_by_task_id(task_id)

        # 计算漏洞数量（漏洞 + 弱口令）
        vulnerability_count = len(findings) + len(successful)

        # 构建报告
        report = {
            'task_id': task_id,
            'task_name': task.name,
            'target_url': task.url,
            'scan_time': task.started_at,
            'status': task.status,
            'score': score.overall_score if score else 0,
            'score_description': _get_score_description(score.overall_score if score else 0, vulnerability_count),
            'vulnerability_count': vulnerability_count,
            'score_details': _build_score_details(score, successful),
            'credentials': [{
                'username': c.username,
                'password': c.password,
                'found_at': c.created_at
            } for c in successful],
            'findings': [_build_finding(f) for f in findings],
            'recommendations': _generate_recommendations(findings, analysis)
        }

        return jsonify({
            'success': True,
            'data': report
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@report_bp.route('/reports/<task_id>/export', methods=['GET'])
def export_report(task_id):
    """导出报告"""
    try:
        task = AuditTask.get_by_task_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': {'code': 'TASK_NOT_FOUND', 'message': '任务不存在'}
            }), 404

        # 获取报告数据
        results = TestResult.get_by_task(task_id)
        successful = [r for r in results if r.success]
        findings = SecurityFinding.get_by_task(task_id)
        score = SecurityScore.get_by_task_id(task_id)

        # 生成HTML报告
        html_content = _generate_html_report(task, successful, findings, score)
        return send_file(
            io.BytesIO(html_content.encode('utf-8')),
            as_attachment=True,
            download_name=f'report_{task_id}.html',
            mimetype='text/html'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'EXPORT_ERROR', 'message': str(e)}
        }), 500


def _get_score_description(score, vulnerability_count=0):
    """获取评分描述 - 根据漏洞数量判断"""
    if vulnerability_count == 0:
        return '😊 很安全：未发现任何漏洞'
    elif vulnerability_count <= 2:
        return '😐 一般安全：存在少量漏洞'
    elif vulnerability_count <= 5:
        return '😟 不安全：存在多个漏洞'
    else:
        return '😢 很危险：存在大量漏洞'


def _build_score_details(score, successful):
    """构建评分详情"""
    details = {}

    # 弱口令评分
    weak_count = len(successful)
    if weak_count == 0:
        weak_score = 100
        weak_desc = '未发现弱口令'
    elif weak_count <= 2:
        weak_score = 60
        weak_desc = f'发现{weak_count}个弱口令'
    else:
        weak_score = 20
        weak_desc = f'发现{weak_count}个弱口令'

    details['weak_password'] = {
        'label': '弱口令防护',
        'score': weak_score if not score else (score.weak_password_score or weak_score),
        'description': weak_desc
    }

    # 验证码评分
    details['captcha'] = {
        'label': '验证码有效性',
        'score': score.captcha_score if score else 50,
        'description': '验证码可被识别'
    }

    # 账户锁定评分
    details['lockout'] = {
        'label': '账户锁定',
        'score': score.lockout_score if score else 40,
        'description': '未检测到账户锁定策略'
    }

    # 频率限制评分
    details['rate_limit'] = {
        'label': '频率限制',
        'score': score.rate_limit_score if score else 30,
        'description': '未检测到请求频率限制'
    }

    return details


def _build_finding(finding):
    """构建发现项"""
    return {
        'level': finding.severity,
        'title': finding.title or finding.finding_type,
        'description': finding.description,
        'evidence': None
    }


def _generate_recommendations(findings, analysis):
    """生成修复建议"""
    recommendations = []

    # 基于发现生成建议
    for finding in findings:
        if finding.recommendation:
            recommendations.append(finding.recommendation)

    # 添加默认建议
    if not recommendations:
        recommendations = [
            '1. 强制使用复杂密码策略，定期更换密码',
            '2. 实施账户锁定策略（5次失败后锁定15分钟）',
            '3. 升级验证码为滑块验证或行为验证',
            '4. 添加请求频率限制（如每分钟最多5次尝试）',
            '5. 启用双因素认证增强安全性'
        ]

    return recommendations


def _generate_html_report(task, credentials, findings, score):
    """生成HTML报告"""
    score_value = score.overall_score if score else 0
    vulnerability_count = len(credentials) + len(findings)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>安全审计报告 - {task.name or task.task_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #409eff; padding-bottom: 10px; }}
        h2 {{ color: #409eff; margin-top: 30px; }}
        .info {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0; }}
        .score-section {{ text-align: center; margin: 30px 0; }}
        .score-face {{ font-size: 72px; margin-bottom: 10px; }}
        .score {{ font-size: 48px; font-weight: bold; color: {'#67c23a' if vulnerability_count == 0 else '#909399' if vulnerability_count <= 2 else '#e6a23c' if vulnerability_count <= 5 else '#f56c6c'}; }}
        .score-desc {{ font-size: 18px; margin-top: 10px; }}
        .credential {{ background: #fef0f0; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #f56c6c; }}
        .finding {{ background: #fdf6ec; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #e6a23c; }}
        .recommendation {{ background: #ecf5ff; padding: 10px; margin: 5px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 安全审计报告</h1>

        <div class="info">
            <p><strong>任务名称:</strong> {task.name or '未命名'}</p>
            <p><strong>目标URL:</strong> {task.url}</p>
            <p><strong>扫描时间:</strong> {task.started_at or 'N/A'}</p>
            <p><strong>状态:</strong> {task.status}</p>
        </div>

        <h2>安全评分</h2>
        <div class="score-section">
            <div class="score-face">{'😊' if vulnerability_count == 0 else '😐' if vulnerability_count <= 2 else '😟' if vulnerability_count <= 5 else '😢'}</div>
            <div class="score">{score_value}/100</div>
            <div class="score-desc">{_get_score_description(score_value, vulnerability_count)}</div>
        </div>

        <h2>发现的弱口令 ({len(credentials)})</h2>
        {''.join([f'<div class="credential">👤 {c.username} / 🔑 {c.password}</div>' for c in credentials]) or '<p>未发现弱口令</p>'}

        <h2>安全问题 ({len(findings)})</h2>
        {''.join([f'<div class="finding"><strong>{f.severity}:</strong> {f.title or f.finding_type}<br><small>{f.description or ""}</small></div>' for f in findings]) or '<p>未发现问题</p>'}

        <h2>修复建议</h2>
        {''.join([f'<div class="recommendation">{r}</div>' for r in _generate_recommendations(findings, None)])}
    </div>
</body>
</html>'''

    return html