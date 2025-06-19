#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updated Flask Application with Steampunk Frontend Integration
集成蒸汽朋克前端的完整Flask应用
"""

import os
import sys
import logging
from flask import Flask
from datetime import datetime
import importlib.util

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
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
from api.routes.frontend import frontend_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置应用
    configure_app(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置服务
    configure_services(app)
    
    # 设置错误处理
    setup_error_handlers(app)
    
    # 执行启动检查（替代before_first_request）
    startup_check(app)
    
    logger.info("🔭 Obscura No.7 应用初始化完成")
    return app

def configure_app(app):
    """配置Flask应用"""
    # 基础配置
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1年缓存静态文件
    
    # 安全配置（仅在HTTPS环境下启用）
    if os.environ.get('RENDER'):  # Render环境下启用安全cookie
        app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 模板配置
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    
    logger.info("✅ Flask应用配置完成")

def register_blueprints(app):
    """注册所有蓝图"""
    # API蓝图
    app.register_blueprint(ml_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(images_bp)
    
    # 前端蓝图（注册到根路径）
    app.register_blueprint(frontend_bp)
    
    logger.info("✅ 所有蓝图注册完成")

def configure_services(app):
    """配置外部服务"""
    with app.app_context():
        # 配置Cloudinary
        cloudinary_url = os.getenv("CLOUDINARY_URL")
        if cloudinary_url and CLOUDINARY_AVAILABLE:
            try:
                cloudinary.config()
                app.config['CLOUDINARY_CONFIGURED'] = True
                logger.info("✅ Cloudinary配置成功")
            except Exception as e:
                logger.error(f"❌ Cloudinary配置失败: {e}")
                app.config['CLOUDINARY_CONFIGURED'] = False
        else:
            app.config['CLOUDINARY_CONFIGURED'] = False
        
        # 检查数据库
        database_url = os.getenv("DATABASE_URL")
        if database_url and POSTGRESQL_AVAILABLE:
            try:
                conn = psycopg2.connect(database_url)
                conn.close()
                app.config['DATABASE_INITIALIZED'] = True
                logger.info("✅ 数据库连接成功")
            except Exception as e:
                logger.error(f"❌ 数据库连接失败: {e}")
                app.config['DATABASE_INITIALIZED'] = False
        else:
            app.config['DATABASE_INITIALIZED'] = False
        
        # 检查工作流
        try:
            module_path = os.path.join(project_root, 'WorkFlow', 'NonRasberryPi_Workflow', '1_1_local_environment_setup_and_mock_process_validation.py')
            spec = importlib.util.spec_from_file_location("workflow_module", module_path)
            workflow_module = importlib.util.module_from_spec(spec)
            sys.modules["workflow_module"] = workflow_module
            spec.loader.exec_module(workflow_module)
            
            app.config['WORKFLOW_AVAILABLE'] = True
            logger.info("✅ 工作流引擎加载成功")
        except Exception as e:
            logger.warning(f"⚠️ 工作流引擎不可用: {e}")
            app.config['WORKFLOW_AVAILABLE'] = False

def setup_error_handlers(app):
    """设置错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404错误: {error}")
        from flask import render_template, jsonify, request
        
        # 如果是API请求，返回JSON
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "API endpoint not found",
                "path": request.path,
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # 否则返回HTML错误页面
        try:
            return render_template('error.html', 
                                 error_code=404, 
                                 error_message="Page Not Found"), 404
        except:
            # 如果模板不存在，返回简单HTML
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>404 - Not Found</title></head>
            <body>
                <h1>404 - Page Not Found</h1>
                <p>The requested page could not be found.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            ''', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500错误: {error}")
        from flask import render_template, jsonify, request
        
        # 如果是API请求，返回JSON
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 否则返回HTML错误页面
        try:
            return render_template('error.html', 
                                 error_code=500, 
                                 error_message="Internal Server Error"), 500
        except:
            # 如果模板不存在，返回简单HTML
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>500 - Server Error</title></head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our end.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            ''', 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        logger.error(f"503错误: {error}")
        from flask import render_template, jsonify, request
        
        # 如果是API请求，返回JSON
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "Service temporarily unavailable",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # 否则返回HTML错误页面
        try:
            return render_template('error.html', 
                                 error_code=503, 
                                 error_message="Service Unavailable"), 503
        except:
            # 如果模板不存在，返回简单HTML
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>503 - Service Unavailable</title></head>
            <body>
                <h1>503 - Service Unavailable</h1>
                <p>The service is temporarily unavailable.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            ''', 503
    
    logger.info("✅ 错误处理器设置完成")

def startup_check(app):
    """应用启动时的检查（替代before_first_request）"""
    logger.info("🚀 Obscura No.7 Virtual Telescope System Starting...")
    
    # 检查关键环境变量
    required_vars = ['DATABASE_URL', 'CLOUDINARY_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ 缺少环境变量: {missing_vars}")
    
    # 输出系统信息
    logger.info(f"📊 系统信息:")
    logger.info(f"   - Python版本: {sys.version}")
    logger.info(f"   - 平台: {sys.platform}")
    logger.info(f"   - 工作目录: {os.getcwd()}")
    logger.info(f"   - 数据库: {'✅' if app.config.get('DATABASE_INITIALIZED') else '❌'}")
    logger.info(f"   - 图片存储: {'✅' if app.config.get('CLOUDINARY_CONFIGURED') else '❌'}")
    logger.info(f"   - ML工作流: {'✅' if app.config.get('WORKFLOW_AVAILABLE') else '❌'}")
    
    logger.info("🔭 Virtual Telescope System Ready!")

# 创建应用实例
app = create_app()

# 向后兼容的路由（如果需要）
@app.route('/predict', methods=['POST'])
def legacy_predict():
    """遗留的预测端点（向后兼容）"""
    from flask import jsonify
    return jsonify({
        "message": "This endpoint has been moved. Please use the new API endpoints.",
        "new_endpoints": {
            "ml_prediction": "/api/v1/ml/predict",
            "image_upload": "/api/v1/images",
            "system_status": "/api/status"
        },
        "documentation": "/",
        "timestamp": datetime.now().isoformat()
    }), 301

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🌐 启动服务器 - 端口: {port}, 调试模式: {debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
