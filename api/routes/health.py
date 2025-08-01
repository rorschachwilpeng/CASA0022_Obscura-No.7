#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查API端点
用于诊断服务器状态和依赖包问题
"""

from flask import Blueprint, jsonify
import sys
import os

# 创建蓝图
health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    """基础健康检查"""
    try:
        return jsonify({
            'status': 'healthy',
            'message': '服务器运行正常',
            'timestamp': '2025-07-31'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}',
            'timestamp': '2025-07-31'
        }), 500

@health_bp.route('/deps', methods=['GET'])
def check_dependencies():
    """检查依赖包"""
    try:
        deps_status = {}
        
        # 检查核心依赖
        core_deps = ['pandas', 'numpy', 'sklearn', 'joblib', 'tensorflow', 'requests', 'flask']
        
        for dep in core_deps:
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'unknown')
                deps_status[dep] = {'available': True, 'version': version}
            except ImportError:
                deps_status[dep] = {'available': False, 'version': None}
        
        return jsonify({
            'status': 'success',
            'dependencies': deps_status,
            'timestamp': '2025-07-31'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'依赖检查失败: {str(e)}',
            'timestamp': '2025-07-31'
        }), 500

@health_bp.route('/simple', methods=['GET'])
def simple_test():
    """最简单的测试"""
    return jsonify({
        'message': 'Hello from simple test',
        'working': True
    })
