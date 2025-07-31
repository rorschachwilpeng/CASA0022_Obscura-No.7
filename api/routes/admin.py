#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Routes - 管理员功能API端点
"""

from flask import Blueprint, request, jsonify, render_template_string
import psycopg2
import cloudinary
import cloudinary.api
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 简单的Web界面模板
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OBSCURA No.7 - 管理员面板</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #CD853F; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .action-card { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 8px; border: 2px solid #CD853F; }
        .btn { background: #CD853F; color: #1a1a2e; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 5px; }
        .btn:hover { background: #B8860B; }
        .danger { background: #dc3545; color: white; }
        .danger:hover { background: #c82333; }
        .result { margin: 20px 0; padding: 15px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔭 OBSCURA No.7 管理员面板</h1>
            <p>Gallery图片清理工具</p>
        </div>
        
        <div class="action-card">
            <h3>🗑️ 清理所有Gallery图片</h3>
            <p>⚠️ 此操作将永久删除所有图片数据，请谨慎操作</p>
            <button class="btn danger" onclick="clearGallery()">删除所有图片</button>
            <button class="btn" onclick="checkGalleryStatus()">检查图片状态</button>
        </div>
        
        <div id="result"></div>
        
        <div class="action-card">
            <h3>📊 系统状态</h3>
            <div id="status">正在加载...</div>
        </div>
    </div>

    <script>
        // 检查Gallery状态
        async function checkGalleryStatus() {
            showResult('正在检查图片状态...', 'info');
            try {
                const response = await fetch('/admin/gallery/status');
                const data = await response.json();
                
                let statusHtml = '<h4>当前状态：</h4>';
                statusHtml += `<p>数据库图片数量: ${data.database_images || 0}</p>`;
                statusHtml += `<p>本地存储图片数量: ${data.local_images || 0}</p>`;
                statusHtml += `<p>分析记录数量: ${data.analysis_records || 0}</p>`;
                statusHtml += `<p>预测记录数量: ${data.prediction_records || 0}</p>`;
                
                document.getElementById('status').innerHTML = statusHtml;
                showResult('状态检查完成', 'success');
            } catch (error) {
                showResult('状态检查失败: ' + error.message, 'error');
            }
        }
        
        // 清理Gallery
        async function clearGallery() {
            if (!confirm('确定要删除所有图片吗？此操作无法撤销！')) {
                return;
            }
            
            showResult('正在清理图片...', 'info');
            try {
                const response = await fetch('/admin/gallery/clear', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showResult('清理完成！' + (data.message || ''), 'success');
                    // 重新检查状态
                    setTimeout(checkGalleryStatus, 1000);
                } else {
                    showResult('清理失败: ' + data.error, 'error');
                }
            } catch (error) {
                showResult('清理失败: ' + error.message, 'error');
            }
        }
        
        // 显示结果
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = `<div class="result ${type}">${message}</div>`;
        }
        
        // 页面加载时检查状态
        window.onload = checkGalleryStatus;
    </script>
</body>
</html>
"""

@admin_bp.route('')
def admin_panel():
    """管理员面板主页"""
    return render_template_string(ADMIN_TEMPLATE)

@admin_bp.route('/gallery/status')
def gallery_status():
    """检查Gallery状态"""
    try:
        status = {
            'database_images': 0,
            'local_images': 0,
            'analysis_records': 0,
            'prediction_records': 0,
            'cloudinary_images': 0
        }
        
        # 检查数据库
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cur = conn.cursor()
                
                # 检查images表
                cur.execute("SELECT COUNT(*) FROM images")
                status['database_images'] = cur.fetchone()[0]
                
                # 检查image_analysis表
                cur.execute("SELECT COUNT(*) FROM image_analysis")
                status['analysis_records'] = cur.fetchone()[0]
                
                # 检查predictions表
                cur.execute("SELECT COUNT(*) FROM predictions")
                status['prediction_records'] = cur.fetchone()[0]
                
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"数据库检查失败: {e}")
        
        # 检查本地存储
        try:
            from routes.images import LOCAL_IMAGES_STORE, LOCAL_ANALYSIS_STORE
            status['local_images'] = len(LOCAL_IMAGES_STORE)
            status['local_analysis'] = len(LOCAL_ANALYSIS_STORE)
        except Exception as e:
            logger.error(f"本地存储检查失败: {e}")
        
        # 检查Cloudinary
        try:
            cloudinary_url = os.getenv("CLOUDINARY_URL")
            if cloudinary_url:
                cloudinary.config()
                result = cloudinary.api.resources(
                    type="upload",
                    prefix="obscura_images/",
                    max_results=500
                )
                status['cloudinary_images'] = len(result.get('resources', []))
        except Exception as e:
            logger.error(f"Cloudinary检查失败: {e}")
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/gallery/clear', methods=['POST'])
def clear_gallery():
    """清理Gallery的所有图片"""
    try:
        results = {
            'database_cleared': False,
            'local_cleared': False,
            'cloudinary_cleared': False,
            'details': []
        }
        
        # 清理数据库
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cur = conn.cursor()
                
                # 获取删除前的数量
                cur.execute("SELECT COUNT(*) FROM images")
                images_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM image_analysis")
                analysis_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM predictions")
                predictions_count = cur.fetchone()[0]
                
                # 删除数据
                cur.execute("DELETE FROM image_analysis")
                cur.execute("DELETE FROM images")
                cur.execute("DELETE FROM predictions")
                
                # 重置序列
                cur.execute("ALTER SEQUENCE images_id_seq RESTART WITH 1")
                cur.execute("ALTER SEQUENCE image_analysis_id_seq RESTART WITH 1")
                cur.execute("ALTER SEQUENCE predictions_id_seq RESTART WITH 1")
                
                conn.commit()
                cur.close()
                conn.close()
                
                results['database_cleared'] = True
                results['details'].append(f"数据库清理完成: {images_count}张图片, {analysis_count}条分析, {predictions_count}条预测")
                
        except Exception as e:
            results['details'].append(f"数据库清理失败: {str(e)}")
        
        # 清理本地存储
        try:
            from routes.images import LOCAL_IMAGES_STORE, LOCAL_ANALYSIS_STORE
            
            local_images = len(LOCAL_IMAGES_STORE)
            local_analysis = len(LOCAL_ANALYSIS_STORE)
            
            LOCAL_IMAGES_STORE.clear()
            LOCAL_ANALYSIS_STORE.clear()
            
            results['local_cleared'] = True
            results['details'].append(f"本地存储清理完成: {local_images}张图片, {local_analysis}条分析")
            
        except Exception as e:
            results['details'].append(f"本地存储清理失败: {str(e)}")
        
        # 清理Cloudinary
        try:
            cloudinary_url = os.getenv("CLOUDINARY_URL")
            if cloudinary_url:
                cloudinary.config()
                
                # 获取所有图片
                result = cloudinary.api.resources(
                    type="upload",
                    prefix="obscura_images/",
                    max_results=500
                )
                
                resources = result.get('resources', [])
                
                if resources:
                    public_ids = [resource['public_id'] for resource in resources]
                    delete_result = cloudinary.api.delete_resources(public_ids)
                    deleted_count = len(delete_result.get('deleted', {}))
                    
                    results['cloudinary_cleared'] = True
                    results['details'].append(f"Cloudinary清理完成: {deleted_count}张图片")
                else:
                    results['details'].append("Cloudinary中没有找到需要删除的图片")
                    
        except Exception as e:
            results['details'].append(f"Cloudinary清理失败: {str(e)}")
        
        success = any([results['database_cleared'], results['local_cleared'], results['cloudinary_cleared']])
        
        return jsonify({
            'success': success,
            'message': '; '.join(results['details']),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"清理操作失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 

@admin_bp.route('/check-dependencies', methods=['GET'])
def check_dependencies():
    """检查依赖包是否正常安装"""
    try:
        deps_status = {}
        
        # 检查核心依赖
        core_deps = [
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('scikit-learn', 'sklearn'),
            ('joblib', 'joblib'),
            ('tensorflow', 'tensorflow'),
            ('requests', 'requests'),
            ('Flask', 'flask'),
        ]
        
        for package, import_name in core_deps:
            try:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'unknown')
                deps_status[package] = {'available': True, 'version': version}
            except ImportError as e:
                deps_status[package] = {'available': False, 'version': None, 'error': str(e)}
        
        return jsonify({
            'success': True,
            'message': '依赖检查完成',
            'dependencies': deps_status,
            'timestamp': '2025-07-31'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'依赖检查失败: {str(e)}',
            'error': str(e)
        }), 500

@admin_bp.route('/test-ml-model', methods=['GET'])
def test_ml_model():
    """测试ML模型是否正常工作"""
    try:
        # 直接测试ML模型，不使用subprocess
        from ML_Models.models.shap_deployment.hybrid_model_wrapper import get_hybrid_shap_model
        
        # 测试模型加载
        model = get_hybrid_shap_model()
        status = model.get_model_status()
        
        # 测试简单预测
        test_result = model.predict_environmental_scores(
            latitude=51.5074,
            longitude=-0.1278,
            month=7
        )
        
        return jsonify({
            'success': True,
            'message': 'ML模型测试完成',
            'model_status': status,
            'test_prediction': test_result,
            'timestamp': '2025-07-31'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'ML模型测试失败: {str(e)}',
            'error': str(e)
        }), 500 