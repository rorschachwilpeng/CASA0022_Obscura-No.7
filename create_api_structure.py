#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 API Structure Generator
创建完整的Flask API文件结构
"""

import os

def create_api_structure():
    """创建API文件结构和内容"""
    
    base_path = "api"
    
    print("🚀 创建Obscura No.7 API文件结构...")
    
    # 文件内容定义
    files_content = {
        # 1. schemas/ml_schemas.py - ML API的输入输出Schema
        "schemas/ml_schemas.py": '''#!/usr/bin/env python3
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
''',

        # 2. schemas/common_schemas.py - 通用Schema定义
        "schemas/common_schemas.py": '''#!/usr/bin/env python3
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
''',

        # 3. schemas/__init__.py
        "schemas/__init__.py": '''#!/usr/bin/env python3
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
''',

        # 4. utils/validators.py - 数据验证工具
        "utils/validators.py": '''#!/usr/bin/env python3
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
''',

        # 5. utils/responses.py - 标准响应格式
        "utils/responses.py": '''#!/usr/bin/env python3
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
''',

        # 6. utils/__init__.py
        "utils/__init__.py": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Utils Package
"""

from .validators import validate_json_input, validate_coordinates, validate_hours_ahead
from .responses import success_response, error_response, ml_prediction_response

__all__ = [
    'validate_json_input',
    'validate_coordinates', 
    'validate_hours_ahead',
    'success_response',
    'error_response',
    'ml_prediction_response'
]
''',

        # 7. routes/ml_predict.py - ML预测API端点
        "routes/ml_predict.py": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Prediction API Routes - 机器学习预测API端点
"""

from flask import Blueprint, request
from datetime import datetime
import logging
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from api.schemas import validate_ml_input
from api.utils import validate_json_input, ml_prediction_response, error_response

logger = logging.getLogger(__name__)

# 创建蓝图
ml_bp = Blueprint('ml_predict', __name__, url_prefix='/api/v1/ml')

@ml_bp.route('/predict', methods=['POST'])
@validate_json_input(validate_ml_input)
def predict():
    """
    ML预测API端点
    
    输入：环境数据 + 预测时间
    输出：预测结果
    """
    try:
        data = request.get_json()
        
        env_data_dict = data['environmental_data']
        hours_ahead = data.get('hours_ahead', 24)
        
        # 导入必要的类
        try:
            from WorkFlow.NonRasberryPi_Workflow.local_environment_setup_and_mock_process_validation import (
                EnvironmentalData, MockMLPredictor
            )
        except ImportError:
            logger.error("Failed to import workflow modules")
            return error_response(
                "ML prediction service temporarily unavailable",
                "IMPORT_ERROR",
                503
            )
        
        # 创建EnvironmentalData对象
        env_data = EnvironmentalData(
            latitude=env_data_dict['latitude'],
            longitude=env_data_dict['longitude'],
            temperature=env_data_dict['temperature'],
            humidity=env_data_dict['humidity'],
            pressure=env_data_dict['pressure'],
            wind_speed=env_data_dict['wind_speed'],
            weather_description=env_data_dict['weather_description'],
            timestamp=env_data_dict.get('timestamp', datetime.now().isoformat()),
            location_name=env_data_dict.get('location_name', '')
        )
        
        # 初始化ML预测器
        ml_predictor = MockMLPredictor()
        
        # 执行预测
        prediction = ml_predictor.predict_weather(env_data, hours_ahead)
        
        # 构建响应数据
        prediction_data = {
            "predicted_temperature": prediction.predicted_temperature,
            "predicted_humidity": prediction.predicted_humidity,
            "predicted_weather_condition": prediction.predicted_weather_condition,
            "confidence_score": prediction.confidence_score,
            "prediction_timestamp": prediction.prediction_timestamp,
            "model_version": prediction.model_version
        }
        
        input_summary = {
            "location": f"({env_data.latitude}, {env_data.longitude})",
            "current_conditions": f"{env_data.temperature}°C, {env_data.weather_description}",
            "hours_ahead": hours_ahead
        }
        
        logger.info(f"ML prediction successful for location ({env_data.latitude}, {env_data.longitude})")
        
        return ml_prediction_response(prediction_data, input_summary)
        
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        return error_response(
            "ML prediction processing failed",
            "PREDICTION_ERROR",
            500
        )

@ml_bp.route('/health', methods=['GET'])
def ml_health():
    """ML服务健康检查"""
    try:
        # 尝试导入和初始化ML模块
        from WorkFlow.NonRasberryPi_Workflow.local_environment_setup_and_mock_process_validation import MockMLPredictor
        
        predictor = MockMLPredictor()
        
        return ml_prediction_response(
            {
                "status": "healthy",
                "model_version": predictor.model_version,
                "model_trained": predictor.is_trained
            },
            {
                "service": "ML Prediction API",
                "endpoint": "/api/v1/ml/predict"
            }
        )
        
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        return error_response(
            "ML service unhealthy",
            "HEALTH_CHECK_FAILED",
            503
        )
''',

        # 8. routes/health.py - 健康检查API
        "routes/health.py": '''#!/usr/bin/env python3
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
''',

        # 9. routes/__init__.py
        "routes/__init__.py": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Routes Package
"""

from .ml_predict import ml_bp
from .health import health_bp

__all__ = ['ml_bp', 'health_bp']
''',

        # 10. 更新主app.py文件
        "app_update.py": '''#!/usr/bin/env python3
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

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入路由蓝图
from api.routes import ml_bp, health_bp

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(ml_bp)
app.register_blueprint(health_bp)

# 检查环境变量
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

# 检查工作流可用性
WORKFLOW_AVAILABLE = False
try:
    from WorkFlow.NonRasberryPi_Workflow.local_environment_setup_and_mock_process_validation import WorkflowOrchestrator
    WORKFLOW_AVAILABLE = True
    logger.info("✅ Workflow engine loaded successfully")
except ImportError as e:
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
        cloudinary_status=bool(CLOUDINARY_URL),
        database_status=bool(DATABASE_URL),
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
'''
    }
    
    # 创建所有文件
    created_files = []
    
    for file_path, content in files_content.items():
        full_path = os.path.join(base_path, file_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(full_path)
            print(f"✅ Created: {file_path}")
        except Exception as e:
            print(f"❌ Failed to create {file_path}: {e}")
    
    # 特殊处理：更新主app.py
    try:
        # 备份原有app.py
        if os.path.exists(os.path.join(base_path, "app.py")):
            backup_path = os.path.join(base_path, "app_backup.py")
            os.rename(os.path.join(base_path, "app.py"), backup_path)
            print(f"📦 Backed up original app.py to app_backup.py")
        
        # 创建新的app.py
        new_app_path = os.path.join(base_path, "app.py")
        with open(new_app_path, 'w', encoding='utf-8') as f:
            f.write(files_content["app_update.py"])
        created_files.append(new_app_path)
        print(f"✅ Updated: app.py")
        
    except Exception as e:
        print(f"❌ Failed to update app.py: {e}")
    
    # 总结
    print(f"\n🎉 API结构创建完成！共创建了 {len(created_files)} 个文件")
    print(f"📁 所有文件已保存到: {os.path.abspath(base_path)}")
    
    print("\n📋 创建的文件列表:")
    print("   📄 Schemas (数据格式定义):")
    print("      1. schemas/ml_schemas.py")
    print("      2. schemas/common_schemas.py")
    print("      3. schemas/__init__.py")
    print("   🛠️ Utils (工具函数):")
    print("      4. utils/validators.py")
    print("      5. utils/responses.py")
    print("      6. utils/__init__.py")
    print("   🌐 Routes (API端点):")
    print("      7. routes/ml_predict.py")
    print("      8. routes/health.py")
    print("      9. routes/__init__.py")
    print("   🚀 Main Application:")
    print("      10. app.py (updated)")
    
    print(f"\n💡 下一步操作:")
    print(f"   1. 检查所有文件是否正确创建")
    print(f"   2. 安装可能需要的新依赖: pip install jsonschema")
    print(f"   3. 本地测试: cd api && python app.py")
    print(f"   4. 测试ML API: POST /api/v1/ml/predict")
    print(f"   5. 推送到GitHub并部署到Render")

if __name__ == "__main__":
    create_api_structure()