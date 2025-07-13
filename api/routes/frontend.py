#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Routes for Obscura No.7
处理前端页面路由和模板渲染
"""

import os
import sys
import logging
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
import psycopg2

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

# 创建前端蓝图
frontend_bp = Blueprint('frontend', __name__)

def get_system_status():
    """获取系统状态信息"""
    try:
        # 检查环境变量
        openweather_status = bool(os.getenv("OPENWEATHER_API_KEY"))
        openai_status = bool(os.getenv("OPENAI_API_KEY"))
        google_maps_status = bool(os.getenv("GOOGLE_MAPS_API_KEY"))
        cloudinary_url = os.getenv("CLOUDINARY_URL")
        database_url = os.getenv("DATABASE_URL")
        
        # 检查Cloudinary配置
        cloudinary_status = False
        if cloudinary_url:
            try:
                import cloudinary
                cloudinary.config()
                cloudinary_status = True
            except Exception as e:
                logger.error(f"Cloudinary配置检查失败: {e}")
        
        # 检查数据库连接
        database_status = False
        if database_url:
            try:
                import psycopg2
                conn = psycopg2.connect(database_url)
                conn.close()
                database_status = True
            except Exception as e:
                logger.error(f"数据库连接检查失败: {e}")
        
        # 检查工作流可用性
        workflow_status = False
        try:
            import importlib.util
            module_path = os.path.join(project_root, 'WorkFlow', 'NonRasberryPi_Workflow', '1_1_local_environment_setup_and_mock_process_validation.py')
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location("workflow_module", module_path)
                workflow_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(workflow_module)
                workflow_status = True
        except Exception as e:
            logger.error(f"工作流检查失败: {e}")
        
        return {
            'openweather_status': openweather_status,
            'openai_status': openai_status,
            'google_maps_status': google_maps_status,
            'cloudinary_status': cloudinary_status,
            'database_status': database_status,
            'workflow_status': workflow_status,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    
    except Exception as e:
        logger.error(f"系统状态检查失败: {e}")
        return {
            'openweather_status': False,
            'openai_status': False,
            'google_maps_status': False,
            'cloudinary_status': False,
            'database_status': False,
            'workflow_status': False,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

@frontend_bp.route('/')
def home():
    """主页 - Gallery图片展示页面"""
    try:
        logger.info("渲染Gallery主页")
        return render_template('gallery.html')
    
    except Exception as e:
        logger.error(f"Gallery主页渲染失败: {e}")
        return render_template('gallery.html'), 500

@frontend_bp.route('/gallery')
def gallery():
    """Gallery别名路由 - 重定向到主页"""
    try:
        logger.info("Gallery别名路由 - 重定向到主页")
        return render_template('gallery.html')
    
    except Exception as e:
        logger.error(f"Gallery页面渲染失败: {e}")
        return render_template('gallery.html'), 500

@frontend_bp.route('/image/<int:image_id>')
def image_detail(image_id):
    """图片详情页面"""
    try:
        logger.info(f"渲染图片详情页面，图片ID: {image_id}")
        
        # 验证图片ID的有效性
        if image_id <= 0:
            logger.warning(f"无效的图片ID: {image_id}")
            return render_template('404.html'), 404
        
        # 检查数据库连接
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("数据库未配置")
            return render_template('image_detail.html', error="Database not configured"), 503
        
        # 验证图片是否存在（基础检查）
        try:
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            cur.execute("SELECT id FROM images WHERE id = %s", (image_id,))
            image_exists = cur.fetchone()
            conn.close()
            
            if not image_exists:
                logger.warning(f"图片不存在，ID: {image_id}")
                return render_template('404.html'), 404
        
        except Exception as db_error:
            logger.error(f"数据库查询失败: {db_error}")
            # 即使数据库查询失败，也渲染页面，让JavaScript处理
            pass
        
        # 渲染详情页面，数据将通过AJAX加载
        return render_template('image_detail.html', image_id=image_id)
    
    except Exception as e:
        logger.error(f"图片详情页面渲染失败: {e}")
        return render_template('image_detail.html', error=str(e)), 500

# System Status API endpoint removed - no longer needed

@frontend_bp.route('/api/gallery/stats')
def gallery_stats():
    """获取图库统计信息"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return jsonify({
                "success": False,
                "error": "Database not configured"
            }), 503
        
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 获取图片总数
        cur.execute("SELECT COUNT(*) FROM images")
        total_images = cur.fetchone()[0]
        
        # 获取预测总数
        cur.execute("SELECT COUNT(DISTINCT prediction_id) FROM images")
        unique_predictions = cur.fetchone()[0]
        
        # 获取最近的图片
        cur.execute("""
            SELECT COUNT(*) FROM images 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        recent_images = cur.fetchone()[0]
        
        # 获取最新图片的创建时间
        cur.execute("""
            SELECT created_at FROM images 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        latest_result = cur.fetchone()
        latest_image = latest_result[0].isoformat() if latest_result else None
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_images": total_images,
                "unique_predictions": unique_predictions,
                "recent_images": recent_images,
                "latest_image": latest_image,
                "locations_explored": min(total_images, 50)  # 模拟位置数据
            },
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"图库统计获取失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@frontend_bp.route('/about')
def about():
    """关于页面"""
    try:
        project_info = {
            "name": "Obscura No.7",
            "subtitle": "Interactive Virtual Telescope Art Installation",
            "description": "A steampunk-inspired art installation that combines environmental data, machine learning predictions, and AI-generated imagery to create visions of possible futures.",
            "version": "1.4.0",
            "technologies": [
                "Flask (Python Web Framework)",
                "OpenAI DALL-E (Image Generation)",
                "OpenWeather API (Environmental Data)",
                "PostgreSQL (Data Storage)",
                "Cloudinary (Image Storage)",
                "Machine Learning (Environmental Prediction)",
                "Steampunk UI/UX Design"
            ],
            "features": [
                "Real-time environmental data collection",
                "ML-powered weather prediction",
                "AI-generated future environment visualizations",
                "Steampunk-themed user interface",
                "Responsive web gallery",
                "RESTful API architecture"
            ]
        }
        
        return render_template('about.html', project=project_info)
    
    except Exception as e:
        logger.error(f"关于页面渲染失败: {e}")
        return render_template('about.html', project={}), 500

@frontend_bp.route('/prediction')
def prediction():
    """环境预测页面"""
    try:
        logger.info("渲染环境预测页面")
        return render_template('prediction.html')
    
    except Exception as e:
        logger.error(f"环境预测页面渲染失败: {e}")
        return render_template('prediction.html'), 500

@frontend_bp.route('/shap')
def shap_prediction():
    """SHAP环境预测分析页面"""
    try:
        logger.info("渲染SHAP环境预测页面")
        return render_template('shap_prediction.html')
    
    except Exception as e:
        logger.error(f"SHAP预测页面渲染失败: {e}")
        return render_template('shap_prediction.html'), 500

@frontend_bp.route('/test')
def local_test():
    """本地测试页面"""
    try:
        logger.info("渲染本地测试页面")
        return render_template('local_test.html')
    except Exception as e:
        logger.error(f"本地测试页面渲染失败: {e}")
        return render_template('local_test.html'), 500

@frontend_bp.route('/ui-test')
def ui_test():
    """UI变化测试页面"""
    return render_template('test_ui_changes.html')

@frontend_bp.route('/health')
def health_check():
    """健康检查端点"""
    try:
        status_data = get_system_status()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.4.0",
            "services": {
                "web_server": True,
                "database": status_data['database_status'],
                "ml_engine": status_data['workflow_status'],
                "image_storage": status_data['cloudinary_status'],
                "weather_api": status_data['openweather_status'],
                "ai_generator": status_data['openai_status']
            },
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "debug_mode": os.getenv('FLASK_ENV') == 'development'
            }
        }
        
        # 检查关键服务
        critical_down = not (status_data['database_status'] and status_data['workflow_status'])
        if critical_down:
            health_status["status"] = "degraded"
            return jsonify(health_status), 503
        
        return jsonify(health_status), 200
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@frontend_bp.route('/manifest.json')
def manifest():
    """PWA manifest文件"""
    return jsonify({
        "name": "Obscura No.7 - Virtual Telescope",
        "short_name": "Obscura No.7",
        "description": "Interactive Virtual Telescope Art Installation",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a1a1a",
        "theme_color": "#CD853F",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'><text y='160' font-size='160'>🔭</text></svg>",
                "sizes": "192x192",
                "type": "image/svg+xml"
            },
            {
                "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><text y='440' font-size='440'>🔭</text></svg>",
                "sizes": "512x512",
                "type": "image/svg+xml"
            }
        ],
        "categories": ["art", "education", "entertainment"],
        "screenshots": []
    })

@frontend_bp.route('/robots.txt')
def robots():
    """robots.txt文件"""
    from flask import Response
    
    robots_content = """User-agent: *
Disallow: /api/
Disallow: /health
Allow: /
Allow: /gallery
Allow: /about

Sitemap: {}/sitemap.xml
""".format(request.url_root.rstrip('/'))
    
    return Response(robots_content, mimetype='text/plain')

@frontend_bp.route('/sitemap.xml')
def sitemap():
    """网站地图"""
    from flask import Response
    
    base_url = request.url_root.rstrip('/')
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/gallery</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/about</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
</urlset>"""
    
    return Response(sitemap_content, mimetype='application/xml')

@frontend_bp.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    logger.warning(f"404错误: {request.url}")
    return render_template('errors/404.html'), 404

@frontend_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"500错误: {error}")
    return render_template('errors/500.html'), 500

@frontend_bp.errorhandler(503)
def service_unavailable_error(error):
    """503错误处理"""
    logger.error(f"503错误: 服务不可用")
    return render_template('errors/503.html'), 503

# 上下文处理器：为所有模板提供全局变量
@frontend_bp.app_context_processor
def inject_global_vars():
    """为模板注入全局变量"""
    return {
        'app_name': 'Obscura No.7',
        'app_version': '1.4.0',
        'current_year': datetime.now().year,
        'build_time': datetime.now().isoformat(),
        'debug_mode': os.getenv('FLASK_ENV') == 'development'
    }

# 模板过滤器
@frontend_bp.app_template_filter('datetime_format')
def datetime_format(value, format='%Y-%m-%d %H:%M:%S'):
    """格式化日期时间"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    return value.strftime(format)

@frontend_bp.app_template_filter('relative_time')
def relative_time(value):
    """相对时间显示"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    now = datetime.now()
    diff = now - value
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

@frontend_bp.app_template_filter('file_size')
def file_size_format(bytes_value):
    """格式化文件大小"""
    try:
        bytes_value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"
    except:
        return "Unknown"

# 请求钩子
@frontend_bp.before_request
def before_request():
    """请求前处理"""
    # 记录请求信息
    logger.info(f"前端请求: {request.method} {request.path} - {request.remote_addr}")

@frontend_bp.after_request
def after_request(response):
    """请求后处理"""
    # 添加安全头
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 添加缓存控制
    if request.endpoint in ['frontend.manifest', 'frontend.robots', 'frontend.sitemap']:
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1天
    elif request.endpoint == 'frontend.api_status':
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    
    return response

# 日志配置
def setup_frontend_logging():
    """设置前端路由日志"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler('logs/frontend.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

# 初始化日志
setup_frontend_logging()

logger.info("前端路由模块已加载")
