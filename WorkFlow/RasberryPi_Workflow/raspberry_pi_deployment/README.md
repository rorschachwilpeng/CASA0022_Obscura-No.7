# 🔭 Obscura No.7 - Raspberry Pi Deployment

**虚拟望远镜树莓派部署版本**

## 📁 文件夹结构

```
raspberry_pi_deployment/
├── main.py                     # 🚀 主程序入口
├── requirements.txt           # 📦 Python依赖包
│
├── 📂 core/                   # 🔧 核心功能模块
│   ├── cloud_api_client.py   # ☁️ 云端API客户端
│   ├── config_manager.py     # ⚙️ 配置管理器
│   ├── coordinate_calculator.py # 📐 坐标计算器
│   ├── image_prompt_builder.py # 🎨 图像提示构建器
│   ├── maps_client.py         # 🗺️ 地图客户端
│   ├── obscura_workflow.py    # 🔄 主工作流逻辑
│   ├── open_meteo_client.py   # 🌤️ Open-Meteo天气客户端
│   ├── progress_display.py    # 📊 进度显示界面
│   ├── raspberry_pi_hardware.py # 🍓 树莓派硬件接口
│   └── weather_client.py      # 🌡️ OpenWeather客户端
│
├── 📂 config/                 # ⚙️ 配置文件
│   ├── config.json           # 🔧 主配置文件
│   └── env_template.txt      # 📝 环境变量模板
│
├── 📂 workflows/              # 🔄 工作流程序
│   └── telescope_workflow.py # 🔭 望远镜工作流
│
├── 📂 scripts/                # 📜 执行脚本
│   ├── install_dependencies.sh # 🔽 依赖安装脚本
│   └── launch_telescope.sh    # 🚀 启动脚本
│
├── 📂 tests/                  # 🧪 测试文件
│   └── test_ml_api_integration.py # 🤖 ML API集成测试
│
├── 📂 docs/                   # 📚 文档文件
│   ├── TASK_PROGRESS_CHECKLIST.md # ✅ 任务进度清单
│   ├── DEPLOYMENT_GUIDE.md   # 🚀 部署指南
│   ├── INTEGRATION_SUMMARY.md # 🔗 集成总结
│   └── NETWORK_OPTIMIZATION_GUIDE.md # 🌐 网络优化指南
│
└── 📂 data/                   # 💾 数据文件
    └── .cache.sqlite         # 🗄️ 缓存数据库
```

## 🚀 快速启动

### 方法1: 使用启动脚本 (推荐)
```bash
# 从任何位置运行
./scripts/launch_telescope.sh
```

### 方法2: 直接运行
```bash
# 在项目根目录运行
python3 main.py
```

## 🔧 功能模块说明

### 🍓 核心模块 (core/)
- **硬件接口**: 处理编码器、磁感器、按钮等树莓派硬件
- **API客户端**: 集成OpenWeather、Open-Meteo、Google Maps等API
- **工作流引擎**: 管理6步望远镜操作流程
- **图像生成**: AI图像提示构建和云端生成

### ⚙️ 配置管理 (config/)
- **统一配置**: 所有API密钥、硬件设置、端点配置
- **环境模板**: 用于设置敏感信息的模板文件

### 🔄 工作流 (workflows/)
- **望远镜会话**: 完整的6步操作流程
- **硬件集成**: 真实硬件和模拟模式支持

### 🧪 测试套件 (tests/)
- **集成测试**: 验证ML API连接和功能
- **性能测试**: 评估系统响应时间

## 📋 使用说明

### 1. 环境准备
```bash
# 安装依赖
./scripts/install_dependencies.sh

# 配置API密钥
cp config/env_template.txt .env
# 编辑.env文件，填入你的API密钥
```

### 2. 运行程序
```bash
# 启动虚拟望远镜
./scripts/launch_telescope.sh
```

### 3. 操作界面
- **🔭 启动虚拟望远镜会话**: 运行完整工作流
- **🔧 硬件状态检查**: 检查树莓派硬件连接
- **⚙️ 配置检查**: 验证API密钥和配置
- **📜 查看最近结果**: 浏览历史生成结果
- **🧪 运行硬件测试**: 测试硬件交互功能

## 🛠️ 开发说明

### 修改配置
编辑 `config/config.json` 文件来调整：
- API端点地址
- 硬件参数设置
- 图像生成参数
- 调试选项

### 添加新功能
- **核心功能**: 在 `core/` 目录添加新模块
- **工作流步骤**: 修改 `workflows/telescope_workflow.py`
- **测试用例**: 在 `tests/` 目录添加测试文件

### 文件导入规则
由于重组了文件夹结构，导入路径已自动更新：
- 核心模块: `from core.module_name import ClassName`
- 工作流: `from workflows.telescope_workflow import WorkflowClass`
- 配置: 自动从 `config/config.json` 加载

## 🔗 相关文档
- 📖 [部署指南](docs/DEPLOYMENT_GUIDE.md)
- 🔗 [集成总结](docs/INTEGRATION_SUMMARY.md)
- 🌐 [网络优化](docs/NETWORK_OPTIMIZATION_GUIDE.md)
- ✅ [任务进度](docs/TASK_PROGRESS_CHECKLIST.md)

---

🌟 **Obscura No.7 虚拟望远镜** - 探索未来环境的艺术化可能性 