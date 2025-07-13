#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Clear Routes - 简单的清理触发器
"""

from flask import Blueprint, jsonify, request, render_template
import psycopg2
import cloudinary
import cloudinary.api
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建简单清理蓝图
simple_clear_bp = Blueprint('simple_clear', __name__)

@simple_clear_bp.route('/gallery-cleaner')
def gallery_cleaner_page():
    """
    Gallery清理工具页面
    访问 /gallery-cleaner 查看清理工具界面
    """
    return render_template('gallery_cleaner.html')

@simple_clear_bp.route('/clear-gallery-now', methods=['GET'])
def clear_gallery_now():
    """
    简单的Gallery清理触发器
    访问 /clear-gallery-now 即可清理所有图片
    """
    try:
        # 安全检查：添加一个简单的验证参数
        confirm = request.args.get('confirm')
        if confirm != 'yes-delete-all':
            return jsonify({
                'success': False,
                'error': '需要确认参数',
                'message': '访问: /clear-gallery-now?confirm=yes-delete-all 来确认删除',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        results = []
        success_count = 0
        
        # 1. 清理数据库
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cur = conn.cursor()
                
                # 检查表是否存在并获取删除前的数量
                images_count = 0
                analysis_count = 0
                predictions_count = 0
                cleared_tables = []
                
                # 检查并清理images表
                try:
                    cur.execute("SELECT COUNT(*) FROM images")
                    images_count = cur.fetchone()[0]
                    if images_count > 0:
                        cur.execute("DELETE FROM images")
                    try:
                        cur.execute("ALTER SEQUENCE images_id_seq RESTART WITH 1")
                    except:
                        pass  # 序列可能不存在
                    cleared_tables.append(f"images({images_count})")
                except psycopg2.ProgrammingError:
                    conn.rollback()  # 重置连接状态
                    cleared_tables.append("images(表不存在)")
                
                # 检查并清理image_analysis表
                try:
                    cur.execute("SELECT COUNT(*) FROM image_analysis")
                    analysis_count = cur.fetchone()[0]
                    if analysis_count > 0:
                        cur.execute("DELETE FROM image_analysis")
                    try:
                        cur.execute("ALTER SEQUENCE image_analysis_id_seq RESTART WITH 1")
                    except:
                        pass  # 序列可能不存在
                    cleared_tables.append(f"image_analysis({analysis_count})")
                except psycopg2.ProgrammingError:
                    conn.rollback()  # 重置连接状态
                    cleared_tables.append("image_analysis(表不存在)")
                
                # 检查并清理predictions表
                try:
                    cur.execute("SELECT COUNT(*) FROM predictions")
                    predictions_count = cur.fetchone()[0]
                    if predictions_count > 0:
                        cur.execute("DELETE FROM predictions")
                    try:
                        cur.execute("ALTER SEQUENCE predictions_id_seq RESTART WITH 1")
                    except:
                        pass  # 序列可能不存在
                    cleared_tables.append(f"predictions({predictions_count})")
                except psycopg2.ProgrammingError:
                    conn.rollback()  # 重置连接状态
                    cleared_tables.append("predictions(表不存在)")
                
                conn.commit()
                cur.close()
                conn.close()
                
                results.append(f"✅ 数据库清理完成: {', '.join(cleared_tables)}")
                success_count += 1
                
        except Exception as e:
            results.append(f"❌ 数据库清理失败: {str(e)}")
        
        # 2. 清理Cloudinary
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
                    
                    results.append(f"✅ Cloudinary清理成功: {deleted_count}张图片")
                    success_count += 1
                else:
                    results.append("ℹ️ Cloudinary中没有找到需要删除的图片")
                    
        except Exception as e:
            results.append(f"❌ Cloudinary清理失败: {str(e)}")
        
        # 3. 清理本地存储
        try:
            from routes.images import LOCAL_IMAGES_STORE, LOCAL_ANALYSIS_STORE
            
            local_images = len(LOCAL_IMAGES_STORE)
            local_analysis = len(LOCAL_ANALYSIS_STORE)
            
            LOCAL_IMAGES_STORE.clear()
            LOCAL_ANALYSIS_STORE.clear()
            
            results.append(f"✅ 本地存储清理成功: {local_images}张图片, {local_analysis}条分析")
            success_count += 1
            
        except Exception as e:
            results.append(f"❌ 本地存储清理失败: {str(e)}")
        
        return jsonify({
            'success': success_count > 0,
            'message': '清理操作完成',
            'results': results,
            'success_count': success_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"清理操作失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@simple_clear_bp.route('/gallery-status', methods=['GET'])
def gallery_status():
    """
    简单的Gallery状态检查
    访问 /gallery-status 查看当前状态
    """
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
                
                # 安全地检查每个表
                try:
                    cur.execute("SELECT COUNT(*) FROM images")
                    status['database_images'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    status['database_images'] = 0
                
                try:
                    cur.execute("SELECT COUNT(*) FROM image_analysis")
                    status['analysis_records'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    status['analysis_records'] = 0
                
                try:
                    cur.execute("SELECT COUNT(*) FROM predictions")
                    status['prediction_records'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    status['prediction_records'] = 0
                
                cur.close()
                conn.close()
        except Exception as e:
            status['database_error'] = str(e)
        
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
            status['cloudinary_error'] = str(e)
        
        # 检查本地存储
        try:
            from routes.images import LOCAL_IMAGES_STORE, LOCAL_ANALYSIS_STORE
            status['local_images'] = len(LOCAL_IMAGES_STORE)
            status['local_analysis'] = len(LOCAL_ANALYSIS_STORE)
        except Exception as e:
            status['local_error'] = str(e)
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500 