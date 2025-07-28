#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Check Routes - 健康检查API端点
"""

from flask import Blueprint, jsonify, current_app
import sys
import os

# 创建蓝图
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """基础健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is running'
    }), 200

@health_bp.route('/debug/websocket-status')
def websocket_status():
    """WebSocket状态调试端点"""
    try:
        # 检查SocketIO导入状态
        socketio_imported = False
        socketio_version = None
        socketio_import_error = None
        try:
            import flask_socketio
            socketio_imported = True
            socketio_version = getattr(flask_socketio, '__version__', 'unknown')
        except ImportError as e:
            socketio_import_error = str(e)
        
        # 检查应用中的SocketIO实例
        app_has_socketio = hasattr(current_app, 'socketio')
        socketio_instance = None
        if app_has_socketio:
            socketio_instance = str(type(current_app.socketio))
        
        # 检查环境变量
        python_path = sys.path[:3]  # 只显示前3个路径
        
        return jsonify({
            'websocket_status': {
                'socketio_imported': socketio_imported,
                'socketio_version': socketio_version,
                'socketio_import_error': socketio_import_error if not socketio_imported else None,
                'app_has_socketio': app_has_socketio,
                'socketio_instance_type': socketio_instance,
                'python_path': python_path,
                'flask_app_name': current_app.name
            },
            'status': 'ok',
            'timestamp': '2025-07-28T12:00:00Z'
        }), 200
        
    except Exception as e:
        return jsonify({
            'websocket_status': {
                'error': str(e),
                'error_type': type(e).__name__
            },
            'status': 'error',
            'timestamp': '2025-07-28T12:00:00Z'
        }), 500
