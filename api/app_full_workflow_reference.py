#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REFERENCE ONLY - 完整工作流参考实现
此文件包含完整的数据库、Cloudinary、图片处理功能
在Stage 2后续开发中可能需要参考
当前使用的是模块化版本: app.py
"""

import os
import sys
import importlib.util
import logging
import time
import tempfile
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json

# 导入Cloudinary和数据库依赖
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    print("⚠️  Cloudinary库未安装，请添加到requirements.txt")

try:
    import psycopg2
    from urllib.parse import urlparse
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    print("⚠️  psycopg2库未安装，请添加到requirements.txt")

# 添加WorkFlow路径
workflow_path = os.path.join(os.path.dirname(__file__), 'WorkFlow', 'NonRasberryPi_Workflow')
sys.path.insert(0, workflow_path)

# 使用importlib动态导入模块
try:
    spec = importlib.util.spec_from_file_location(
        "workflow_module", 
        os.path.join(workflow_path, "1_1_local_environment_setup_and_mock_process_validation.py")
    )
    workflow_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(workflow_module)
    WorkflowOrchestrator = workflow_module.WorkflowOrchestrator
    WORKFLOW_AVAILABLE = True
except Exception as e:
    print(f"Warning: Workflow module not available: {e}")
    WORKFLOW_AVAILABLE = False
    WorkflowOrchestrator = None

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取API密钥
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

# 配置Cloudinary
if CLOUDINARY_URL and CLOUDINARY_AVAILABLE:
    # Cloudinary会自动从CLOUDINARY_URL解析配置
    try:
        cloudinary.config()
        logger.info("✅ Cloudinary配置成功")
        CLOUDINARY_CONFIGURED = True
    except Exception as e:
        logger.error(f"❌ Cloudinary配置失败: {e}")
        CLOUDINARY_CONFIGURED = False
else:
    CLOUDINARY_CONFIGURED = False

# 数据库连接函数
def get_db_connection():
    """获取数据库连接"""
    if not DATABASE_URL or not POSTGRESQL_AVAILABLE:
        return None
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# 初始化数据库表
def init_database():
    """初始化数据库表"""
    if not DATABASE_URL or not POSTGRESQL_AVAILABLE:
        return False
    
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # 创建预测记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                current_temperature FLOAT,
                predicted_temperature FLOAT,
                current_humidity FLOAT,
                predicted_humidity FLOAT,
                weather_description TEXT,
                predicted_weather_condition TEXT,
                image_url TEXT,
                image_filename TEXT,
                location_name TEXT,
                formatted_address TEXT,
                confidence_score FLOAT,
                execution_time FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                full_data JSONB
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ 数据库表初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False

# 在应用启动时初始化数据库
DATABASE_INITIALIZED = init_database()

# 图片上传到Cloudinary
def upload_to_cloudinary(image_path, public_id_prefix="obscura"):
    """上传图片到Cloudinary"""
    if not CLOUDINARY_CONFIGURED:
        logger.warning("Cloudinary未配置，跳过上传")
        return None
        
    try:
        timestamp = int(time.time())
        result = cloudinary.uploader.upload(
            image_path,
            public_id=f"{public_id_prefix}_{timestamp}",
            folder="obscura-no7",
            resource_type="image"
        )
        logger.info(f"✅ 图片上传成功: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        logger.error(f"❌ Cloudinary上传失败: {e}")
        return None

# 保存预测数据到数据库
def save_prediction_to_db(result_data, image_url):
    """保存预测数据到数据库"""
    if not DATABASE_INITIALIZED:
        logger.warning("数据库未初始化，跳过保存")
        return None
        
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        env_data = result_data.get('environmental_data', {})
        pred_data = result_data.get('prediction_result', {})
        loc_data = result_data.get('location_data', {})
        meta_data = result_data.get('workflow_metadata', {})
        
        # 转换所有数值为标准Python类型，避免numpy数据类型问题
        def convert_to_python_type(value):
            """将numpy数据类型转换为Python标准数据类型"""
            if hasattr(value, 'item'):  # numpy数据类型有item()方法
                return value.item()
            return value
        
        cursor.execute("""
            INSERT INTO predictions (
                latitude, longitude, current_temperature, predicted_temperature,
                current_humidity, predicted_humidity, weather_description, 
                predicted_weather_condition, image_url, location_name,
                formatted_address, confidence_score, execution_time, full_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            convert_to_python_type(env_data.get('latitude')),
            convert_to_python_type(env_data.get('longitude')),
            convert_to_python_type(env_data.get('temperature')),
            convert_to_python_type(pred_data.get('predicted_temperature')),
            convert_to_python_type(env_data.get('humidity')),
            convert_to_python_type(pred_data.get('predicted_humidity')),
            env_data.get('weather_description'),
            pred_data.get('predicted_weather_condition'),
            image_url,
            env_data.get('location_name'),
            loc_data.get('formatted_address'),
            convert_to_python_type(pred_data.get('confidence_score')),
            convert_to_python_type(meta_data.get('execution_time_seconds')),
            json.dumps(result_data)
        ))
        
        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ 预测数据保存成功，ID: {record_id}")
        return record_id
        
    except Exception as e:
        logger.error(f"❌ 数据库保存失败: {e}")
        return None

@app.route('/')
def home():
    """主页 - 显示API状态"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔭 Obscura No.7 - API Server</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background-color: #d4edda; color: #155724; }
            .warning { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; }
            .info { background-color: #d1ecf1; color: #0c5460; }
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
        
        <div class="status {{ 'success' if cloudinary_status else 'warning' }}">
            <strong>Cloudinary Storage:</strong> {{ 'Connected' if cloudinary_status else 'Not configured (using local storage)' }}
        </div>
        
        <div class="status {{ 'success' if database_status else 'warning' }}">
            <strong>PostgreSQL Database:</strong> {{ 'Connected' if database_status else 'Not configured (no data persistence)' }}
        </div>
        
        <div class="status {{ 'success' if workflow_status else 'error' }}">
            <strong>Workflow Engine:</strong> {{ 'Available' if workflow_status else 'Not available' }}
        </div>
        
        <h2>API Endpoints</h2>
        <ul>
            <li><code>GET /</code> - This status page</li>
            <li><code>POST /predict</code> - Generate weather prediction and image</li>
            <li><code>GET /health</code> - Health check</li>
            <li><code>GET /gallery</code> - View prediction history (if database connected)</li>
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
        
        <div class="info">
            <h3>System Information</h3>
            <p><strong>Total Predictions:</strong> {{ total_predictions }}</p>
            <p><strong>Last Updated:</strong> {{ timestamp }}</p>
            <p><strong>Deployed on:</strong> Render</p>
        </div>
    </body>
    </html>
    """
    
    # 获取预测总数
    total_predictions = 0
    if DATABASE_INITIALIZED:
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM predictions;")
                total_predictions = cursor.fetchone()[0]
                cursor.close()
                conn.close()
        except:
            pass
    
    return render_template_string(html,
        openweather_status=bool(OPENWEATHER_API_KEY),
        openai_status=bool(OPENAI_API_KEY),
        google_maps_status=bool(GOOGLE_MAPS_API_KEY),
        cloudinary_status=CLOUDINARY_CONFIGURED,
        database_status=DATABASE_INITIALIZED,
        workflow_status=WORKFLOW_AVAILABLE,
        total_predictions=total_predictions,
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
            "cloudinary": CLOUDINARY_CONFIGURED,
            "database": DATABASE_INITIALIZED,
            "workflow": WORKFLOW_AVAILABLE
        },
        "version": "1.2.0"
    })

@app.route('/predict', methods=['POST'])
def predict():
    """生成天气预测和AI图片 (集成Cloudinary + PostgreSQL)"""
    if not WORKFLOW_AVAILABLE or not WorkflowOrchestrator:
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
        
        # 上传图片到Cloudinary
        image_url = None
        if result.get('generated_image', {}).get('image_path'):
            local_image_path = result['generated_image']['image_path']
            image_url = upload_to_cloudinary(local_image_path)
            
            # 更新结果中的图片URL
            if image_url:
                result['generated_image']['cloudinary_url'] = image_url
                result['generated_image']['generation_method'] = 'openai_cloudinary'
        
        # 保存到数据库
        record_id = save_prediction_to_db(result, image_url)
        if record_id:
            result['database_id'] = record_id
        
        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"预测处理失败: {e}")
        return jsonify({
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/gallery')
def gallery():
    """获取历史预测记录"""
    if not DATABASE_INITIALIZED:
        return jsonify({
            "error": "Database not available",
            "message": "Historical data not accessible"
        }), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, latitude, longitude, current_temperature, predicted_temperature,
                   weather_description, predicted_weather_condition, image_url, 
                   location_name, formatted_address, created_at
            FROM predictions 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s;
        """, (limit, offset))
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        gallery_data = []
        for record in records:
            gallery_data.append({
                "id": record[0],
                "latitude": record[1],
                "longitude": record[2],
                "current_temperature": record[3],
                "predicted_temperature": record[4],
                "weather_description": record[5],
                "predicted_weather_condition": record[6],
                "image_url": record[7],
                "location_name": record[8],
                "formatted_address": record[9],
                "created_at": record[10].isoformat() if record[10] else None
            })
        
        return jsonify({
            "success": True,
            "total_records": len(gallery_data),
            "gallery": gallery_data,
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        })
        
    except Exception as e:
        logger.error(f"Gallery查询失败: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/v1/ml/predict', methods=['POST'])
def ml_predict_only():
    """
    专门用于机器学习预测的轻量级API
    输入：环境数据
    输出：预测结果
    """
    try:
        data = request.get_json()
        
        # 输入验证
        required_fields = ['environmental_data', 'hours_ahead']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "success": False
                }), 400
        
        env_data_dict = data['environmental_data']
        hours_ahead = data.get('hours_ahead', 24)
        
        # 验证环境数据格式
        required_env_fields = ['latitude', 'longitude', 'temperature', 'humidity', 'pressure', 'wind_speed', 'weather_description']
        for field in required_env_fields:
            if field not in env_data_dict:
                return jsonify({
                    "error": f"Missing environmental data field: {field}",
                    "success": False
                }), 400
        
        # 创建EnvironmentalData对象
        from WorkFlow.NonRasberryPi_Workflow.1_1_local_environment_setup_and_mock_process_validation import EnvironmentalData, MockMLPredictor
        
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
        
        # 返回预测结果
        return jsonify({
            "success": True,
            "prediction": {
                "predicted_temperature": prediction.predicted_temperature,
                "predicted_humidity": prediction.predicted_humidity,
                "predicted_weather_condition": prediction.predicted_weather_condition,
                "confidence_score": prediction.confidence_score,
                "prediction_timestamp": prediction.prediction_timestamp,
                "model_version": prediction.model_version
            },
            "input_summary": {
                "location": f"({env_data.latitude}, {env_data.longitude})",
                "current_conditions": f"{env_data.temperature}°C, {env_data.weather_description}",
                "hours_ahead": hours_ahead
            },
            "api_version": "1.0",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"ML预测API失败: {e}")
        return jsonify({
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False) 