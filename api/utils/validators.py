#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation Utilities - 数据验证工具
"""

from flask import jsonify
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_json_input(schema_validator):
    """装饰器：验证JSON输入数据"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "No JSON data provided",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # 使用提供的验证器验证数据
                schema_validator(data)
                
                # 验证通过，继续执行原函数
                return f(*args, **kwargs)
                
            except ValueError as e:
                logger.warning(f"Validation error: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "error_code": "VALIDATION_ERROR",
                    "timestamp": datetime.now().isoformat()
                }), 400
            except Exception as e:
                logger.error(f"Unexpected validation error: {e}")
                return jsonify({
                    "success": False,
                    "error": "Internal validation error",
                    "timestamp": datetime.now().isoformat()
                }), 500
                
        return decorated_function
    return decorator

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """验证地理坐标"""
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180")
    return True

def validate_hours_ahead(hours: int) -> bool:
    """验证预测时间范围"""
    if not (1 <= hours <= 168):  # 1小时到7天
        raise ValueError(f"Invalid hours_ahead: {hours}. Must be between 1 and 168")
    return True
