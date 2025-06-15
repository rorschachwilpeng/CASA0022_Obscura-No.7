#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Utilities - 标准响应格式工具
"""

from flask import jsonify
from datetime import datetime
from typing import Dict, Any, Optional

def success_response(data: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """创建标准成功响应"""
    response = {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    response.update(data)
    return jsonify(response)

def error_response(error_message: str, error_code: Optional[str] = None, status_code: int = 400) -> tuple:
    """创建标准错误响应"""
    response = {
        "success": False,
        "error": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return jsonify(response), status_code

def ml_prediction_response(prediction_data: Dict[str, Any], input_summary: Dict[str, Any]) -> Dict[str, Any]:
    """创建ML预测专用响应"""
    return success_response({
        "prediction": prediction_data,
        "input_summary": input_summary,
        "api_version": "1.0"
    })
