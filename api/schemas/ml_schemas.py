#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML API Schemas - 机器学习API的输入输出数据格式定义
"""

import jsonschema
from typing import Dict, Any

# ML预测API输入Schema
ML_PREDICT_INPUT_SCHEMA = {
    "type": "object",
    "required": ["environmental_data", "hours_ahead"],
    "properties": {
        "environmental_data": {
            "type": "object",
            "required": ["latitude", "longitude", "temperature", "humidity", "pressure", "wind_speed", "weather_description"],
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                "temperature": {"type": "number", "minimum": -50, "maximum": 60},
                "humidity": {"type": "number", "minimum": 0, "maximum": 100},
                "pressure": {"type": "number", "minimum": 800, "maximum": 1200},
                "wind_speed": {"type": "number", "minimum": 0, "maximum": 100},
                "weather_description": {"type": "string", "minLength": 1},
                "location_name": {"type": "string"},
                "timestamp": {"type": "string"}
            }
        },
        "hours_ahead": {"type": "integer", "minimum": 1, "maximum": 168}  # 最多7天
    }
}

# ML预测API输出Schema
ML_PREDICT_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["success", "prediction", "api_version", "timestamp"],
    "properties": {
        "success": {"type": "boolean"},
        "prediction": {
            "type": "object",
            "required": ["predicted_temperature", "predicted_humidity", "predicted_weather_condition", "confidence_score"],
            "properties": {
                "predicted_temperature": {"type": "number"},
                "predicted_humidity": {"type": "number", "minimum": 0, "maximum": 100},
                "predicted_weather_condition": {"type": "string"},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                "prediction_timestamp": {"type": "string"},
                "model_version": {"type": "string"}
            }
        },
        "input_summary": {"type": "object"},
        "api_version": {"type": "string"},
        "timestamp": {"type": "string"}
    }
}

def validate_ml_input(data: Dict[str, Any]) -> bool:
    """验证ML API输入数据"""
    try:
        jsonschema.validate(data, ML_PREDICT_INPUT_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Input validation failed: {e.message}")

def validate_ml_output(data: Dict[str, Any]) -> bool:
    """验证ML API输出数据"""
    try:
        jsonschema.validate(data, ML_PREDICT_OUTPUT_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Output validation failed: {e.message}")
