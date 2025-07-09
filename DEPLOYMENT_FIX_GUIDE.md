# 🔧 Render部署修复指南

## 问题诊断
- ✅ 本地环境完全正常
- ✅ SHAP API和前端页面都已创建
- ❌ Render部署时pandas依赖安装失败

## 🚀 解决方案

### 方案1：分步部署（推荐）

1. **先部署基础版本**
```bash
# 1. 重命名当前requirements.txt
mv api/requirements.txt api/requirements_full.txt

# 2. 创建基础版本
cat > api/requirements.txt << EOF
Flask==2.3.2
python-dotenv==1.0.0
requests==2.31.0
Pillow==10.0.0
cloudinary==1.33.0
psycopg2-binary==2.9.6
numpy==1.24.3
scikit-learn==1.3.0
joblib==1.3.1
gunicorn==21.2.0
EOF

# 3. 部署基础版本
git add .
git commit -m "Deploy basic version without SHAP"
git push
```

2. **基础版本稳定后，添加SHAP**
```bash
# 等基础版本部署成功后
mv api/requirements_full.txt api/requirements.txt
git add .
git commit -m "Add SHAP functionality"
git push
```

### 方案2：优化依赖安装

在Render部署设置中添加构建命令：
```bash
pip install --upgrade pip setuptools wheel
pip install numpy==1.24.3
pip install pandas==2.0.3  
pip install scipy==1.11.1
pip install -r requirements.txt
```

### 方案3：使用Docker（最稳定）

创建 `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
```

## 🎯 当前功能状态

### ✅ 已完成
- SHAP环境预测API (`/api/v1/shap/*`)
- SHAP前端页面 (`/shap`)
- 错误处理和优雅降级
- 完整的可解释性分析

### 🔍 功能预览
访问 `yoursite.com/shap` 可以：
- 输入坐标和月份
- 获得环境评分
- 查看SHAP特征重要性分析
- 可视化预测过程

## 📊 API使用示例

```bash
curl -X POST https://yoursite.com/api/v1/shap/predict \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 51.5074,
    "longitude": -0.1278,
    "month": 7,
    "analyze_shap": true
  }'
```

## 🛠️ 调试命令

检查部署状态：
```bash
curl https://yoursite.com/api/v1/shap/health
```

## 💡 建议
1. 先用方案1确保基础功能稳定
2. 在Render日志中监控pandas安装过程
3. 成功后可以添加更多ML功能

---
*Obscura No.7 - Virtual Telescope System* 