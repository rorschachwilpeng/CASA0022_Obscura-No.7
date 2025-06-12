#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - Railway部署的主应用文件
Flask API服务器
"""

import os
import sys
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json

# 添加WorkFlow路径以导入我们的脚本
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'WorkFlow', 'NonRasberryPi_Workflow'))

try:
    from 1_1_local_environment_setup_and_mock_process_validation import WorkflowOrchestrator
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Workflow module not available: {e}")
    WORKFLOW_AVAILABLE = False

app = Flask(__name__)

# 从环境变量获取API密钥
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@app.route('/')
def home():
    """主页 - 显示API状态"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔭 Obscura No.7 - API Server</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background-color: #d4edda; color: #155724; }
            .warning { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>🔭 Obscura No.7 - Virtual Telescope API</h1>
        <h2>API Status</h2>
        
        <div class="status {{ 'success' if openweather_status else 'error' }}">
            <strong>OpenWeather API:</strong> {{ 'Connected' if openweather_status else 'Not configured' }}
        </div>
        
        <div class="status {{ 'success' if openai_status else 'warning' }}">
            <strong>OpenAI API:</strong> {{ 'Connected' if openai_status else 'Not configured (using mock)' }}
        </div>
        
        <div class="status {{ 'success' if google_maps_status else 'warning' }}">
            <strong>Google Maps API:</strong> {{ 'Connected' if google_maps_status else 'Not configured (using mock)' }}
        </div>
        
        <div class="status {{ 'success' if workflow_status else 'error' }}">
            <strong>Workflow Engine:</strong> {{ 'Available' if workflow_status else 'Not available' }}
        </div>
        
        <h2>API Endpoints</h2>
        <ul>
            <li><code>GET /</code> - This status page</li>
            <li><code>POST /predict</code> - Generate weather prediction and image</li>
            <li><code>GET /health</code> - Health check</li>
        </ul>
        
        <h2>Usage Example</h2>
        <pre>
POST /predict
Content-Type: application/json

{
    "latitude": 51.5074,
    "longitude": -0.1278,
    "hours_ahead": 24
}
        </pre>
        
        <p><em>Deployed on Railway • {{ timestamp }}</em></p>
    </body>
    </html>
    """
    
    return render_template_string(html,
        openweather_status=bool(OPENWEATHER_API_KEY),
        openai_status=bool(OPENAI_API_KEY),
        google_maps_status=bool(GOOGLE_MAPS_API_KEY),
        workflow_status=WORKFLOW_AVAILABLE,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openweather": bool(OPENWEATHER_API_KEY),
            "openai": bool(OPENAI_API_KEY),
            "google_maps": bool(GOOGLE_MAPS_API_KEY),
            "workflow": WORKFLOW_AVAILABLE
        }
    })

@app.route('/predict', methods=['POST'])
def predict():
    """生成天气预测和AI图片"""
    if not WORKFLOW_AVAILABLE:
        return jsonify({
            "error": "Workflow engine not available",
            "message": "Please check server configuration"
        }), 500
    
    try:
        data = request.get_json()
        latitude = data.get('latitude', 51.5074)
        longitude = data.get('longitude', -0.1278)
        hours_ahead = data.get('hours_ahead', 24)
        
        # 初始化工作流
        orchestrator = WorkflowOrchestrator(
            OPENWEATHER_API_KEY,
            OPENAI_API_KEY,
            GOOGLE_MAPS_API_KEY
        )
        
        # 运行预测
        result = orchestrator.run_complete_workflow(
            latitude=latitude,
            longitude=longitude,
            hours_ahead=hours_ahead
        )
        
        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False) 