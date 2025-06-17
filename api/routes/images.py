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
from werkzeug.datastructures import FileStorage
import io

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
        
        # 检查原始数据
        logger.info(f"Request data length: {len(request.data)}")
        logger.info(f"Request stream available: {hasattr(request, 'stream')}")
        
        # 尝试手动解析文件 - 如果Flask解析失败
        file = None
        description = request.form.get('description', '')
        prediction_id = request.form.get('prediction_id')
        
        # 方法1: 标准Flask方式
        if 'file' in request.files:
            file = request.files['file']
            logger.info(f"Found file via Flask: {file.filename}")
        
        # 方法2: 检查是否有None键（说明解析出错）
        elif None in request.form:
            # 文件内容被当作表单数据了，尝试重建FileStorage对象
            file_content = request.form[None]
            if file_content and file_content.startswith(b'\xff\xd8\xff') or file_content.startswith('JFIF'):
                # 这是JPEG文件内容
                file_bytes = file_content.encode('latin-1') if isinstance(file_content, str) else file_content
                file = FileStorage(
                    stream=io.BytesIO(file_bytes),
                    filename="uploaded_image.jpg",
                    content_type="image/jpeg"
                )
                logger.info("Reconstructed file from form data")
        
        # 方法3: 尝试从原始数据中提取
        if not file and request.data:
            try:
                # 这里可以添加更复杂的multipart解析逻辑
                logger.info("Trying to parse from raw request data")
                # 暂时跳过，使用前两种方法
            except Exception as e:
                logger.error(f"Raw data parsing failed: {e}")
        
        logger.info(f"Final extracted - file: {file}, description: {description}, prediction_id: {prediction_id}")
        
        # 验证必要参数
        if not file:
            return jsonify({
                "success": False,
                "error": "Missing file parameter - check if file field type is set to 'File' in Postman",
                "debug": {
                    "files_keys": list(request.files.keys()),
                    "form_keys": list(request.form.keys()),
                    "content_type": request.content_type
                },
                "timestamp": datetime.now().isoformat()
            }), 400
            
        if not prediction_id:
            return jsonify({
                "success": False,
                "error": "Missing prediction_id parameter",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 验证文件是否有效
        if hasattr(file, 'filename') and not file.filename:
            return jsonify({
                "success": False,
                "error": "No file selected",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 上传图片到Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder="obscura_images",
                use_filename=True,
                unique_filename=True
            )
            
            image_url = upload_result['secure_url']
            thumbnail_url = upload_result.get('secure_url', image_url)
            
            logger.info(f"Image uploaded to Cloudinary: {image_url}")
            
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Image upload failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 保存图片信息到数据库
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
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
        
        # 返回成功响应
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
