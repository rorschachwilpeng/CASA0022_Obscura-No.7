# Obscura No.7 端到端测试套件

## 📋 概述

本测试套件模拟完整的树莓派工作流程，验证从用户交互到网站展示的整个流程。

## 🔧 测试模块

### 1. 快速测试 (`quick_test.py`)
验证基本系统功能和API可用性。

```bash
python quick_test.py
```

**测试内容：**
- 系统状态检查
- ML预测API测试  
- Gallery页面访问
- 图片API验证

### 2. 完整端到端测试 (`e2e_test_suite.py`)
模拟完整的用户工作流程，包含多地点测试。

```bash
python e2e_test_suite.py
```

**测试流程：**
1. **用户交互模拟** - 编码器距离 + 磁感器方向
2. **坐标计算** - 距离+方向 → 经纬度转换
3. **ML预测API** - 环境数据预测
4. **网站验证** - Gallery和API功能

## 🌍 测试地点

- 🇬🇧 伦敦市中心 (51.5074, -0.1278)
- 🇨🇳 北京天安门 (39.9042, 116.4074)  
- 🇺🇸 纽约时代广场 (40.7589, -73.9851)
- 🇫🇷 巴黎埃菲尔铁塔 (48.8584, 2.2945)
- 🇯🇵 东京银座 (35.6762, 139.7653)

## 📊 输出文件

- `e2e_test.log` - 详细测试日志
- `e2e_test_report_YYYYMMDD_HHMMSS.json` - JSON测试报告

## 🎯 成功标准

- ✅ API响应时间 < 1秒
- ✅ 所有地点预测成功
- ✅ Gallery页面可访问
- ✅ 图片数据库连接正常

## 🔍 坐标计算公式

基于地球球面几何学的坐标计算：

```python
# 纬度变化
delta_lat = distance_km * cos(heading_rad) / earth_radius
target_lat = base_lat + delta_lat

# 经度变化 (考虑纬度余弦值)
delta_lon = distance_km * sin(heading_rad) / (earth_radius * cos(base_lat))
target_lon = base_lon + delta_lon
```

## 📈 性能基准

- **单次API调用：** ~0.25秒
- **完整工作流：** ~3-5秒
- **多地点测试：** ~2-3分钟

## 🐛 故障排除

### 常见问题：

1. **ModuleNotFoundError: requests**
   ```bash
   pip install requests
   ```

2. **API超时**
   - 检查网络连接
   - 验证Render部署状态

3. **坐标计算异常**
   - 检查距离范围 (0.1-50km)
   - 验证方向角度 (0-360°)

## 🔗 相关链接

- 网站地址: https://casa0022-obscura-no-7.onrender.com/
- Gallery: https://casa0022-obscura-no-7.onrender.com/gallery
- API文档: https://casa0022-obscura-no-7.onrender.com/api/status 