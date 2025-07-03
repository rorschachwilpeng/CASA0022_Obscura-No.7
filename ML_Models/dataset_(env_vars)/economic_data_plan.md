# 🏛️ 伦敦经济数据收集计划

## Phase 1: 立即可获取数据 (本周)

### 1.1 ONS官方数据
- **数据源**: https://www.ons.gov.uk/economy/grossdomesticproductgdp/datasets
- **获取内容**: London Regional GDP, GVA by sector
- **时间跨度**: 1997-2023
- **地理级别**: London Region + 32 Boroughs

### 1.2 London Datastore  
- **数据源**: https://data.london.gov.uk/dataset/london-borough-profiles
- **获取内容**: 
  - GDP per capita by borough
  - Employment rates
  - Business density
  - Average income
- **格式**: CSV/Excel直接下载

### 1.3 Eurostat数据
- **数据源**: https://ec.europa.eu/eurostat
- **获取内容**: NUTS2级别伦敦经济指标
- **时间跨度**: 2000-2023

## Phase 2: 中期扩展 (2-4周)

### 2.1 UK Data Service申请
- **目标数据集**: SN 8913 (LSOA级别GVA)
- **申请流程**: 
  1. 注册账户
  2. 准备research proposal
  3. 提交申请
  4. 等待审批

### 2.2 OECD Metropolitan数据
- **数据源**: OECD.Stat
- **获取内容**: London Metropolitan Area经济指标
- **优势**: 国际标准化数据

## Phase 3: 数据整合与处理

### 3.1 数据标准化
```python
# 经济指标标准化框架
london_economic_index = {
    'gdp_per_capita': normalize(gdp_data),
    'employment_rate': normalize(employment_data), 
    'business_density': normalize(business_data),
    'industrial_output': normalize(industry_data)
}
```

### 3.2 时间对齐
```python
# 将年度经济数据对齐到日度环境数据
economic_daily = interpolate_economic_to_daily(
    economic_annual_data,
    start_date='2022-01-01',
    end_date='2025-12-31'
)
```

## 推荐优先级

1. **立即开始**: London Datastore Borough Profiles
2. **本周完成**: ONS Regional GDP数据  
3. **并行进行**: UK Data Service申请
4. **后续扩展**: OECD国际数据

## 目标输出

- [ ] 32个伦敦行政区的经济指标数据
- [ ] 1997-2023年时间序列  
- [ ] 标准化的经济影响指数
- [ ] 与环境数据的时间对齐 