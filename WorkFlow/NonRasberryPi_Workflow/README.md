# Obscura No.7 项目实施计划 / Project Implementation Plan

## 📋 项目概述 / Project Overview

### 🇨🇳 中文版本

**Obscura No.7** 是一个基于树莓派的交互式虚拟望远镜艺术装置项目。该项目将物理交互（编码器控制距离、磁感器控制方向、时间变量）转换为AI生成的未来环境预测图像，并通过网站进行展示和存档。

### 🇺🇸 English Version

**Obscura No.7** is an interactive virtual telescope art installation project based on Raspberry Pi. This project converts physical interactions (encoder for distance control, magnetometer for direction control, time variables) into AI-generated future environmental prediction images, displayed and archived through a website.

---

## 🎯 项目目标 / Project Objectives

### 🇨🇳 中文版本

**核心目标：**
- 构建完整的"用户输入 → 环境数据获取 → ML预测 → AI图片生成 → 网站展示"工作流
- 开发基于环境数据的机器学习预测模型
- 创建展览级别的图片展示网站
- 实现树莓派端与云端服务的无缝集成

### 🇺🇸 English Version

**Core Objectives:**
- Build complete workflow: "User Input → Environmental Data → ML Prediction → AI Image Generation → Website Display"
- Develop machine learning prediction models based on environmental data
- Create exhibition-level image display website
- Achieve seamless integration between Raspberry Pi and cloud services

---

## 🚀 Stage 1: 打通整体工作流 (MVP版本) / Complete Workflow (MVP Version)

### 🇨🇳 中文版本

#### **1.1 本地环境搭建与Mock流程验证**✅
1. 搭建本地Python环境，安装必要依赖 (OpenAI, requests, flask等)✅
2. 实现OpenWeather API数据获取模块 (基于已有代码)✅
3. 创建Mock ML模型 (简单的线性回归或随机预测)✅
4. 集成OpenAI DALL-E API进行AI图片生成✅
5. 本地测试完整流程：`环境数据 → Mock预测 → AI图片生成 → 本地保存`✅

#### **1.2 云端基础设施部署**✅
1. 选择并设置云平台账户 (Heroku/Railway/Render)✅
2. 创建PostgreSQL数据库实例✅
3. 设置图片存储服务 (Cloudinary/AWS S3)✅
4. 配置环境变量和API密钥管理✅
5. 创建基础的Flask API应用框架✅

#### **1.3 ML模型服务化**✅
1. 将Mock ML模型包装成Flask API接口✅
2. 定义标准的输入输出JSON格式✅
3. 添加基础的数据验证和错误处理✅
4. 本地测试API接口功能✅
5. 部署ML API到云端并测试连接✅

#### **1.4 网站前后端开发**✅
1. 设计数据库schema (图片信息、预测数据、用户会话)✅
2. 开发后端API：图片上传、存储、检索功能✅
3. 创建简单的前端页面：展览式图片展示✅
4. 实现图片点击查看详情功能
5. 部署网站到云端✅

#### **1.5 端到端集成测试**✅
1. 测试完整云端工作流：`API调用 → ML预测 → 图片生成 → 网站显示`✅
2. 在MacOS本地编写测试脚本模拟树莓派输入✅
3. 验证图片同步和网站展示功能✅
4. 性能测试和错误处理验证✅
5. 为树莓派集成准备API接口文档✅

#### **1.6 树莓派端集成**✅
1. 修改现有树莓派脚本，集成云端API调用✅
2. 实现用户输入 → 坐标计算 → 环境数据获取 → API调用流程 → ML预测 → 图片生成 → 网站显示✅
3. 添加网络连接和错误处理机制✅
4. 现场测试完整的用户交互流程✅
5. 优化用户体验和响应时间✅

### 🇺🇸 English Version

#### **1.1 Local Environment Setup & Mock Process Validation**
1. Set up local Python environment, install necessary dependencies (OpenAI, requests, flask, etc.)
2. Implement OpenWeather API data acquisition module (based on existing code)
3. Create Mock ML model (simple linear regression or random prediction)
4. Integrate OpenAI DALL-E API for AI image generation
5. Local testing of complete process: `Environmental Data → Mock Prediction → AI Image Generation → Local Storage`

#### **1.2 Cloud Infrastructure Deployment**
1. Select and set up cloud platform account (Heroku/Railway/Render)
2. Create PostgreSQL database instance
3. Set up image storage service (Cloudinary/AWS S3)
4. Configure environment variables and API key management
5. Create basic Flask API application framework

#### **1.3 ML Model as a Service**
1. Wrap Mock ML model into Flask API interface
2. Define standard input/output JSON format
3. Add basic data validation and error handling
4. Local testing of API interface functionality
5. Deploy ML API to cloud and test connectivity

#### **1.4 Website Frontend & Backend Development**
1. Design database schema (image info, prediction data, user sessions)
2. Develop backend API: image upload, storage, retrieval functions
3. Create simple frontend pages: exhibition-style image display
4. Implement image click-to-view details functionality
5. Deploy website to cloud

#### **1.5 End-to-End Integration Testing**
1. Test complete cloud workflow: `API Call → ML Prediction → Image Generation → Website Display`
2. Write test scripts on MacOS to simulate Raspberry Pi input
3. Verify image synchronization and website display functionality
4. Performance testing and error handling validation
5. Prepare API interface documentation for Raspberry Pi integration

#### **1.6 Raspberry Pi Integration**
1. Modify existing Raspberry Pi scripts to integrate cloud API calls
2. Implement user input → coordinate calculation → environmental data acquisition → API call workflow
3. Add network connectivity and error handling mechanisms
4. On-site testing of complete user interaction process
5. Optimize user experience and response time

---

## 🔬 Stage 2: 深度优化与精确预测模型 / Deep Optimization & Accurate Prediction Models

### 🇨🇳 中文版本

#### **2.1 Background Research与变量选择**
1. 文献调研：环境预测相关的学术论文和实用模型
2. 确定关键环境变量：温度、湿度、空气质量、风速、季节性等
3. 评估各种环境数据API的可用性和成本
4. 设计变量重要性评估实验
5. 确定最终的输入特征集

#### **2.2 历史数据收集与处理**
1. 获取多源历史环境数据 (OpenWeather历史API、政府开放数据等)
2. 数据清洗：处理缺失值、异常值、格式统一
3. 特征工程：创建时间特征、季节性特征、地理特征
4. 数据质量评估和验证
5. 建立训练/验证/测试数据集

#### **2.3 机器学习模型开发**
1. 尝试多种回归模型：线性回归、随机森林、XGBoost、神经网络
2. 实现交叉验证和超参数调优
3. 模型性能评估：RMSE、MAE、R²等指标
4. 特征重要性分析和模型解释性
5. 选择最优模型并进行最终训练

#### **2.4 模型部署与API升级**
1. 模型序列化和版本管理
2. 更新ML API接口以支持新模型
3. 实现A/B测试框架 (新旧模型对比)
4. 添加模型监控和性能跟踪
5. 云端部署并进行压力测试

#### **2.5 AI图片生成优化**
1. 基于准确预测数据优化Prompt模板
2. 研究环境数据到视觉描述的映射关系
3. 实现多种图片风格和构图选项
4. 添加图片质量控制和筛选机制
5. 优化图片生成速度和成本

#### **2.6 系统性能优化与最终测试**
1. 整体系统性能优化：缓存、并发处理、数据库优化
2. 网站功能增强：更好的图片展示、搜索、过滤功能
3. 用户体验优化：响应时间、错误提示、加载状态
4. 全面的端到端测试和用户验收测试
5. 准备正式展览和项目文档

### 🇺🇸 English Version

#### **2.1 Background Research & Variable Selection**
1. Literature review: academic papers and practical models related to environmental prediction
2. Identify key environmental variables: temperature, humidity, air quality, wind speed, seasonality, etc.
3. Evaluate availability and cost of various environmental data APIs
4. Design variable importance assessment experiments
5. Determine final input feature set

#### **2.2 Historical Data Collection & Processing**
1. Acquire multi-source historical environmental data (OpenWeather historical API, government open data, etc.)
2. Data cleaning: handle missing values, outliers, format standardization
3. Feature engineering: create time features, seasonal features, geographical features
4. Data quality assessment and validation
5. Establish training/validation/testing datasets

#### **2.3 Machine Learning Model Development**
1. Try multiple regression models: linear regression, random forest, XGBoost, neural networks
2. Implement cross-validation and hyperparameter tuning
3. Model performance evaluation: RMSE, MAE, R² and other metrics
4. Feature importance analysis and model interpretability
5. Select optimal model and conduct final training

#### **2.4 Model Deployment & API Upgrade**
1. Model serialization and version management
2. Update ML API interface to support new models
3. Implement A/B testing framework (new vs old model comparison)
4. Add model monitoring and performance tracking
5. Cloud deployment and stress testing

#### **2.5 AI Image Generation Optimization**
1. Optimize Prompt templates based on accurate prediction data
2. Research mapping relationships from environmental data to visual descriptions
3. Implement multiple image styles and composition options
4. Add image quality control and filtering mechanisms
5. Optimize image generation speed and cost

#### **2.6 System Performance Optimization & Final Testing**
1. Overall system performance optimization: caching, concurrent processing, database optimization
2. Website functionality enhancement: better image display, search, filtering features
3. User experience optimization: response time, error messages, loading states
4. Comprehensive end-to-end testing and user acceptance testing
5. Prepare for official exhibition and project documentation

---
 dd d