#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Schemas Package
"""

from .ml_schemas import (
    ML_PREDICT_INPUT_SCHEMA,
    ML_PREDICT_OUTPUT_SCHEMA,
    validate_ml_input,
    validate_ml_output
)

from .common_schemas import (
    ERROR_RESPONSE_SCHEMA,
    SUCCESS_RESPONSE_SCHEMA,
    COORDINATES_SCHEMA
)

__all__ = [
    'ML_PREDICT_INPUT_SCHEMA',
    'ML_PREDICT_OUTPUT_SCHEMA',
    'validate_ml_input',
    'validate_ml_output',
    'ERROR_RESPONSE_SCHEMA',
    'SUCCESS_RESPONSE_SCHEMA',
    'COORDINATES_SCHEMA'
]
