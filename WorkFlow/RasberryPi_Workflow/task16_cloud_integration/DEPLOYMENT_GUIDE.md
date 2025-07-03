# TASK1.6 - Obscura No.7 增强版虚拟望远镜部署指南

## 🎯 项目概述

TASK1.6 实现了完整的硬件集成云端AI工作流，结合：
- 🔧 硬件交互（距离编码器、时间编码器、磁感器）
- 🌐 云端AI服务（OpenAI、OpenWeather、Cloudinary）
- 🎨 智能图像生成与网站上传

## 📋 系统要求

### 硬件要求
- Raspberry Pi 4 (推荐)
- I2C 编码器 x2 (距离控制、时间控制)
- QMC5883L 磁感器 (方向控制)
- 800x800 显示屏 (可选)

### 软件要求
- Python 3.9+
- pip 包管理器
- Git

## 🚀 快速部署

### 1. 克隆代码仓库
```bash
git clone https://github.com/your-repo/CASA0022_Obscura-No.7.git
cd CASA0022_Obscura-No.7/WorkFlow/RasberryPi_Workflow/task16_cloud_integration
```

### 2. 安装依赖
```bash
pip install -r ../../../requirements.txt
```

### 3. 配置API密钥
```bash
# 复制配置模板
cp config.json.template config.json

# 编辑配置文件
nano config.json
```

### 4. 必需的API密钥

在 `config.json` 中替换以下占位符：

```json
{
  "api_keys": {
    "openweather_api_key": "YOUR_OPENWEATHER_API_KEY_HERE",
    "openai_api_key": "YOUR_OPENAI_API_KEY_HERE", 
    "google_maps_api_key": "YOUR_GOOGLE_MAPS_API_KEY_HERE",
    "cloudinary_url": "cloudinary://key:secret@cloud_name"
  }
}
```

#### 获取API密钥：
- **OpenWeather**: [openweathermap.org/api](https://openweathermap.org/api)
- **OpenAI**: [platform.openai.com](https://platform.openai.com)
- **Google Maps**: [console.cloud.google.com](https://console.cloud.google.com)
- **Cloudinary**: [cloudinary.com](https://cloudinary.com)

### 5. 硬件连接

确保I2C设备连接正确：
- 距离编码器: I2C总线3，地址0x36
- 磁感器: I2C总线4，地址0x0d  
- 时间编码器: I2C总线5，地址0x36

### 6. 运行系统
```bash
python main_telescope.py
```

## 🎮 使用说明

### 硬件操作
1. **🔄 距离编码器**: 旋转调整探索距离 (1-50km)
2. **📅 时间编码器**: 旋转选择预测年份 (2025-2075)
3. **🧭 旋转设备**: 物理旋转选择探索方向
4. **🔘 时间编码器按钮**: 确认参数并启动AI工作流

### 工作流程
1. **Phase 1**: 硬件参数选择
2. **Phase 2**: 云端AI工作流执行
   - 坐标计算
   - 环境数据获取 (OpenWeather API)
   - AI艺术预测 (OpenAI)
   - 图像生成 (DALL-E)
   - 结果保存与上传 (Cloudinary)
3. **Phase 3**: 结果展示

## 🔧 配置选项

### 硬件设置
```json
"hardware_settings": {
  "distance_bus": 3,    // 距离编码器I2C总线
  "compass_bus": 4,     // 磁感器I2C总线  
  "time_bus": 5,        // 时间编码器I2C总线
  "encoder_addr": "0x36" // 编码器I2C地址
}
```

### 望远镜参数
```json
"telescope_settings": {
  "base_location": {
    "latitude": 51.5074,   // 基础位置纬度
    "longitude": -0.1278,  // 基础位置经度
    "name": "London, UK"
  },
  "distance_range": {
    "min_km": 1,          // 最小探索距离
    "max_km": 50,         // 最大探索距离
    "step_km": 1          // 距离步进
  }
}
```

### 图像生成设置
```json
"image_generation": {
  "width": 1024,                    // 图像宽度
  "height": 1024,                   // 图像高度
  "style_prompt_prefix": "A beautiful artistic interpretation...",
  "quality": "standard",            // 图像质量
  "steps": 30,                      // 生成步数
  "cfg_scale": 7.0                  // 提示词遵循度
}
```

## 🐛 故障排除

### 常见问题

#### 1. I2C设备连接失败
```bash
# 检查I2C设备
sudo i2cdetect -y 1
```

#### 2. API密钥错误
- 检查 `config.json` 中的API密钥格式
- 确认API密钥有效且有足够额度

#### 3. 权限问题
```bash
# 添加用户到i2c组
sudo usermod -a -G i2c $USER
# 重启后生效
```

#### 4. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip
# 单独安装problematic包
pip install package_name
```

### 调试模式
在 `config.json` 中启用详细日志：
```json
"debugging": {
  "verbose_logging": true,
  "save_api_responses": true,
  "log_file": "./logs/telescope_workflow.log"
}
```

## 📁 文件结构
```
task16_cloud_integration/
├── main_telescope.py           # 主启动脚本
├── enhanced_telescope.py       # 硬件控制模块
├── obscura_workflow.py         # 云端工作流
├── cloud_api_client.py         # API客户端
├── config_manager.py           # 配置管理
├── progress_display.py         # 进度显示
├── coordinate_calculator.py    # 坐标计算
├── weather_client.py           # 天气API客户端
├── config.json.template        # 配置模板
├── generated_images/           # 生成的图像 (git忽略)
├── workflow_outputs/           # 工作流结果 (git忽略)
└── logs/                       # 日志文件 (git忽略)
```

## 🌐 网站集成

生成的图像会自动上传到展示网站：
- **网站**: https://casa0022-obscura-no-7.onrender.com/
- **API**: 环境数据和图像上传
- **Gallery**: 实时查看生成的艺术作品

## 🔒 安全注意事项

- ✅ `config.json` 已添加到 `.gitignore`
- ✅ 敏感目录（logs, generated_images）被Git忽略
- ⚠️ 不要在公共仓库中提交包含真实API密钥的文件
- 💡 使用环境变量可以覆盖配置文件中的设置

## 📞 支持

如有问题，请检查：
1. 硬件连接是否正确
2. API密钥是否有效
3. 网络连接是否正常
4. 日志文件中的详细错误信息

---

**更新日期**: 2025-07-03  
**版本**: TASK1.6 - 增强版硬件集成云端工作流 