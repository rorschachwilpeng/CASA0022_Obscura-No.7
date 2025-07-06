# 🧠 智能数据管理系统 & 环境预测框架

## 概述

这个目录包含了为CASA0022 Obscura No.7项目开发的智能数据管理系统和环境预测变量框架。系统提供了全面的数据管理解决方案，支持多维度环境数据的收集、处理、分析和管理。

## 📁 目录结构

```
ML_Models/
├── 🌍 environmental_prediction_framework/     # 环境预测框架
│   ├── meteorological_climate_factors/       # 气象与气候因子
│   ├── human_activities_socioeconomic_factors/ # 人类活动与社会经济因子
│   └── geospatial_topographic_factors/       # 地理空间与地形因子
├── 🧠 intelligent_data_manager.py            # 智能数据管理器主程序
├── 📊 usage_example.py                       # 使用示例
├── 📋 requirements.txt                       # 依赖包列表
├── 🗂️ data_cache/                           # 数据缓存目录
├── 📈 metadata/                             # 元数据存储
└── 📝 README.md                             # 本文件
```

## 🎯 主要功能

### 1. 环境预测框架
- **三维度数据分类**：气象、社会经济、地理空间
- **标准化数据源**：每个数据类别都有详细的英文文档
- **数据源映射**：明确的数据来源和获取方式
- **环境意义说明**：每个变量的环境预测重要性

### 2. 智能数据管理器
- **自动数据下载**：支持多种数据格式（CSV、Excel、JSON、API）
- **缓存管理**：智能缓存策略，避免重复下载
- **数据质量检查**：自动分析数据质量，检测异常值
- **元数据管理**：完整的数据血缘和版本控制
- **自动调度**：支持定时数据更新和备份
- **多格式支持**：统一的数据加载接口

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行示例
```bash
python usage_example.py
```

### 3. 使用数据管理器
```python
from intelligent_data_manager import IntelligentDataManager

# 初始化
dm = IntelligentDataManager()

# 更新所有数据
dm.update_all_data()

# 按类别更新数据
dm.update_all_data(category='meteorological')

# 加载数据
df = dm.load_data('temperature_data')

# 生成报告
report = dm.generate_report()
print(report)
```

## 📊 环境预测框架结构

### 🌤️ 气象与气候因子
- **温度**：气温、地表水温、水柱温度
- **湿度**：相对湿度、绝对湿度
- **风速**：10米高度风速、风向
- **大气压力**：海平面气压、气压梯度
- **太阳辐射**：全球太阳辐射、直射辐射
- **降水**：强度、累积、持续时间、模式
- **海平面**：平均海平面、潮汐变化

### 🏙️ 人类活动与社会经济因子
- **土地利用/土地覆盖**：城市建设、农业、林业、水体
- **人口分布**：人口密度、年龄结构、人口预测
- **经济活动指标**：GDP、GVA、人均收入
- **铁路基础设施**：铁路密度、网络连通性
- **生活质量指标**：平均寿命、健康指标

### 🏔️ 地理空间与地形因子
- **水文网络**：河流密度、流域特征
- **地质与土壤**：土壤类型、土壤湿度、地质构造
- **植被与水体健康**：NDVI、NDWI、生态系统指标
- **城市洪水风险**：洪水易发区、排水能力

## 🔧 配置说明

### 数据源配置
系统会自动生成`data_config.json`配置文件，包含：
- 数据源URL和格式
- 更新频率设置
- API密钥配置
- 缓存策略配置

### 自定义数据源
可以通过修改配置文件添加新的数据源：
```json
{
  "name": "custom_data",
  "url": "https://your-data-source.com/api",
  "format": "csv",
  "update_frequency": "daily",
  "description": "Custom environmental data",
  "local_path": "custom_category/custom_data.csv",
  "category": "custom"
}
```

## 📈 数据质量管理

系统提供自动数据质量检查：
- **缺失值检测**：计算缺失值比例
- **重复记录检测**：识别重复数据
- **异常值检测**：使用IQR方法检测异常值
- **数据完整性验证**：验证数据格式和结构

## 🔄 自动调度功能

支持后台自动运行：
- **每日数据更新**：02:00自动更新所有数据源
- **每日备份**：01:00自动备份数据
- **每周清理**：自动清理过期缓存文件
- **故障恢复**：自动重试失败的下载任务

## 📚 文档说明

每个数据类别都包含详细的英文README文档，包括：
- 数据源介绍和链接
- 数据格式和特征说明
- 环境预测意义
- 数据处理建议
- 相关变量关系

## 🛠️ 开发指南

### 扩展新数据源
1. 在配置文件中添加数据源定义
2. 在相应框架目录中创建README文档
3. 测试数据下载和处理功能

### 自定义数据处理
```python
# 自定义数据处理函数
def custom_data_processor(df):
    # 数据清洗和转换
    processed_df = df.dropna()
    return processed_df

# 使用自定义处理器
dm = IntelligentDataManager()
df = dm.load_data('your_data_source')
processed_df = custom_data_processor(df)
```

## 🔍 故障排除

### 常见问题
1. **API密钥错误**：检查配置文件中的API密钥设置
2. **网络连接问题**：检查网络连接和代理设置
3. **磁盘空间不足**：运行缓存清理或增加存储空间
4. **数据格式错误**：检查数据源格式设置

### 日志查看
系统会自动生成日志文件：
```bash
tail -f ML_Models/data_manager.log
```

## 🤝 贡献指南

1. 遵循现有的代码风格和文档格式
2. 添加新功能前先创建issue讨论
3. 提供完整的测试用例
4. 更新相关文档

## 📄 许可证

本项目为CASA0022 Obscura No.7项目的一部分，遵循项目整体的许可证协议。

## 🙏 致谢

感谢所有数据源提供方：
- UK Met Office Climate Data Portal
- Open-Meteo Historical Weather API
- London Datastore
- ONS (Office for National Statistics)

---

*最后更新：2025年7月*  
*项目：CASA0022 Obscura No.7 环境预测系统* 