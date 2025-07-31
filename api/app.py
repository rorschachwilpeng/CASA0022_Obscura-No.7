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

# SocketIO导入
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

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
from api.routes.environmental import environmental_bp
from api.routes.lightweight_ml_predict import lightweight_ml_bp
from api.routes.shap_predict import shap_bp
from api.routes.admin import admin_bp
from api.routes.simple_clear import simple_clear_bp

# 条件导入SHAP预测蓝图
SHAP_BP_AVAILABLE = False
shap_bp = None

try:
    from api.routes.shap_predict import shap_bp
    SHAP_BP_AVAILABLE = True
    print("✅ SHAP预测模块导入成功")
except ImportError as e:
    print(f"⚠️ SHAP预测模块不可用: {e}")
    SHAP_BP_AVAILABLE = False
    shap_bp = None

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
    
    # 初始化SocketIO
    socketio = None
    logger.info(f"🔍 SocketIO availability check: SOCKETIO_AVAILABLE={SOCKETIO_AVAILABLE}")
    
    if SOCKETIO_AVAILABLE:
        try:
            socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
            app.socketio = socketio
            logger.info("✅ SocketIO successfully initialized")
            logger.info(f"🔗 SocketIO instance created: {type(socketio)}")
        except Exception as e:
            logger.error(f"❌ SocketIO initialization failed: {e}")
            socketio = None
    else:
        logger.warning("⚠️ SocketIO not available - flask-socketio not imported")
        try:
            import flask_socketio
            logger.warning(f"🤔 Actually flask-socketio IS available, version: {getattr(flask_socketio, '__version__', 'unknown')}")
        except ImportError as import_error:
            logger.warning(f"📦 flask-socketio import error: {import_error}")
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置服务
    configure_services(app)
    
    # 设置错误处理
    setup_error_handlers(app)
    
    # 执行启动检查（替代before_first_request）
    startup_check(app)
    
    logger.info("🔭 Obscura No.7 应用初始化完成")
    return app, socketio

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
    app.register_blueprint(environmental_bp)
    
    # 轻量级ML API蓝图（云端部署优化）
    app.register_blueprint(lightweight_ml_bp)
    
    # SHAP预测API蓝图（环境变化指数框架）
    if SHAP_BP_AVAILABLE and shap_bp is not None:
        app.register_blueprint(shap_bp)
        logger.info("✅ SHAP蓝图注册成功")
    else:
        logger.warning("⚠️ SHAP蓝图跳过注册")
    
    # 管理员蓝图
    app.register_blueprint(admin_bp)
    logger.info("✅ 管理员蓝图注册成功")
    
    # 简单清理蓝图
    app.register_blueprint(simple_clear_bp)
    logger.info("✅ 简单清理蓝图注册成功")
    
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
            <html>
                <head><title>404 - Page Not Found</title></head>
                <body>
                    <h1>404 - Page Not Found</h1>
                    <p>The requested page was not found.</p>
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
                "path": request.path,
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
            <html>
                <head><title>500 - Internal Server Error</title></head>
                <body>
                    <h1>500 - Internal Server Error</h1>
                    <p>An internal server error occurred.</p>
                    <a href="/">Return to Home</a>
                </body>
            </html>
            ''', 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """捕获所有未处理的异常"""
        logger.error(f"未处理的异常: {e}")
        from flask import jsonify, request
        
        # 如果是API请求，返回JSON
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "Unhandled exception",
                "exception": str(e),
                "path": request.path,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 否则返回简单错误页面
        return '''
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>An error occurred</h1>
                <p>Please try again later.</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        ''', 500

def startup_check(app):
    """启动检查"""
    with app.app_context():
        try:
            logger.info("🔍 执行启动检查...")
            
            # 输出环境信息
            logger.info(f"Python版本: {sys.version}")
            logger.info(f"项目根目录: {project_root}")
            logger.info(f"Flask调试模式: {app.debug}")
            
            # 检查关键目录
            critical_dirs = [
                'api/templates',
                'api/static',
                'api/routes'
            ]
            
            for dir_path in critical_dirs:
                full_path = os.path.join(project_root, dir_path)
                if os.path.exists(full_path):
                    logger.info(f"✅ 目录存在: {dir_path}")
                else:
                    logger.warning(f"⚠️ 目录缺失: {dir_path}")
            
            logger.info("✅ 启动检查完成")
        except Exception as e:
            logger.error(f"❌ 启动检查失败: {e}")

# 创建应用实例
app, socketio = create_app()

# Legacy route for compatibility (在app创建后添加)
@app.route('/predict', methods=['POST'])
def legacy_predict():
    """保持向后兼容的预测端点"""
    from flask import jsonify
    return jsonify({
        "message": "Please use /api/v1/ml/predict or /api/v1/lightweight/predict",
        "redirect": "/api/v1/ml/predict"
    }), 301

if __name__ == '__main__':
    # 开发模式启动
    port = int(os.environ.get('PORT', 52778))  # 使用可用端口52778
    debug = not os.environ.get('RENDER')  # 在Render环境中禁用调试模式
    
    logger.info(f"🚀 启动应用 - 端口: {port}, 调试模式: {debug}")
    
    if socketio and SOCKETIO_AVAILABLE:
        # 在生产环境中允许Werkzeug运行（仅用于WebSocket支持）
        socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug) 