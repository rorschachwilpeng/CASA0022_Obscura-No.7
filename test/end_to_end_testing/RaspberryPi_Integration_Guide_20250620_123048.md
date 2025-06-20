# 🍓 Obscura No.7 树莓派集成指南

## 概述
本指南将帮助您将Obscura No.7系统集成到树莓派硬件平台上，实现完整的物理交互体验。

**文档生成时间**: 2025-06-20 12:30:48

## 🎯 系统架构

```
[用户交互] → [树莓派] → [云端API] → [AI生成] → [网站展示]
     ↓           ↓          ↓           ↓           ↓
  旋转编码器    坐标计算   ML预测      图像生成    蒸汽朋克界面
  磁力计传感器  环境数据   天气预测    艺术风格    实时展示
```

## 🛠️ 硬件要求

### 必需组件
- **树莓派 4B** (推荐4GB+内存)
- **旋转编码器** (I2C接口)
- **磁力计** (HMC5883L或类似)
- **E-ink显示屏** (可选，用于本地显示)
- **Wi-Fi连接** (访问云端API)

### 可选组件
- GPS模块 (自动定位)
- 环境传感器 (温湿度、气压)
- 扬声器 (音效反馈)

## 📦 软件依赖

### 系统要求
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python依赖
sudo apt install python3-pip python3-venv git -y

# 启用I2C
sudo raspi-config nonint do_i2c 0
```

### Python包安装
```bash
# 创建虚拟环境
python3 -m venv obscura_env
source obscura_env/bin/activate

# 安装依赖
pip install requests numpy adafruit-circuitpython-seesaw
pip install RPi.GPIO smbus2 board digitalio
```

## 🔧 硬件连接

### I2C设备连接
```
树莓派引脚连接:
┌─────────────────┐
│ 3.3V  → VCC     │ (编码器和磁力计)
│ GND   → GND     │ (编码器和磁力计)  
│ SDA   → SDA     │ (GPIO 2)
│ SCL   → SCL     │ (GPIO 3)
└─────────────────┘
```

### 编码器地址配置
```python
# I2C地址设置
ENCODER_ADDRESS = 0x36  # 默认编码器地址
COMPASS_ADDRESS = 0x1E  # HMC5883L地址
```

## 💻 代码实现

### 主要模块结构
```
raspberry_pi_integration/
├── main.py              # 主程序入口
├── hardware/
│   ├── encoder.py       # 编码器控制
│   ├── compass.py       # 磁力计读取
│   └── display.py       # 显示控制
├── api/
│   ├── client.py        # API客户端
│   └── data_processor.py # 数据处理
└── utils/
    ├── coordinates.py   # 坐标计算
    └── config.py        # 配置管理
```

### 核心坐标计算
```python
import math

def encoder_to_coordinates(encoder_position, compass_bearing, base_lat=51.5074, base_lon=-0.1278):
    """
    将编码器位置和磁力计方向转换为地理坐标
    
    Args:
        encoder_position: 编码器位置 (0-1023)
        compass_bearing: 磁力计方向 (0-359度)
        base_lat: 基准纬度
        base_lon: 基准经度
    
    Returns:
        tuple: (latitude, longitude)
    """
    # 将编码器位置转换为距离 (0-20000公里)
    max_distance_km = 20000
    distance_km = (encoder_position / 1023.0) * max_distance_km
    
    # 将方向转换为弧度
    bearing_rad = math.radians(compass_bearing)
    
    # 地球半径
    earth_radius_km = 6371.0
    
    # 计算目标坐标
    lat1_rad = math.radians(base_lat)
    lon1_rad = math.radians(base_lon)
    
    lat2_rad = math.asin(
        math.sin(lat1_rad) * math.cos(distance_km / earth_radius_km) +
        math.cos(lat1_rad) * math.sin(distance_km / earth_radius_km) * math.cos(bearing_rad)
    )
    
    lon2_rad = lon1_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_km / earth_radius_km) * math.cos(lat1_rad),
        math.cos(distance_km / earth_radius_km) - math.sin(lat1_rad) * math.sin(lat2_rad)
    )
    
    return math.degrees(lat2_rad), math.degrees(lon2_rad)
```

### API客户端示例
```python
import requests
import json
from datetime import datetime

class ObscuraAPIClient:
    def __init__(self, base_url="https://casa0022-obscura-no-7.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Obscura-RaspberryPi/1.0'
        })
    
    def predict_weather(self, lat, lon, temperature=20.0, humidity=65):
        """发送天气预测请求"""
        payload = {
            "environmental_data": {
                "latitude": lat,
                "longitude": lon,
                "temperature": temperature,
                "humidity": humidity,
                "pressure": 1013,
                "wind_speed": 5.0,
                "weather_description": "clear sky",
                                 "location_name": f"Location_{lat:.2f}_{lon:.2f}"
            },
            "hours_ahead": 24
        }
        
        try:
                         response = self.session.post(
                 f"{{self.base_url}}/api/v1/ml/predict",
                json=payload,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
```

## 🚀 部署步骤

### 1. 克隆代码库
```bash
git clone https://github.com/your-repo/CASA0022_Obscura-No.7.git
cd CASA0022_Obscura-No.7
```

### 2. 配置硬件
```bash
# 检测I2C设备
sudo i2cdetect -y 1

# 应该显示:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- 1e -- 
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 30: -- -- -- -- -- -- 36 -- -- -- -- -- -- -- -- --
```

### 3. 测试硬件连接
```bash
cd Hardware/
python3 encoder_test.py       # 测试编码器
python3 qmc5883l.py          # 测试磁力计
```

### 4. 运行主程序
```bash
cd WorkFlow/RasberryPi_Workflow/
python3 simple_workflow.py
```

## 🔄 工作流程

### 完整交互流程
1. **用户操作**: 转动编码器，调整方向
2. **硬件读取**: 获取编码器位置和磁力计数据
3. **坐标计算**: 转换为地理坐标
4. **环境数据**: 读取本地传感器(可选)
5. **API请求**: 发送数据到云端进行ML预测
6. **结果处理**: 接收预测结果
7. **本地显示**: 在E-ink屏幕显示结果
8. **网站更新**: 图像自动添加到在线画廊

### 自动运行服务
```bash
# 创建systemd服务
sudo nano /etc/systemd/system/obscura.service

[Unit]
Description=Obscura No.7 Telescope Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/CASA0022_Obscura-No.7
ExecStart=/home/pi/obscura_env/bin/python WorkFlow/RasberryPi_Workflow/simple_workflow.py
Restart=always

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl enable obscura.service
sudo systemctl start obscura.service
```

## 🐛 故障排除

### 常见问题

#### I2C设备无法检测
```bash
# 检查I2C是否启用
sudo raspi-config nonint get_i2c
# 输出应该是0

# 重新启用I2C
sudo raspi-config nonint do_i2c 0
sudo reboot
```

#### API连接失败
```bash
# 测试网络连接
ping casa0022-obscura-no-7.onrender.com

# 测试API健康状况
curl -X GET "https://casa0022-obscura-no-7.onrender.com/api/v1/health"
```

#### 编码器读取异常
```python
# 调试编码器
import board
import digitalio
from adafruit_seesaw.seesaw import Seesaw

try:
    i2c = board.I2C()
    seesaw = Seesaw(i2c, addr=0x36)
    print(f"编码器位置: {seesaw.encoder_position()}")
except Exception as e:
    print(f"编码器错误: {e}")
```

## 📊 性能优化

### 系统调优
```bash
# GPU内存分配
echo 'gpu_mem=16' >> /boot/config.txt

# 禁用不必要服务
sudo systemctl disable bluetooth.service
sudo systemctl disable wifi-powersave@wlan0.service
```

### 代码优化
- 使用缓存减少API调用频率
- 异步处理长时间任务
- 实现本地错误恢复机制

## 🎨 定制化

### 修改坐标计算范围
```python
# 在coordinates.py中调整
MAX_DISTANCE_KM = 10000  # 减少最大距离
RESOLUTION_STEPS = 2048  # 增加精度
```

### 添加本地传感器
```python
# 集成DHT22温湿度传感器
import Adafruit_DHT

def read_local_environment():
    humidity, temperature = Adafruit_DHT.read_retry(
        Adafruit_DHT.DHT22, 4  # GPIO 4
    )
    return temperature, humidity
```

## 📞 技术支持

如遇到问题，请:
1. 检查硬件连接
2. 查看日志文件
3. 测试网络连接
4. 联系开发团队

---
**文档版本**: 1.0  
**适用系统**: Raspberry Pi OS (Bullseye)  
**更新时间**: 2025-06-20 12:30:48
