# 🔭 Obscura No.7 API文档

## 概述
Obscura No.7是一个蒸汽朋克风格的虚拟望远镜艺术装置API，提供天气预测和图像生成服务。

**基础URL**: `https://casa0022-obscura-no-7.onrender.com`  
**文档生成时间**: 2025-06-20 12:30:48  
**API版本**: v1.0  

## 🚀 快速开始

### 认证
当前API无需认证，直接使用即可。

### 请求格式
- **Content-Type**: `application/json`
- **Accept**: `application/json`
- **User-Agent**: 推荐设置为具体的应用名称

## 📚 API端点

### 1. 系统健康检查

#### GET `/api/v1/health`
检查系统各组件状态

**请求示例**:
```bash
curl -X GET "https://casa0022-obscura-no-7.onrender.com/api/v1/health"
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-20T12:00:00.000Z",
  "services": {
    "database": "online",
    "ml_model": "online", 
    "image_storage": "online",
    "external_apis": "online",
    "file_system": "online",
    "memory_usage": "online"
  },
  "uptime": "0 days, 2 hours, 30 minutes",
  "version": "1.0.0"
}
```

### 2. 机器学习预测

#### POST `/api/v1/ml/predict`
基于环境数据进行天气预测

**请求体参数**:
- `environmental_data` (object, required): 环境数据
  - `latitude` (float, required): 纬度 (-90 to 90)
  - `longitude` (float, required): 经度 (-180 to 180)
  - `temperature` (float, required): 当前温度 (°C)
  - `humidity` (integer, required): 湿度 (0-100%)
  - `pressure` (integer, required): 大气压强 (hPa)
  - `wind_speed` (float, required): 风速 (m/s)
  - `weather_description` (string, required): 天气描述
  - `location_name` (string, required): 地点名称
- `hours_ahead` (integer, required): 预测未来小时数 (6-168)

**请求示例**:
```bash
curl -X POST "https://casa0022-obscura-no-7.onrender.com/api/v1/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "environmental_data": {
      "latitude": 51.5074,
      "longitude": -0.1278,
      "temperature": 20.5,
      "humidity": 65,
      "pressure": 1013,
      "wind_speed": 5.2,
      "weather_description": "partly cloudy",
      "location_name": "London, UK"
    },
    "hours_ahead": 24
  }'
```

**响应示例**:
```json
{
  "success": true,
  "prediction": {
    "predicted_temperature": 18.7,
    "predicted_humidity": 72.3,
    "predicted_weather_condition": "light rain",
    "confidence_score": 0.85,
    "model_version": "mock_v1.0",
    "prediction_timestamp": "2025-06-20T12:00:00.000Z"
  },
  "input_data": {
    "location": "London, UK",
    "coordinates": [51.5074, -0.1278],
    "hours_ahead": 24
  },
  "processing_time": "0.245s"
}
```

### 3. 图像管理

#### GET `/api/v1/images`
获取所有生成的图像列表

**查询参数**:
- `page` (integer, optional): 页码，默认1
- `limit` (integer, optional): 每页数量，默认20
- `sort` (string, optional): 排序方式，可选 'newest', 'oldest'

**请求示例**:
```bash
curl -X GET "https://casa0022-obscura-no-7.onrender.com/api/v1/images?page=1&limit=10&sort=newest"
```

**响应示例**:
```json
{
  "success": true,
  "images": [
    {
      "id": 1,
      "filename": "weather_prediction_20250620_120000.png",
      "public_id": "obscura/img_001",
      "url": "https://res.cloudinary.com/...",
      "created_at": "2025-06-20T12:00:00Z",
      "prediction_data": {
        "temperature": 18.7,
        "weather_condition": "light rain",
        "location": "London, UK"
      }
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_images": 25,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET `/api/v1/images/<image_id>`
获取特定图像的详细信息

**路径参数**:
- `image_id` (integer, required): 图像ID

**请求示例**:
```bash
curl -X GET "https://casa0022-obscura-no-7.onrender.com/api/v1/images/1"
```

**响应示例**:
```json
{
  "success": true,
  "image": {
    "id": 1,
    "filename": "weather_prediction_20250620_120000.png",
    "public_id": "obscura/img_001",
    "url": "https://res.cloudinary.com/...",
    "created_at": "2025-06-20T12:00:00Z",
    "prediction_data": {
      "predicted_temperature": 18.7,
      "predicted_humidity": 72.3,
      "predicted_weather_condition": "light rain",
      "confidence_score": 0.85,
      "location": "London, UK",
      "coordinates": [51.5074, -0.1278]
    },
    "environmental_input": {
      "temperature": 20.5,
      "humidity": 65,
      "pressure": 1013,
      "wind_speed": 5.2
    }
  }
}
```

## ⚠️ 错误处理

### HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源未找到
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid latitude value",
    "details": "Latitude must be between -90 and 90"
  }
}
```

## 🔧 性能指标

基于最新性能测试结果:
- **平均响应时间**: 0.246秒
- **并发处理能力**: 5.91 请求/秒
- **系统可用性**: 100%
- **边界条件支持**: 完全支持极端地理坐标

## 📱 前端界面

### 网站访问
- **主页**: `https://casa0022-obscura-no-7.onrender.com/`
- **图像画廊**: `https://casa0022-obscura-no-7.onrender.com/gallery`
- **关于页面**: `https://casa0022-obscura-no-7.onrender.com/about`

### 特色功能
- 🔭 蒸汽朋克风格望远镜界面
- 🎨 AI生成的天气艺术图像
- 📊 实时数据可视化
- 📱 响应式设计支持

## 🤝 技术支持

如需技术支持或报告问题，请联系开发团队。

---
**生成时间**: 2025-06-20 12:30:48  
**API版本**: v1.0  
**文档版本**: 1.0  
