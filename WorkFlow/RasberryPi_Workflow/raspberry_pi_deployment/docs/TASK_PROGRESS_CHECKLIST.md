# 🔭 Obscura No.7 展厅模式开发任务清单

## 📊 项目概述
**目标**: 将开发测试版本升级为展厅展示版本
**关键需求**: 持续运行、英文界面、统一写实画风、触屏交互

---

## 📋 阶段一：数据基础设施重构
**目标**: 完成从OpenWeather → Open-Meteo的API迁移

### 1.1 创建Open-Meteo数据客户端 🔴 最高优先级
- [x] 创建 `core/open_meteo_client.py` 文件
- [x] 集成 Historical Weather API 
- [x] 集成 Flood API (river_discharge_max)
- [x] 实现气象气候因子数据抓取：
  - [x] `temperature_2m` (温度)
  - [x] `relative_humidity_2m` (湿度)
  - [x] `wind_speed_10m` (风速)
  - [x] `surface_pressure` (大气压)
  - [x] `shortwave_radiation` (太阳辐射)
  - [x] `precipitation` (降雨量)
  - [x] `sealevel_pressure` (SeaLevel)
  - [ ] ❓ NO2 (空气质量，需要额外Air Quality API)
- [x] 实现地理空间因子数据抓取：
  - [x] `et0_fao_evapotranspiration` (水文网络)
  - [x] `soil_temperature_0_7cm` (地质土壤)
  - [x] `soil_moisture_7_28cm` (植被水体健康)
  - [x] `river_discharge_max` (城市洪水风险)

### 1.2 数据映射验证 🔴 最高优先级
- [x] 验证所有14个数据字段能成功抓取
- [x] 确保数据格式与 `environmental_prediction_framework` 匹配
- [x] 验证数据格式与云端SHAP模型兼容
- [x] 实现数据标准化处理
- [x] **错误处理**: 实现降级机制（标注为模拟数据备用）

### 1.3 替换现有调用 🟡 高优先级
- [x] 更新 `obscura_workflow.py` 中的weather_client引用
- [x] 更新 `telescope_workflow.py` 中的相关调用
- [x] 确保向后兼容性
- [x] 测试数据抓取功能正常工作

---

## 📋 阶段二：Prompt系统完善
**目标**: 确保统一写实画风

### 2.1 修复CloudAPIClient集成 🟡 高优先级
- [x] ✅ 已完成：升级 `core/image_prompt_builder.py` 统一写实风格
- [x] 更新 `core/cloud_api_client.py` 中的 `_build_art_prompt` 方法
- [x] 确保调用升级后的 `ImagePromptBuilder` 类
- [x] 验证所有生成图像都使用统一写实风格
- [x] 测试prompt生成功能

### 2.2 英文化输出 🟡 高优先级
- [x] 更新 `core/progress_display.py` 所有中文输出为英文
- [x] 更新 `core/obscura_workflow.py` 用户界面文本
- [x] 更新 `workflows/telescope_workflow.py` 状态提示信息
- [x] 更新 `main.py` 菜单和提示文本
- [x] 更新 `tests/test_ml_api_integration.py` 测试输出为英文
- [x] 更新所有错误信息为英文
- [x] 验证所有用户可见文本都是英文

---

## 📋 阶段三：展厅模式架构重构
**目标**: 从单次执行改为持续运行

### 3.1 状态机设计 🟡 高优先级
- [x] 设计状态机架构：
  ```
  🎮 参数输入状态 → ⚡ 数据抓取确认 → 🔄 处理中状态 → 
  🖼️ 结果展示状态 → 👆 等待交互状态 → 🔄 重置状态
  ```
- [x] 创建 `core/exhibition_state_machine.py`
- [x] 实现状态切换逻辑
- [x] 实现状态持久化（如需要）

### 3.2 Pygame界面开发 🟠 中优先级
- [x] 安装和配置Pygame用于HyperPixel 4.0 (800x480)
- [x] 创建 `core/pygame_interface.py`
- [x] 实现参数可视化显示：
  - [x] 距离显示（1-50km范围）
  - [x] 角度显示（0-360度，16方位）
  - [x] 时间偏移显示（年份）
- [x] 实现数据抓取触发按钮（替代Time Encoder）
- [x] 实现生成图像的全屏显示
- [x] 实现"Touch to continue"交互界面
- [x] 实现触屏事件处理

### 3.3 持续运行循环 🟠 中优先级
- [x] 重构 `main.py` 为无限循环模式
- [x] 实现展厅模式启动选项
- [x] 集成状态机和Pygame界面
- [x] 实现资源管理和内存优化
- [x] 实现异常恢复机制
- [x] 添加日志记录功能

### 3.4 用户交互流程 🟠 中优先级
- [x] 实现硬件输入处理（距离、角度编码器）
- [x] 实现按钮点击数据抓取确认
- [x] 实现处理中状态的进度显示
- [x] 实现结果展示界面
- [x] 实现触屏继续/重置功能
- [x] 实现超时自动重置（可选）

---

## 📋 阶段四：系统集成与测试
**目标**: 端到端功能验证

### 4.1 数据流测试 🟢 低优先级
- [x] 测试 Open-Meteo数据抓取端到端
- [x] 测试 数据 → 云端API → SHAP预测 流程
- [ ] 测试 SHAP预测 → 图像生成 流程
- [ ] 验证完整工作流程性能
- [x] 测试错误处理和降级机制

### 4.2 展厅模式测试 🟢 低优先级
- [ ] 用户交互流程完整测试
- [ ] 长时间运行稳定性测试（2-4小时）
- [ ] 内存泄漏检查
- [ ] 异常情况处理验证
- [ ] 触屏响应性能测试

### 4.3 最终优化 🟢 低优先级
- [ ] 性能优化和代码清理
- [ ] 用户体验微调
- [ ] 更新文档和部署指南
- [ ] 创建展厅操作手册
- [ ] 最终验收测试

---

## 🚀 里程碑检查点

### Milestone 1: 数据基础设施完成
- [x] Open-Meteo API成功抓取所有14个数据字段
- [x] 数据格式与云端SHAP模型兼容
- [x] 错误处理机制已实现并标注

### Milestone 2: 界面系统完成
- [x] 所有输出已英文化 (全面完成)
- [x] 统一写实画风已验证
- [x] Pygame界面基本功能运行

### Milestone 3: 展厅模式完成 ✅
- [x] 持续运行循环正常工作
- [x] 用户交互流程完整
- [x] 触屏功能正常响应

### Milestone 4: 系统就绪
- [ ] 端到端功能验证通过
- [ ] 长时间运行稳定
- [ ] 展厅部署就绪

---

## 📝 开发备注

### 技术栈确认
- ✅ GUI框架: Pygame（HyperPixel 4.0, 800x480）
- ✅ 数据源: Open-Meteo APIs (Historical Weather + Flood)
- ✅ 画风: 统一写实摄影风格
- ✅ 语言: 全英文界面

### 特殊注意事项
- 🚨 **错误处理**: 所有降级机制需要明确标注
- 🚨 **资源管理**: 长时间运行需要防内存泄漏
- 🚨 **用户体验**: 触屏响应需要快速流畅
- 🚨 **数据完整性**: 确保14个环境因子数据完整性

### API信息
- **Historical Weather**: https://open-meteo.com/en/docs/historical-weather-api
- **Flood API**: https://open-meteo.com/en/docs/flood-api
- **云端SHAP API**: http://127.0.0.1:8080 (✅ 已验证运行中，测试通过)

### 🍓 树莓派部署指令
**快速传输整个项目到树莓派**:
```bash
# 从项目根目录执行 - 传输整个raspberry_pi_deployment文件夹
scp -r ./WorkFlow/RasberryPi_Workflow/raspberry_pi_deployment youtianpeng@obscuraNo7-RPi:/home/youtianpeng/Desktop/

# 从raspberry_pi_deployment目录执行 - 传输当前目录所有文件
scp -r ./* youtianpeng@obscuraNo7-RPi:/home/youtianpeng/Desktop/raspberry_pi_deployment/

# 传输单个文件（用于快速更新）
scp ./core/open_meteo_client.py youtianpeng@obscuraNo7-RPi:/home/youtianpeng/Desktop/raspberry_pi_deployment/core/

# 传输core文件夹全部内容
scp -r ./core/* youtianpeng@obscuraNo7-RPi:/home/youtianpeng/Desktop/raspberry_pi_deployment/core/
```

**树莓派上运行测试**:
```bash
# SSH连接到树莓派
ssh youtianpeng@obscuraNo7-RPi

# 进入项目目录
cd /home/youtianpeng/Desktop/raspberry_pi_deployment

# 或者使用简化路径
cd ~/Desktop/raspberry_pi_deployment

# 运行主程序
python3 main_telescope.py

# 运行测试
python3 -m pytest test_*.py
```

---

## 📊 项目进度统计
**总任务数**: 约60个子任务  
**已完成**: 51/60 ✅  
**进行中**: 0/60 🟡  
**待开始**: 9/60 ⭕  

**进度**: 85% 完成  
**阶段**: 🎉 阶段一+二+三全面完成！  
**预估完成时间**: 1-2天  
**开始日期**: 2025-01-09  
**目标完成**: 2025-01-12

---

*最后更新: 2025-01-10*  
*状态: ✅ 阶段三展厅模式架构重构全面完成！状态机、Pygame界面、持续运行循环和用户交互流程全部实现，接下来进入阶段四：系统集成与测试* 