#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updated Flask Application with Modular Structure
这是更新后的主Flask应用文件，需要替换现有的app.py
"""

import os
import sys
import logging
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import importlib.util

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 从项目根目录加载.env文件
    load_dotenv(os.path.join(project_root, '.env'))
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 导入可选依赖
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

try:
    import psycopg2
    from urllib.parse import urlparse
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# 导入路由蓝图
from api.routes import ml_bp, health_bp
from api.routes.images import images_bp

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(ml_bp)
app.register_blueprint(health_bp)
app.register_blueprint(images_bp)

# 检查环境变量
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

# 配置Cloudinary
CLOUDINARY_CONFIGURED = False
if CLOUDINARY_URL and CLOUDINARY_AVAILABLE:
    try:
        cloudinary.config()
        logger.info("✅ Cloudinary配置成功")
        CLOUDINARY_CONFIGURED = True
    except Exception as e:
        logger.error(f"❌ Cloudinary配置失败: {e}")

# 数据库初始化
DATABASE_INITIALIZED = False
if DATABASE_URL and POSTGRESQL_AVAILABLE:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        DATABASE_INITIALIZED = True
        logger.info("✅ 数据库连接成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")

# 检查工作流可用性
WORKFLOW_AVAILABLE = False
try:
    # 动态导入以数字开头的模块
    module_path = os.path.join(project_root, 'WorkFlow', 'NonRasberryPi_Workflow', '1_1_local_environment_setup_and_mock_process_validation.py')
    spec = importlib.util.spec_from_file_location("workflow_module", module_path)
    workflow_module = importlib.util.module_from_spec(spec)
    sys.modules["workflow_module"] = workflow_module
    spec.loader.exec_module(workflow_module)
    
    # 现在可以访问模块中的类
    WorkflowOrchestrator = workflow_module.WorkflowOrchestrator
    WORKFLOW_AVAILABLE = True
    logger.info("✅ Workflow engine loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ Workflow engine not available: {e}")

@app.route('/')
def home():
    """主页 - 显示API状态和文档"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Obscura No.7 - API Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .healthy { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .unhealthy { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background-color: #e2e3e5; color: #383d41; border: 1px solid #d6d8db; padding: 15px; border-radius: 5px; margin: 20px 0; }
            pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
            h1 { color: #2c3e50; }
            h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔭 Obscura No.7 - API Service</h1>
            <p>Interactive Virtual Telescope Art Installation - Cloud API Service</p>
            
            <h2>Service Status</h2>
            <div class="status {{ 'healthy' if openweather_status else 'unhealthy' }}">
                OpenWeather API: {{ '✅ Connected' if openweather_status else '❌ Not configured' }}
            </div>
            <div class="status {{ 'healthy' if openai_status else 'unhealthy' }}">
                OpenAI API: {{ '✅ Connected' if openai_status else '❌ Not configured' }}
            </div>
            <div class="status {{ 'healthy' if google_maps_status else 'unhealthy' }}">
                Google Maps API: {{ '✅ Connected' if google_maps_status else '❌ Not configured' }}
            </div>
            <div class="status {{ 'healthy' if cloudinary_status else 'unhealthy' }}">
                Cloudinary: {{ '✅ Connected' if cloudinary_status else '❌ Not configured' }}
            </div>
            <div class="status {{ 'healthy' if database_status else 'unhealthy' }}">
                Database: {{ '✅ Connected' if database_status else '❌ Not configured' }}
            </div>
            <div class="status {{ 'healthy' if workflow_status else 'unhealthy' }}">
                ML Workflow: {{ '✅ Available' if workflow_status else '❌ Not available' }}
            </div>
            
            <h2>API Endpoints</h2>
            <ul>
                <li><code>GET /</code> - This status page</li>
                <li><code>GET /health</code> - System health check</li>
                <li><code>POST /api/v1/ml/predict</code> - ML prediction service (Task 1.3)</li>
                <li><code>GET /api/v1/ml/health</code> - ML service health check</li>
                <li><code>POST /predict</code> - Complete workflow (legacy endpoint)</li>
                <li><code>GET /gallery</code> - Prediction history gallery</li>
            </ul>
            
            <h2>ML Prediction API Usage (Task 1.3)</h2>
            <pre>
POST /api/v1/ml/predict
Content-Type: application/json

{
    "environmental_data": {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "temperature": 16.5,
        "humidity": 67,
        "pressure": 1017,
        "wind_speed": 7.2,
        "weather_description": "scattered clouds",
        "location_name": "London"
    },
    "hours_ahead": 24
}
            </pre>
            
            <div class="info">
                <h3>System Information</h3>
                <p><strong>API Version:</strong> 1.3.0</p>
                <p><strong>Task 1.3 Status:</strong> {{ '✅ ML API Ready' if workflow_status else '⚠️ ML API Not Ready' }}</p>
                <p><strong>Last Updated:</strong> {{ timestamp }}</p>
                <p><strong>Deployed on:</strong> Render</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html,
        openweather_status=bool(OPENWEATHER_API_KEY),
        openai_status=bool(OPENAI_API_KEY),
        google_maps_status=bool(GOOGLE_MAPS_API_KEY),
        cloudinary_status=CLOUDINARY_CONFIGURED,
        database_status=DATABASE_INITIALIZED,
        workflow_status=WORKFLOW_AVAILABLE,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

# 保留原有的完整工作流端点（向后兼容）
@app.route('/predict', methods=['POST'])
def legacy_predict():
    """完整工作流端点（向后兼容）"""
    # 这里可以保留你原有的完整predict逻辑
    # 或者重定向到新的模块化端点
    return jsonify({
        "message": "Legacy endpoint. Please use /api/v1/ml/predict for ML-only predictions",
        "new_endpoint": "/api/v1/ml/predict",
        "documentation": "/"
    }), 301

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
