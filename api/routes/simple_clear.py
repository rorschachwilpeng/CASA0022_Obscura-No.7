#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Clear Routes - 简单的清理触发器
"""

from flask import Blueprint, request, jsonify, render_template
import cloudinary
import cloudinary.uploader
import cloudinary.api
import psycopg2
import os
import shutil
from datetime import datetime
import psycopg2.extras

simple_clear_bp = Blueprint('simple_clear', __name__)

@simple_clear_bp.route('/gallery-cleaner')
def gallery_cleaner_page():
    """
    Gallery清理工具的美丽页面
    """
    return render_template('gallery_cleaner.html')

@simple_clear_bp.route('/clear-gallery-now', methods=['GET'])
def clear_gallery_now():
    """
    清理Gallery的简单触发器
    """
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
            
            # 按正确的顺序删除表（修复外键约束问题）
            # 1. 先删除 image_analysis (引用 images)
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
            
            # 2. 再删除 images (引用 predictions)
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
            
            # 3. 最后删除 predictions (被 images 引用)
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
            
            # 获取所有在obscura_images文件夹中的图片
            resources = cloudinary.api.resources(
                type="upload",
                prefix="obscura_images/",
                max_results=500
            )
            
            deleted_count = 0
            for resource in resources['resources']:
                try:
                    cloudinary.uploader.destroy(resource['public_id'])
                    deleted_count += 1
                except Exception as e:
                    pass  # 忽略单个删除失败
            
            results.append(f"✅ Cloudinary清理完成: {deleted_count}张图片")
            success_count += 1
        else:
            results.append("ℹ️ Cloudinary中没有找到需要删除的图片")
    except Exception as e:
        results.append(f"❌ Cloudinary清理失败: {str(e)}")
    
    # 3. 清理本地存储
    try:
        static_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'images')
        deleted_files = 0
        deleted_analyses = 0
        
        if os.path.exists(static_images_path):
            for filename in os.listdir(static_images_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    try:
                        os.remove(os.path.join(static_images_path, filename))
                        deleted_files += 1
                    except Exception as e:
                        pass  # 忽略删除失败
        
        results.append(f"✅ 本地存储清理成功: {deleted_files}张图片，{deleted_analyses}条分析")
        success_count += 1
        
    except Exception as e:
        results.append(f"❌ 本地存储清理失败: {str(e)}")
    
    # 返回结果
    return jsonify({
        'success': success_count > 0,
        'results': results,
        'success_count': success_count,
        'total_operations': 3,
        'timestamp': datetime.now().isoformat()
    })

@simple_clear_bp.route('/gallery-status', methods=['GET'])
def gallery_status():
    """
    获取Gallery状态信息
    """
    try:
        status = {}
        
        # 检查数据库状态
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cur = conn.cursor()
                
                # 检查各表的记录数
                tables_info = {}
                
                # 检查images表
                try:
                    cur.execute("SELECT COUNT(*) FROM images")
                    tables_info['images'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    tables_info['images'] = "表不存在"
                
                # 检查image_analysis表
                try:
                    cur.execute("SELECT COUNT(*) FROM image_analysis")
                    tables_info['image_analysis'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    tables_info['image_analysis'] = "表不存在"
                
                # 检查predictions表
                try:
                    cur.execute("SELECT COUNT(*) FROM predictions")
                    tables_info['predictions'] = cur.fetchone()[0]
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    tables_info['predictions'] = "表不存在"
                
                cur.close()
                conn.close()
                
                status['database'] = {
                    'available': True,
                    'tables': tables_info
                }
            else:
                status['database'] = {
                    'available': False,
                    'error': 'DATABASE_URL not configured'
                }
        except Exception as e:
            status['database'] = {
                'available': False,
                'error': str(e)
            }
        
        # 检查Cloudinary状态
        try:
            cloudinary_url = os.getenv("CLOUDINARY_URL")
            if cloudinary_url:
                cloudinary.config()
                resources = cloudinary.api.resources(
                    type="upload",
                    prefix="obscura_images/",
                    max_results=1
                )
                
                status['cloudinary'] = {
                    'available': True,
                    'images_count': len(resources.get('resources', []))
                }
            else:
                status['cloudinary'] = {
                    'available': False,
                    'error': 'CLOUDINARY_URL not configured'
                }
        except Exception as e:
            status['cloudinary'] = {
                'available': False,
                'error': str(e)
            }
        
        # 检查本地存储状态
        try:
            static_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'images')
            local_images_count = 0
            
            if os.path.exists(static_images_path):
                for filename in os.listdir(static_images_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        local_images_count += 1
            
            status['local_storage'] = {
                'available': True,
                'images_count': local_images_count,
                'path': static_images_path
            }
        except Exception as e:
            status['local_storage'] = {
                'available': False,
                'error': str(e)
            }
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500 