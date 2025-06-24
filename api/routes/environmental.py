#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environmental Data API Routes - 环境数据上传与管理API端点
"""

from flask import Blueprint, request, jsonify
import psycopg2
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 创建蓝图
environmental_bp = Blueprint('environmental', __name__, url_prefix='/api/v1/environmental')

@environmental_bp.route('/upload', methods=['POST'])
def upload_environmental_data():
    """
    环境数据上传API端点
    
    接收: JSON格式的环境数据和坐标信息
    返回: 确认信息和数据ID
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 验证必要字段
        required_fields = ['coordinates', 'weather_data', 'timestamp', 'source']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 提取数据
        coordinates = data['coordinates']
        weather_data = data['weather_data']
        timestamp = data['timestamp']
        source = data['source']
        
        # 提取具体的环境参数
        current_weather = weather_data.get('current_weather', {})
        air_quality = weather_data.get('air_quality', {})
        
        # 保存环境数据到数据库
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            
            # 创建环境数据记录
            cur.execute("""
                INSERT INTO environmental_data (
                    latitude, longitude, timestamp, source,
                    temperature, humidity, pressure, wind_speed, wind_direction,
                    weather_description, weather_main, cloud_cover, visibility,
                    aqi, pm2_5, pm10, no2, so2, co, o3,
                    raw_data, created_at
                ) VALUES (
                    %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s
                ) RETURNING id
            """, (
                coordinates.get('latitude'),
                coordinates.get('longitude'),
                timestamp,
                source,
                current_weather.get('temperature'),
                current_weather.get('humidity'),
                current_weather.get('pressure'),
                current_weather.get('wind_speed'),
                current_weather.get('wind_direction'),
                current_weather.get('weather_description'),
                current_weather.get('weather_main'),
                current_weather.get('cloud_cover'),
                current_weather.get('visibility'),
                air_quality.get('aqi'),
                air_quality.get('pm2_5'),
                air_quality.get('pm10'),
                air_quality.get('no2'),
                air_quality.get('so2'),
                air_quality.get('co'),
                air_quality.get('o3'),
                str(data),  # 原始JSON数据
                datetime.now()
            ))
            
            env_data_id = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Environmental data saved with ID: {env_data_id}")
            
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
            "environmental_data": {
                "id": env_data_id,
                "latitude": coordinates.get('latitude'),
                "longitude": coordinates.get('longitude'),
                "temperature": current_weather.get('temperature'),
                "weather_description": current_weather.get('weather_description'),
                "timestamp": timestamp,
                "source": source
            },
            "message": "Environmental data uploaded successfully",
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in upload_environmental_data: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500

@environmental_bp.route('', methods=['GET'])
def get_environmental_data():
    """
    获取环境数据列表API端点
    
    支持查询参数: limit, offset, start_date, end_date
    返回: 环境数据列表
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # 构建查询
        base_query = """
            SELECT id, latitude, longitude, timestamp, source,
                   temperature, humidity, pressure, wind_speed,
                   weather_description, weather_main, aqi, created_at
            FROM environmental_data
        """
        
        conditions = []
        params = []
        
        if start_date:
            conditions.append("timestamp >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("timestamp <= %s")
            params.append(end_date)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(base_query, params)
        
        environmental_data = []
        for row in cur.fetchall():
            environmental_data.append({
                "id": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "timestamp": row[3],
                "source": row[4],
                "temperature": row[5],
                "humidity": row[6],
                "pressure": row[7],
                "wind_speed": row[8],
                "weather_description": row[9],
                "weather_main": row[10],
                "aqi": row[11],
                "created_at": row[12].isoformat() if row[12] else None
            })
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM environmental_data"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions[:-2])  # 排除limit/offset参数
            cur.execute(count_query, params[:-2])
        else:
            cur.execute(count_query)
        
        total_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "environmental_data": environmental_data,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get environmental data: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve environmental data",
            "timestamp": datetime.now().isoformat()
        }), 500

@environmental_bp.route('/<int:env_data_id>', methods=['GET'])
def get_environmental_data_detail(env_data_id):
    """
    获取特定环境数据详情
    """
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, latitude, longitude, timestamp, source,
                   temperature, humidity, pressure, wind_speed, wind_direction,
                   weather_description, weather_main, cloud_cover, visibility,
                   aqi, pm2_5, pm10, no2, so2, co, o3,
                   raw_data, created_at
            FROM environmental_data 
            WHERE id = %s
        """, (env_data_id,))
        
        row = cur.fetchone()
        
        if not row:
            return jsonify({
                "success": False,
                "error": "Environmental data not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        environmental_data = {
            "id": row[0],
            "coordinates": {
                "latitude": row[1],
                "longitude": row[2]
            },
            "timestamp": row[3],
            "source": row[4],
            "weather": {
                "temperature": row[5],
                "humidity": row[6],
                "pressure": row[7],
                "wind_speed": row[8],
                "wind_direction": row[9],
                "weather_description": row[10],
                "weather_main": row[11],
                "cloud_cover": row[12],
                "visibility": row[13]
            },
            "air_quality": {
                "aqi": row[14],
                "pm2_5": row[15],
                "pm10": row[16],
                "no2": row[17],
                "so2": row[18],
                "co": row[19],
                "o3": row[20]
            },
            "raw_data": row[21],
            "created_at": row[22].isoformat() if row[22] else None
        }
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "environmental_data": environmental_data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get environmental data detail: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve environmental data detail",
            "timestamp": datetime.now().isoformat()
        }), 500 