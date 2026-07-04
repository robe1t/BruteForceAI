# -*- coding: utf-8 -*-
"""
Dictionary API endpoints
"""
import os
import uuid
from flask import Blueprint, request, jsonify

from app.database.models import Dictionary

dict_bp = Blueprint('dictionary', __name__)

# 字典存储目录
DICT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'dictionaries')


def ensure_dict_dir():
    """确保字典目录存在"""
    os.makedirs(DICT_DIR, exist_ok=True)


@dict_bp.route('/dictionaries', methods=['GET'])
def get_dictionaries():
    """获取字典列表"""
    try:
        dict_type = request.args.get('type')
        dictionaries = Dictionary.get_all(type=dict_type)

        return jsonify({
            'success': True,
            'data': {
                'items': [d.to_dict() for d in dictionaries]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@dict_bp.route('/dictionaries', methods=['POST'])
def upload_dictionary():
    """上传字典"""
    try:
        ensure_dict_dir()

        # 检查是否是文件上传
        if 'file' in request.files:
            file = request.files['file']
            name = request.form.get('name', file.filename)
            dict_type = request.form.get('type', 'password')

            if not file.filename:
                return jsonify({
                    'success': False,
                    'error': {'code': 'NO_FILE', 'message': '未选择文件'}
                }), 400

            # 保存文件
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            filepath = os.path.join(DICT_DIR, filename)
            file.save(filepath)

            # 统计行数
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                count = sum(1 for line in f if line.strip())

            # 创建记录
            dictionary = Dictionary.create(
                name=name,
                type=dict_type,
                file_path=filepath,
                count=count
            )

            return jsonify({
                'success': True,
                'data': dictionary.to_dict()
            }), 201

        # 处理JSON请求（手动输入）
        else:
            data = request.get_json() or {}
            name = data.get('name')
            dict_type = data.get('type', 'password')
            entries = data.get('entries', [])

            if not name:
                return jsonify({
                    'success': False,
                    'error': {'code': 'INVALID_NAME', 'message': '字典名称不能为空'}
                }), 400

            # 保存文件
            filename = f"{uuid.uuid4().hex}_{name}.txt"
            filepath = os.path.join(DICT_DIR, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(entries))

            # 创建记录
            dictionary = Dictionary.create(
                name=name,
                type=dict_type,
                file_path=filepath,
                count=len(entries)
            )

            return jsonify({
                'success': True,
                'data': dictionary.to_dict()
            }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'UPLOAD_ERROR', 'message': str(e)}
        }), 500


@dict_bp.route('/dictionaries/<int:dict_id>', methods=['GET'])
def get_dictionary(dict_id):
    """获取字典详情"""
    try:
        dictionaries = Dictionary.get_all()
        dictionary = next((d for d in dictionaries if d.id == dict_id), None)

        if not dictionary:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': '字典不存在'}
            }), 404

        return jsonify({
            'success': True,
            'data': dictionary.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@dict_bp.route('/dictionaries/<int:dict_id>', methods=['DELETE'])
def delete_dictionary(dict_id):
    """删除字典"""
    try:
        dictionaries = Dictionary.get_all()
        dictionary = next((d for d in dictionaries if d.id == dict_id), None)

        if not dictionary:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': '字典不存在'}
            }), 404

        # 删除文件
        if dictionary.file_path and os.path.exists(dictionary.file_path):
            os.remove(dictionary.file_path)

        # 删除记录
        from app.database.db import execute_db
        execute_db('DELETE FROM dictionaries WHERE id = ?', (dict_id,))

        return jsonify({
            'success': True,
            'message': '字典已删除'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'DELETE_ERROR', 'message': str(e)}
        }), 500


@dict_bp.route('/dictionaries/<int:dict_id>/content', methods=['GET'])
def get_dictionary_content(dict_id):
    """获取字典内容"""
    try:
        dictionaries = Dictionary.get_all()
        dictionary = next((d for d in dictionaries if d.id == dict_id), None)

        if not dictionary:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': '字典不存在'}
            }), 404

        entries = dictionary.get_entries()

        return jsonify({
            'success': True,
            'data': {
                'items': entries,
                'total': len(entries)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500


@dict_bp.route('/dictionaries/<int:dict_id>/preview', methods=['GET'])
def preview_dictionary(dict_id):
    """预览字典内容"""
    try:
        dictionaries = Dictionary.get_all()
        dictionary = next((d for d in dictionaries if d.id == dict_id), None)

        if not dictionary:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': '字典不存在'}
            }), 404

        limit = int(request.args.get('limit', 50))
        entries = dictionary.get_entries()[:limit]

        return jsonify({
            'success': True,
            'data': {
                'items': entries,
                'total': dictionary.count
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'QUERY_ERROR', 'message': str(e)}
        }), 500