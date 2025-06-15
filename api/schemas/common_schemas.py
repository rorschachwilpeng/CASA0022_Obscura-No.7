#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Schemas - 通用数据格式定义
"""

# 标准错误响应Schema
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["success", "error", "timestamp"],
    "properties": {
        "success": {"type": "boolean", "enum": [False]},
        "error": {"type": "string"},
        "error_code": {"type": "string"},
        "timestamp": {"type": "string"}
    }
}

# 标准成功响应Schema
SUCCESS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["success", "timestamp"],
    "properties": {
        "success": {"type": "boolean", "enum": [True]},
        "timestamp": {"type": "string"}
    }
}

# 地理坐标Schema
COORDINATES_SCHEMA = {
    "type": "object",
    "required": ["latitude", "longitude"],
    "properties": {
        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180}
    }
}
