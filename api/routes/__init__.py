#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Routes Package
"""

from .ml_predict import ml_bp
from .health import health_bp

__all__ = ['ml_bp', 'health_bp']
