# 🧪 Obscura No.7 测试脚本使用指南

本文件夹包含了用于测试 Obscura No.7 虚拟望远镜工作流的测试脚本，特别是用于验证参数传递修复和Vision Description生成的测试。

## 📁 测试脚本概览

### 1. `test_keyboard_input_workflow.py` - 交互式键盘输入测试
**用途**: 允许您手动输入不同的距离、方向、时间参数来测试工作流

**特点**:
- ✅ 交互式参数输入
- ✅ 预设参数组合选择
- ✅ 坐标预览功能
- ✅ 详细的结果显示
- ✅ 测试结果保存

### 2. `test_batch_workflow.py` - 自动批量测试
**用途**: 自动运行多个预设参数组合，验证Vision Description的变化

**特点**:
- ✅ 8个预设测试案例
- ✅ 自动比较Vision Description差异
- ✅ 生成详细测试报告
- ✅ 性能统计分析

### 3. 现有测试脚本
- `test_exhibition_mode.py` - 展览模式功能测试
- `test_ml_api_integration.py` - ML API集成测试

## 🚀 使用方法

### 交互式测试

```bash
cd WorkFlow/RasberryPi_Workflow/raspberry_pi_deployment/tests
python test_keyboard_input_workflow.py
```

**运行流程**:
1. 选择预设参数或手动输入
2. 预览计算得到的坐标
3. 确认执行测试
4. 查看详细结果，包括Vision Description
5. 选择是否继续下一轮测试

**适用场景**:
- 🔧 开发调试时测试特定参数
- 🎯 验证修复效果
- 📊 查看单个测试的详细信息

### 批量自动测试

```bash
cd WorkFlow/RasberryPi_Workflow/raspberry_pi_deployment/tests
python test_batch_workflow.py
```

**运行流程**:
1. 自动运行8个测试案例
2. 每个测试之间等待3秒
3. 自动分析Vision Description差异
4. 生成测试报告和日志文件

**适用场景**:
- 🔍 验证参数传递修复是否成功
- 📈 批量验证不同参数的效果
- 📊 生成完整的测试报告

## 📋 预设测试案例

批量测试包含以下8个测试案例：

| 测试名称 | 距离(km) | 方向(°) | 时间偏移(年) | 预期区域 |
|---------|---------|---------|-------------|----------|
| 近距离北方 | 5.0 | 0° | 0 | 伦敦市中心北部 |
| 中距离东方 | 20.0 | 90° | 5 | 伦敦东部郊区 |
| 远距离南方 | 40.0 | 180° | 10 | 英格兰南部 |
| 中距离西方 | 30.0 | 270° | 15 | 伦敦西部 |
| 近距离东北 | 8.0 | 45° | 2 | 伦敦东北部 |
| 远距离西南 | 35.0 | 225° | 20 | 英格兰西南部 |
| 极近距离 | 2.0 | 315° | 0 | 伦敦市中心 |
| 极远距离 | 50.0 | 135° | 25 | 英格兰东南边界 |

## 📊 测试结果分析

### 期望的成功指标

1. **参数传递成功**:
   - 不同输入参数生成不同的目标坐标
   - 坐标计算正确反映距离和方向

2. **Vision Description差异化**:
   - 每个测试案例生成唯一的Vision Description
   - 描述中包含不同的地理位置和建筑信息

3. **工作流稳定性**:
   - 所有测试案例都能成功完成
   - 没有程序崩溃或API错误

### 故障排查

#### 如果所有Vision Description都相同：
- ❌ 参数传递可能仍有问题
- 🔧 检查 `telescope_workflow.py` 是否正确使用 `hardware_params`
- 🔧 检查 `main.py` 展览控制器是否正确传递参数

#### 如果测试频繁失败：
- 🌐 检查网络连接和API密钥配置
- 🔧 查看生成的日志文件获取详细错误信息
- ⏰ 检查API调用频率限制

## 📄 生成的文件

### 日志文件
- `test_results_YYYYMMDD_HHMMSS.log` - 交互式测试日志
- `batch_test_YYYYMMDD_HHMMSS.log` - 批量测试日志

### 报告文件
- `test_summary_YYYYMMDD_HHMMSS.json` - 交互式测试总结
- `batch_test_report_YYYYMMDD_HHMMSS.json` - 批量测试报告

## 🔧 配置要求

运行测试脚本需要：

1. **Python环境**: Python 3.7+
2. **依赖包**: 参见 `requirements.txt`
3. **API密钥**: 配置文件中的相关API密钥
4. **网络连接**: 用于调用外部API

## 💡 使用建议

### 首次测试建议流程：

1. **先运行交互式测试**:
   ```bash
   python test_keyboard_input_workflow.py
   ```
   - 测试1-2个参数组合确认基本功能

2. **再运行批量测试**:
   ```bash
   python test_batch_workflow.py
   ```
   - 验证修复效果和生成差异化描述

3. **分析测试报告**:
   - 检查Vision Description是否各不相同
   - 验证坐标计算是否正确

### 调试建议：

- 🔍 优先查看日志文件了解详细错误
- 📊 使用交互式测试定位具体问题
- 🔄 修改代码后重新运行批量测试验证

## 🎯 验证修复成功的标准

如果看到以下结果，说明参数传递修复成功：

✅ **坐标差异化**: 不同参数生成明显不同的经纬度坐标
✅ **描述差异化**: Vision Description中包含不同的地理位置名称  
✅ **逻辑正确性**: 北方向的坐标纬度更高，东方向的坐标经度更大
✅ **稳定性**: 所有测试案例都能成功完成

---

📞 **如有问题**: 请查看生成的日志文件或联系开发团队 