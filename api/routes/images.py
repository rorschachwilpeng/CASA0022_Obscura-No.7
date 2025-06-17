#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Images API Routes - 图片上传与管理API端点
"""

from flask import Blueprint, request, jsonify
import cloudinary.uploader
import psycopg2
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建蓝图
images_bp = Blueprint('images', __name__, url_prefix='/api/v1/images')

@images_bp.route('', methods=['POST'])
def upload_image():
    """
    图片上传API端点
    
    接收: multipart/form-data 包含 file, description, prediction_id
    返回: 图片信息JSON
    """
    try:
        # 添加调试代码 - 开始
        logger.info("=== DEBUG: Upload request received ===")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        
        # 检查所有files
        for key in request.files:
            file_obj = request.files[key]
            logger.info(f"File key '{key}': filename={file_obj.filename}, content_type={file_obj.content_type}")
        
        # 检查所有form数据
        for key in request.form:
            logger.info(f"Form key '{key}': value={request.form[key]}")
        # 调试代码 - 结束
        
        # 1. 获取表单数据
        file = request.files.get('file')
        description = request.form.get('description', '')
        prediction_id = request.form.get('prediction_id')
        
        logger.info(f"Extracted - file: {file}, description: {description}, prediction_id: {prediction_id}")
        
        # 2. 验证必要参数
        if not file:
            return jsonify({
                "success": False,
                "error": "Missing file parameter",
                "timestamp": datetime.now().isoformat()
            }), 400
            
        if not prediction_id:
            return jsonify({
                "success": False,
                "error": "Missing prediction_id parameter",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 3. 上传图片到Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder="obscura_images",  # 在Cloudinary中创建文件夹
                use_filename=True,
                unique_filename=True
            )
            
            image_url = upload_result['secure_url']
            thumbnail_url = upload_result.get('secure_url', image_url)  # 如需缩略图可后续处理
            
            logger.info(f"Image uploaded to Cloudinary: {image_url}")
            
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Image upload failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 4. 保存图片信息到数据库
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
            # 插入图片记录
            cur.execute("""
                INSERT INTO images (url, thumbnail_url, description, prediction_id, created_at) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id, created_at
            """, (image_url, thumbnail_url, description, int(prediction_id), datetime.now()))
            
            result = cur.fetchone()
            image_id, created_at = result
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Image record saved to database with ID: {image_id}")
            
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Database save failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 5. 返回成功响应
        return jsonify({
            "success": True,
            "image": {
                "id": image_id,
                "url": image_url,
                "thumbnail_url": thumbnail_url,
                "description": description,
                "prediction_id": int(prediction_id),
                "created_at": created_at.isoformat()
            },
            "message": "Image uploaded successfully",
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in upload_image: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('', methods=['GET'])
def get_images():
    """
    获取图片列表API端点
    
    返回: 所有图片信息的JSON列表
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 查询所有图片，按创建时间倒序
        cur.execute("""
            SELECT id, url, thumbnail_url, description, prediction_id, created_at 
            FROM images 
            ORDER BY created_at DESC
        """)
        
        images = []
        for row in cur.fetchall():
            images.append({
                "id": row[0],
                "url": row[1],
                "thumbnail_url": row[2],
                "description": row[3],
                "prediction_id": row[4],
                "created_at": row[5].isoformat()
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "images": images,
            "count": len(images),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching images: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch images",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/<int:image_id>', methods=['GET'])
def get_image_detail(image_id):
    """
    获取单张图片详情API端点
    
    返回: 图片信息及关联的预测数据
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 联查图片和预测数据
        cur.execute("""
            SELECT 
                i.id, i.url, i.thumbnail_url, i.description, i.created_at,
                p.id as prediction_id, p.input_data, p.result_data, p.prompt, p.location
            FROM images i
            LEFT JOIN predictions p ON i.prediction_id = p.id
            WHERE i.id = %s
        """, (image_id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({
                "success": False,
                "error": "Image not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        image_detail = {
            "id": row[0],
            "url": row[1],
            "thumbnail_url": row[2],
            "description": row[3],
            "created_at": row[4].isoformat(),
            "prediction": {
                "id": row[5],
                "input_data": row[6],
                "result_data": row[7],
                "prompt": row[8],
                "location": row[9]
            } if row[5] else None
        }
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "image": image_detail,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching image detail: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch image detail",
            "timestamp": datetime.now().isoformat()
        }), 500
