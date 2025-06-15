#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Check API Routes - 系统健康检查API端点
"""

from flask import Blueprint
import os
from datetime import datetime

from api.utils import success_response

# 创建蓝图
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """系统健康检查端点"""
    
    # 检查环境变量
    services_status = {
        "openweather": bool(os.getenv("OPENWEATHER_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
        "cloudinary": bool(os.getenv("CLOUDINARY_URL")),
        "database": bool(os.getenv("DATABASE_URL"))
    }
    
    # 检查工作流可用性
    workflow_available = False
    try:
        from WorkFlow.NonRasberryPi_Workflow.local_environment_setup_and_mock_process_validation import WorkflowOrchestrator
        workflow_available = True
    except ImportError:
        pass
    
    return success_response({
        "status": "healthy",
        "services": services_status,
        "workflow": workflow_available,
        "version": "1.3.0"
    })
