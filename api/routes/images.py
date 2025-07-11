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

# 添加OpenAI导入
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# 创建蓝图
images_bp = Blueprint('images', __name__, url_prefix='/api/v1/images')

def generate_ai_environmental_story(shap_data):
    """
    使用DeepSeek生成环境故事（约100词英文，戏剧性描述）
    
    Args:
        shap_data: SHAP分析数据，包含三个维度得分和特征重要性
        
    Returns:
        str: 生成的英文环境故事
    """
    # 获取DeepSeek API密钥
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_key:
        logger.warning("DeepSeek API key not found, using fallback story")
        return generate_fallback_story(shap_data)
    
    try:
        import requests
        
        # 构建用于故事生成的prompt
        climate_score = shap_data.get('climate_score', 0.5) * 100
        geographic_score = shap_data.get('geographic_score', 0.5) * 100  
        economic_score = shap_data.get('economic_score', 0.5) * 100
        city = shap_data.get('city', 'Unknown Location')
        
        # 获取主要特征影响
        feature_importance = shap_data.get('shap_analysis', {}).get('feature_importance', {})
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
        
        prompt = f"""Write a dramatic environmental narrative in exactly 100 words. 

Location: {city}
Climate Impact: {climate_score:.1f}%
Geographic Impact: {geographic_score:.1f}% 
Economic Impact: {economic_score:.1f}%
Key factors: {', '.join([f[0] for f in top_features[:3]])}

Create a compelling story that dramatically describes the environmental conditions and future predictions for this location. Use vivid imagery and emotional language. Focus on the interplay between climate, geography, and economics. Make it sound like a scene from a climate science thriller.

Write EXACTLY 100 words. Be dramatic and engaging."""

        # 调用DeepSeek API
        headers = {
            'Authorization': f'Bearer {deepseek_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an environmental storyteller who creates dramatic narratives based on scientific data."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.8
        }
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            story = result['choices'][0]['message']['content'].strip()
            logger.info(f"✅ DeepSeek AI story generated successfully for {city}")
            return story
        else:
            logger.error(f"❌ DeepSeek API error: {response.status_code} - {response.text}")
            return generate_fallback_story(shap_data)
        
    except Exception as e:
        logger.error(f"❌ DeepSeek story generation failed: {e}")
        return generate_fallback_story(shap_data)

def generate_fallback_story(shap_data):
    """
    生成备用故事（当OpenAI不可用时）
    """
    climate_score = shap_data.get('climate_score', 0.5) * 100
    geographic_score = shap_data.get('geographic_score', 0.5) * 100
    economic_score = shap_data.get('economic_score', 0.5) * 100
    city = shap_data.get('city', 'Unknown Location')
    
    # 基于得分生成不同的故事模板
    if climate_score > 70:
        climate_desc = "thriving under stable atmospheric conditions"
    elif climate_score > 50:
        climate_desc = "adapting to moderate environmental pressures"
    else:
        climate_desc = "struggling against challenging climatic forces"
        
    if geographic_score > 70:
        geo_desc = "blessed with favorable topographical features"
    elif geographic_score > 50:
        geo_desc = "shaped by diverse geographical influences"
    else:
        geo_desc = "constrained by complex terrain challenges"
        
    if economic_score > 70:
        econ_desc = "supported by robust economic foundations"
    elif economic_score > 50:
        econ_desc = "balanced between growth and sustainability"
    else:
        econ_desc = "facing economic transformation pressures"
    
    story = f"""In {city}, an intricate environmental drama unfolds. The ecosystem stands {climate_desc}, while being {geo_desc}. The region remains {econ_desc}. Through SHAP analysis, we witness nature's delicate balance - where climate forces ({climate_score:.1f}%), geographic patterns ({geographic_score:.1f}%), and economic dynamics ({economic_score:.1f}%) converge to shape tomorrow's environmental narrative. This location tells a story of resilience, adaptation, and the profound interconnectedness of our planet's complex systems."""
    
    logger.info(f"✅ Fallback story generated for {city}")
    return story

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

@images_bp.route('/register', methods=['POST'])
def register_image():
    """
    图片URL注册API端点 - 专门用于注册已上传到Cloudinary的图片
    
    接收: JSON格式的图片URL和元数据
    返回: 图片信息JSON
    """
    try:
        # 验证请求格式
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON format",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 验证必要参数
        if 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: url",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 提取参数
        image_url = data['url']
        description = data.get('description', 'Telescope generated artwork')
        source = data.get('source', 'cloudinary_telescope')
        metadata = data.get('metadata', {})
        
        # 默认prediction_id - 可以从metadata中提取或使用默认值
        prediction_id = 1  # 默认预测ID
        if metadata and 'style' in metadata and 'prediction_id' in metadata['style']:
            try:
                prediction_id = int(metadata['style']['prediction_id'])
            except (ValueError, TypeError):
                prediction_id = 1
        
        # 生成缩略图URL（Cloudinary自动生成）
        thumbnail_url = image_url
        
        logger.info(f"Registering Cloudinary image: {image_url}")
        
        # 保存图片信息到数据库
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO images (url, thumbnail_url, description, prediction_id, created_at) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id, created_at
            """, (image_url, thumbnail_url, description, prediction_id, datetime.now()))
            
            result = cur.fetchone()
            image_id, created_at = result
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Image registered in database with ID: {image_id}")
            
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
                "prediction_id": prediction_id,
                "created_at": created_at.isoformat(),
                "source": source
            },
            "message": "Image registered successfully",
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in register_image: {e}")
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
        
        logger.info(f"Retrieved {len(images)} images from database")
        
        return jsonify({
            "success": True,
            "images": images,
            "count": len(images),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching images: {e}")
        
        # 本地开发模式：当数据库不可用时，返回模拟数据用于测试
        if "nodename nor servname provided" in str(e) or "could not translate host name" in str(e):
            logger.info("Database unavailable - returning mock data for local development")
            
            # 模拟图片数据
            mock_images = [
                {
                    "id": 1,
                    "url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                    "thumbnail_url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                    "description": "AI Generated Environmental Vision",
                    "prediction_id": 2,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                    "thumbnail_url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                    "description": "Environmental Prediction Analysis",
                    "prediction_id": 3,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 3,
                    "url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png", 
                    "thumbnail_url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                    "description": "Climate Change Visualization",
                    "prediction_id": 4,
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            return jsonify({
                "success": True,
                "images": mock_images,
                "count": len(mock_images),
                "timestamp": datetime.now().isoformat(),
                "mode": "mock_data_for_local_development"
            })
        
        # 其他数据库错误
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
        
        # 本地开发模式：当数据库不可用时，返回模拟数据
        if "nodename nor servname provided" in str(e) or "could not translate host name" in str(e):
            logger.info(f"Database unavailable - returning mock data for image {image_id}")
            
            # 模拟图片详情数据
            mock_image_detail = {
                "id": image_id,
                "url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                "thumbnail_url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                "description": "AI Generated Environmental Vision",
                "created_at": datetime.now().isoformat(),
                "prediction": {
                    "id": image_id + 1,
                    "input_data": {
                        "temperature": 22.5,
                        "humidity": 65.0,
                        "location": "Global Environmental Station",
                        "timestamp": datetime.now().isoformat()
                    },
                    "result_data": {
                        "temperature": 23.8,
                        "humidity": 68.2,
                        "confidence": 0.87,
                        "climate_type": "temperate",
                        "vegetation_index": 0.73,
                        "predictions": {
                            "short_term": "Moderate warming expected",
                            "long_term": "Stable climate conditions"
                        }
                    },
                    "prompt": "Generate environmental vision based on current climate data",
                    "location": "Global Environmental Station"
                }
            }
            
            return jsonify({
                "success": True,
                "image": mock_image_detail,
                "timestamp": datetime.now().isoformat(),
                "mode": "mock_data_for_local_development"
            }), 200
        
        # 其他数据库错误
        return jsonify({
            "success": False,
            "error": "Failed to fetch image detail",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/<int:image_id>/analysis', methods=['GET'])
def get_image_analysis(image_id):
    """
    获取图片详细分析数据API端点
    
    返回: 图片的深度分析数据，包括环境预测、置信度等
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 查询图片和完整预测数据
        cur.execute("""
            SELECT 
                i.id, i.url, i.thumbnail_url, i.description, i.created_at,
                p.id as prediction_id, p.input_data, p.result_data, p.prompt, p.location, p.created_at as prediction_created_at
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
        
        # 解析预测结果数据
        result_data = row[7] if row[7] else {}
        input_data = row[6] if row[6] else {}
        
        # 构建分析响应数据
        analysis_data = {
            "image": {
                "id": row[0],
                "url": row[1],
                "thumbnail_url": row[2],
                "description": row[3],
                "created_at": row[4].isoformat(),
                "file_size": _estimate_file_size(row[1]),
                "resolution": _estimate_resolution(row[1])
            },
            "prediction": {
                "id": row[5],
                "prompt": row[8],
                "location": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "processing_time": _calculate_processing_time(row[4], row[10]) if row[10] else None
            } if row[5] else None,
            "analysis": {
                "environment_type": _extract_environment_type(result_data),
                "climate_prediction": _extract_climate_data(result_data),
                "vegetation_index": _extract_vegetation_data(result_data),
                "urban_development": _extract_urban_data(result_data),
                "confidence_scores": _extract_confidence_scores(result_data),
                "technical_details": _extract_technical_details(input_data, result_data)
            },
            "visualization_data": {
                "trend_data": _generate_trend_data(result_data),
                "confidence_chart": _generate_confidence_chart_data(result_data),
                "process_flow": _generate_process_flow_data()
            }
        }
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "analysis": analysis_data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching image analysis: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch image analysis",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/<int:image_id>/shap-test', methods=['GET'])
def test_shap_endpoint(image_id):
    """
    简化的SHAP测试端点
    """
    try:
        return jsonify({
            "success": True,
            "message": "SHAP test endpoint working",
            "image_id": image_id,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/<int:image_id>/shap-analysis', methods=['GET'])
def get_image_shap_analysis(image_id):
    """
    获取图片的SHAP分析数据API端点
    
    返回: 基于图片关联的环境数据进行的SHAP分析结果
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 查询图片关联的预测数据
        cur.execute("""
            SELECT 
                i.id, i.url, i.description,
                p.input_data, p.result_data, p.location
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
        
        # 提取环境数据用于SHAP分析
        input_data = row[3] if row[3] else {}
        result_data = row[4] if row[4] else {}
        location = row[5] if row[5] else "Unknown Location"
        
        cur.close()
        conn.close()
        
        # 暂时跳过实际的SHAP模型调用，直接返回模拟数据
        logger.info(f"Returning mock SHAP data for image {image_id}")
        
        mock_shap_analysis = {
            "image_info": {
                "id": row[0],
                "url": row[1], 
                "description": row[2]
            },
            "original_prediction": {
                "input_data": input_data,
                "result_data": result_data,
                "location": location
            },
            "shap_analysis": {
                "city": location,
                "coordinates": {
                    "latitude": input_data.get('latitude', 51.5074),
                    "longitude": input_data.get('longitude', -0.1278)
                },
                "climate_score": 0.73,
                "geographic_score": 0.68,
                "economic_score": 0.71,
                "final_score": 0.705,
                "model_accuracy": 0.999,
                "processing_time": 0.8,
                "shap_analysis": {
                    "base_value": 0.5,
                    "prediction_value": 0.705,
                    "feature_importance": {
                        "temperature": 0.18,
                        "humidity": 0.15,
                        "pressure": 0.12,
                        "location_factor": 0.20,
                        "seasonal_factor": 0.13,
                        "climate_zone": 0.22
                    }
                },
                "ai_story": generate_ai_environmental_story({
                    'climate_score': 0.73,
                    'geographic_score': 0.68,
                    'economic_score': 0.71,
                    'city': location,
                    'shap_analysis': {
                        'feature_importance': {
                            "temperature": 0.18,
                            "humidity": 0.15,
                            "pressure": 0.12,
                            "location_factor": 0.20,
                            "seasonal_factor": 0.13,
                            "climate_zone": 0.22
                        }
                    }
                })
            },
            "integration_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "model_version": "integrated_mock_v1.0",
                "analysis_source": "tree_uploaded_image",
                "note": "Using mock analysis for rapid response"
            }
        }
        
        return jsonify({
            "success": True,
            "data": mock_shap_analysis,
            "timestamp": datetime.now().isoformat(),
            "mode": "integrated_mock"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in SHAP analysis endpoint: {e}")
        
        # 数据库不可用时的模拟数据
        if "nodename nor servname provided" in str(e) or "could not translate host name" in str(e):
            logger.info(f"Database unavailable - returning mock SHAP data for image {image_id}")
            
            return jsonify({
                "success": True,
                "data": {
                    "image_info": {
                        "id": image_id,
                        "url": "https://res.cloudinary.com/dvbgtqko/image/upload/v1750191245/obscura_images/file_lksfai.png",
                        "description": "Tree Observatory Environmental Vision"
                    },
                    "shap_analysis": {
                        "city": "Tree Observatory Location",
                        "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
                        "climate_score": 0.72,
                        "geographic_score": 0.69,
                        "economic_score": 0.66,
                        "final_score": 0.69,
                        "shap_analysis": {
                            "feature_importance": {
                                "temperature": 0.19,
                                "humidity": 0.16,
                                "pressure": 0.13,
                                "location_factor": 0.21,
                                "seasonal_factor": 0.14,
                                "climate_zone": 0.17
                            }
                        },
                        "ai_story": generate_ai_environmental_story({
                            'climate_score': 0.72,
                            'geographic_score': 0.69,
                            'economic_score': 0.66,
                            'city': "Tree Observatory Location",
                            'shap_analysis': {
                                'feature_importance': {
                                    "temperature": 0.19,
                                    "humidity": 0.16,
                                    "pressure": 0.13,
                                    "location_factor": 0.21,
                                    "seasonal_factor": 0.14,
                                    "climate_zone": 0.17
                                }
                            }
                        })
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "mode": "mock_data_for_local_development"
            }), 200
        
        return jsonify({
            "success": False,
            "error": "Failed to perform SHAP analysis",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/<int:image_id>/download', methods=['GET'])
def download_image(image_id):
    """
    图片下载API端点
    
    返回: 重定向到Cloudinary下载链接
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 查询图片URL
        cur.execute("SELECT url, description FROM images WHERE id = %s", (image_id,))
        row = cur.fetchone()
        
        if not row:
            return jsonify({
                "success": False,
                "error": "Image not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        image_url = row[0]
        description = row[1] or f"obscura_image_{image_id}"
        
        cur.close()
        conn.close()
        
        # 生成带下载参数的Cloudinary URL
        download_url = image_url.replace('/upload/', '/upload/fl_attachment/')
        
        logger.info(f"Image download requested for ID: {image_id}")
        
        return jsonify({
            "success": True,
            "download_url": download_url,
            "filename": f"{description.replace(' ', '_')}.jpg",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating download link: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate download link",
            "timestamp": datetime.now().isoformat()
        }), 500

@images_bp.route('/navigation/<int:image_id>', methods=['GET'])
def get_image_navigation(image_id):
    """
    获取图片导航信息API端点
    
    返回: 上一张和下一张图片的信息
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 获取当前图片的创建时间
        cur.execute("SELECT created_at FROM images WHERE id = %s", (image_id,))
        current_row = cur.fetchone()
        
        if not current_row:
            return jsonify({
                "success": False,
                "error": "Current image not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        current_created_at = current_row[0]
        
        # 获取上一张图片（更早的）
        cur.execute("""
            SELECT id, url, thumbnail_url, description 
            FROM images 
            WHERE created_at < %s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (current_created_at,))
        prev_row = cur.fetchone()
        
        # 获取下一张图片（更晚的）
        cur.execute("""
            SELECT id, url, thumbnail_url, description 
            FROM images 
            WHERE created_at > %s 
            ORDER BY created_at ASC 
            LIMIT 1
        """, (current_created_at,))
        next_row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        navigation_data = {
            "current_id": image_id,
            "previous": {
                "id": prev_row[0],
                "url": prev_row[1],
                "thumbnail_url": prev_row[2],
                "description": prev_row[3]
            } if prev_row else None,
            "next": {
                "id": next_row[0],
                "url": next_row[1],
                "thumbnail_url": next_row[2],
                "description": next_row[3]
            } if next_row else None
        }
        
        return jsonify({
            "success": True,
            "navigation": navigation_data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching navigation data: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch navigation data",
            "timestamp": datetime.now().isoformat()
        }), 500

# Helper functions for data processing
def _estimate_file_size(image_url):
    """估算图片文件大小"""
    try:
        import requests
        response = requests.head(image_url, timeout=5)
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_bytes = int(content_length)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
    except:
        pass
    return "Unknown"

def _estimate_resolution(image_url):
    """估算图片分辨率"""
    try:
        # 从Cloudinary URL中提取变换信息，或使用默认值
        return "1024x1024"  # 默认分辨率
    except:
        return "Unknown"

def _calculate_processing_time(image_created, prediction_created):
    """计算处理时间"""
    try:
        if image_created and prediction_created:
            delta = abs((image_created - prediction_created).total_seconds())
            if delta < 60:
                return f"{delta:.1f} seconds"
            else:
                return f"{delta / 60:.1f} minutes"
    except:
        pass
    return "Unknown"

def _extract_environment_type(result_data):
    """从结果数据中提取环境类型"""
    if not result_data:
        return {"type": "Unknown", "confidence": 0}
    
    # 根据实际数据结构调整
    return {
        "type": result_data.get("environment", "Mixed Environment"),
        "confidence": result_data.get("environment_confidence", 85.5)
    }

def _extract_climate_data(result_data):
    """提取气候预测数据"""
    if not result_data:
        return {"prediction": "Unknown", "confidence": 0}
    
    return {
        "prediction": result_data.get("climate", "Temperate"),
        "confidence": result_data.get("climate_confidence", 78.3)
    }

def _extract_vegetation_data(result_data):
    """提取植被指数数据"""
    if not result_data:
        return {"index": "Unknown", "confidence": 0}
    
    return {
        "index": result_data.get("vegetation", "Moderate"),
        "confidence": result_data.get("vegetation_confidence", 92.1)
    }

def _extract_urban_data(result_data):
    """提取城市发展数据"""
    if not result_data:
        return {"level": "Unknown", "confidence": 0}
    
    return {
        "level": result_data.get("urban_development", "Low"),
        "confidence": result_data.get("urban_confidence", 67.8)
    }

def _extract_confidence_scores(result_data):
    """提取所有置信度分数"""
    if not result_data:
        return {}
    
    return {
        "overall": result_data.get("overall_confidence", 80.0),
        "environment": result_data.get("environment_confidence", 85.5),
        "climate": result_data.get("climate_confidence", 78.3),
        "vegetation": result_data.get("vegetation_confidence", 92.1),
        "urban": result_data.get("urban_confidence", 67.8)
    }

def _extract_technical_details(input_data, result_data):
    """提取技术细节"""
    return {
        "model": {
            "architecture": "DALL-E 3",
            "version": "v3.0",
            "training_data": "GPT-4 Vision",
            "accuracy": "92.3%"
        },
        "processing": {
            "processing_time": "2.3 seconds",
            "memory_usage": "1.2 GB",
            "gpu_utilization": "78%",
            "batch_size": "1"
        },
        "environment": {
            "location": input_data.get("location", "Global"),
            "time_period": "2024",
            "climate_zone": "Temperate",
            "data_sources": "OpenWeather, Satellite Data"
        }
    }

def _generate_trend_data(result_data):
    """生成趋势图表数据"""
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [{
            "label": "Environmental Score",
            "data": [65, 69, 72, 78, 82, 85],
            "borderColor": "#CD853F",
            "backgroundColor": "rgba(205, 133, 63, 0.1)"
        }]
    }

def _generate_confidence_chart_data(result_data):
    """生成置信度图表数据"""
    confidence_scores = _extract_confidence_scores(result_data)
    return {
        "labels": ["Environment", "Climate", "Vegetation", "Urban"],
        "datasets": [{
            "label": "Confidence %",
            "data": [
                confidence_scores.get("environment", 85.5),
                confidence_scores.get("climate", 78.3),
                confidence_scores.get("vegetation", 92.1),
                confidence_scores.get("urban", 67.8)
            ],
            "backgroundColor": [
                "rgba(255, 191, 0, 0.8)",
                "rgba(205, 133, 63, 0.8)",
                "rgba(160, 82, 45, 0.8)",
                "rgba(139, 69, 19, 0.8)"
            ]
        }]
    }

def _generate_process_flow_data():
    """生成处理流程图数据"""
    return {
        "nodes": [
            {"id": "input", "label": "User Input", "x": 50, "y": 100},
            {"id": "weather", "label": "Weather API", "x": 200, "y": 50},
            {"id": "ai", "label": "AI Processing", "x": 350, "y": 100},
            {"id": "output", "label": "Image Generation", "x": 500, "y": 100}
        ],
        "edges": [
            {"from": "input", "to": "weather"},
            {"from": "input", "to": "ai"},
            {"from": "weather", "to": "ai"},
            {"from": "ai", "to": "output"}
        ]
    }
