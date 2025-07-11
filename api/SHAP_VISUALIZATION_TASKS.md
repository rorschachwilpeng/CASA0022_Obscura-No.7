# SHAP可视化重构任务清单

**项目目标**: 简化图片详情页面，实现三模块设计：图片显示 + AI故事 + 圆形打包图可视化

## 📊 任务进度跟踪

### 阶段1: 页面结构重构
- [x] **Task 1.1**: 移除"📊 Temporal Data Analysis"模块
- [x] **Task 1.2**: 移除"🔬 Prediction Analysis"模块  
- [x] **Task 1.3**: 保留并优化图片显示模块
- [x] **Task 1.4**: 重新设计页面布局为三模块结构

### 阶段2: AI故事生成实现
- [x] **Task 2.1**: 分析当前故事数据结构（已发现在`api/routes/images.py`）
- [x] **Task 2.2**: 实现真实AI故事生成逻辑（替换模拟数据）
- [x] **Task 2.3**: 确保故事内容~100词英文，戏剧性描述SHAP结果
- [x] **Task 2.4**: 集成大模型API生成故事内容

### 阶段3: 圆形打包图可视化开发
- [x] **Task 3.1**: 创建新的圆形打包图JavaScript组件
- [x] **Task 3.2**: 将SHAP数据转换为层次化数据结构  
- [x] **Task 3.3**: 实现三个维度（气候、地理、经济）的数据映射
- [x] **Task 3.4**: 集成D3.js + ECharts渲染逻辑
- [x] **Task 3.5**: 实现交互功能（钻取、hover效果）
- [x] **Task 3.6**: 适配蒸汽朋克主题颜色方案

### 阶段4: 数据集成与API增强
- [x] **Task 4.1**: 增强`/api/v1/images/<id>/shap-analysis`端点
- [x] **Task 4.2**: 确保返回层次化的特征重要性数据
- [x] **Task 4.3**: 验证三个维度数据的完整性
- [x] **Task 4.4**: 优化数据传输格式

### 阶段5: 前后端集成
- [x] **Task 5.1**: 修改`image-detail.js`加载逻辑
- [x] **Task 5.2**: 移除现有bubble chart相关代码
- [x] **Task 5.3**: 集成新的圆形打包图组件
- [x] **Task 5.4**: 测试数据流从API到可视化

### 阶段6: 样式与用户体验
- [x] **Task 6.1**: 应用蒸汽朋克风格CSS
- [x] **Task 6.2**: 确保响应式布局
- [x] **Task 6.3**: 添加加载状态和错误处理
- [x] **Task 6.4**: 优化移动端显示效果

### 阶段7: 测试与部署
- [ ] **Task 7.1**: 单元测试AI故事生成
- [ ] **Task 7.2**: 集成测试可视化渲染
- [ ] **Task 7.3**: 跨浏览器兼容性测试
- [ ] **Task 7.4**: 性能优化和代码审查
- [ ] **Task 7.5**: 生产环境部署

## 🔧 技术实现细节

### 当前数据结构（已分析）
```javascript
// SHAP数据来源: /api/v1/images/<id>/shap-analysis
{
  "climate_score": 0.73,
  "geographic_score": 0.68, 
  "economic_score": 0.71,
  "final_score": 0.705,
  "shap_analysis": {
    "feature_importance": {
      "temperature": 0.18,
      "humidity": 0.15,
      "pressure": 0.12,
      "location_factor": 0.20,
      "seasonal_factor": 0.13,
      "climate_zone": 0.22
    }
  },
  "ai_story": { /* 需要增强 */ }
}
```

### 目标层次化数据结构
```javascript
// 转换为圆形打包图格式
{
  "final_score": { /* 根节点 */ },
  "climate": {
    "temperature": 0.18,
    "humidity": 0.15,
    "climate_zone": 0.22
  },
  "geographic": {
    "location_factor": 0.20,
    "pressure": 0.12
  },
  "economic": {
    "seasonal_factor": 0.13
    /* 需要添加更多经济维度特征 */
  }
}
```

## 📝 下一步行动
1. 从**Task 1.1**开始逐步执行
2. 每完成一个任务，在对应行添加 `[x]`
3. 遇到问题时在任务下方添加注释
4. 完成阶段后进行代码review

## ⚠️ 注意事项
- 保持向后兼容性，不影响现有功能
- 确保数据安全，避免泄露敏感信息  
- 优先移动端用户体验
- 遵循项目代码规范

---
**创建时间**: 2025-01-11  
**预计完成时间**: 2025-01-18  
**负责人**: 开发团队 