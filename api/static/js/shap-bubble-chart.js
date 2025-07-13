/**
 * SHAP Hierarchical Bubble Chart Visualization
 * 基于SHAP分析结果生成分层泡泡图可视化 - Focus Drill-down Mode
 */

console.log('🚀 Loading SHAP Bubble Chart - Focus Drill-down Mode');

class SHAPBubbleChart {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // 响应式尺寸设置
        const containerRect = this.container ? this.container.getBoundingClientRect() : { width: 800, height: 600 };
        const isMobile = window.innerWidth < 768;
        
        this.width = options.width || Math.min(containerRect.width || 800, isMobile ? 350 : 800);
        this.height = options.height || Math.min(containerRect.height || 600, isMobile ? 350 : 600);
        this.margin = options.margin || { top: 60, right: 20, bottom: 20, left: 20 };
        
        // 蒸汽朋克风格配色
        this.colors = {
            climate: '#D2691E',     // 巧克力橙色 - 气候/温度
            geographic: '#5F8A8B',  // 钢青色 - 地理/自然
            economic: '#DAA520',    // 金棒色 - 经济/金融
            root: '#8B7355',        // 中性棕色 - 根节点
            positive: '#4CAF50',    // 绿色 - 正向影响
            negative: '#DC143C',    // 深红色 - 负向影响
            focus: '#FF6B6B',       // 聚焦边框颜色
            breadcrumb: '#DAA520'   // 面包屑导航颜色
        };
        
        this.chart = null;
        this.rawData = null;
        this.processedData = null;
        this.displayRoot = null;
        
        // 聚焦状态管理
        this.focusState = {
            isActive: false,        // 是否处于聚焦状态
            focusedDimension: null, // 当前聚焦的维度
            focusedPath: null,      // 当前聚焦的路径
            globalView: true        // 是否显示全局视图
        };
        
        // 交互状态管理
        this.expandedNodes = new Set([
            'Environmental Impact',                    // 根节点
            'Environmental Impact.Climate',           // 气候维度
            'Environmental Impact.Geographic',        // 地理维度  
            'Environmental Impact.Economic'           // 经济维度
        ]);  // 默认展开根节点和三个子维度
        this.currentDepthLevel = 2;  // 当前显示的深度级别
        this.maxDepth = 2;  // 最大深度
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Container #${this.containerId} not found`);
            return;
        }
        
        // 检查ECharts是否可用
        if (typeof echarts === 'undefined') {
            console.error('ECharts library not loaded');
            return;
        }
        
        // 初始化ECharts实例
        this.chart = echarts.init(this.container, 'dark');
        
        // 设置容器样式
        this.container.style.width = this.width + 'px';
        this.container.style.height = this.height + 'px';
        this.container.style.background = 'linear-gradient(45deg, #1a1a2e 0%, #16213e 100%)';
        this.container.style.borderRadius = '10px';
        this.container.style.border = '2px solid #CD853F';
        this.container.style.position = 'relative';
        
        // 创建面包屑导航
        this.createBreadcrumb();
        
        // 添加键盘事件监听
        this.addKeyboardListeners();
        
        // 添加点击空白区域监听
        this.addClickOutsideListener();
        
        // 添加窗口大小改变监听器
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
        
        console.log('🎯 SHAP Hierarchical Bubble Chart initialized - Focus Drill-down Mode');
    }

    /**
     * 创建面包屑导航
     */
    createBreadcrumb() {
        const breadcrumbContainer = document.createElement('div');
        breadcrumbContainer.id = 'shap-breadcrumb';
        breadcrumbContainer.style.cssText = `
            position: absolute;
            top: 10px;
            left: 20px;
            right: 20px;
            height: 30px;
            display: flex;
            align-items: center;
            font-family: "Crimson Text", "Times New Roman", serif;
            font-size: 14px;
            color: ${this.colors.breadcrumb};
            z-index: 10;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        this.container.appendChild(breadcrumbContainer);
        this.breadcrumbContainer = breadcrumbContainer;
    }

    /**
     * 更新面包屑导航
     */
    updateBreadcrumb() {
        if (!this.breadcrumbContainer) return;
        
        if (this.focusState.isActive && this.focusState.focusedDimension) {
            const breadcrumbText = `🏠 Global View → ${this.focusState.focusedDimension} (聚焦模式)`;
            this.breadcrumbContainer.innerHTML = `
                <span style="cursor: pointer; text-decoration: underline; pointer-events: auto;" 
                      onclick="window.shapBubbleChart.exitFocusMode()">
                    ${breadcrumbText}
                </span>
                <span style="margin-left: 10px; color: #999; font-size: 12px;">
                    按 ESC 或点击空白处返回
                </span>
            `;
            this.breadcrumbContainer.style.opacity = '1';
        } else {
            this.breadcrumbContainer.style.opacity = '0';
        }
    }

    /**
     * 添加键盘事件监听
     */
    addKeyboardListeners() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.focusState.isActive) {
                this.exitFocusMode();
            }
        });
    }

    /**
     * 添加点击空白区域监听
     */
    addClickOutsideListener() {
        this.chart.on('click', (params) => {
            // 如果点击的不是图表元素，且处于聚焦状态，则退出聚焦
            if (!params.data && this.focusState.isActive) {
                this.exitFocusMode();
            }
        });
    }

    /**
     * 进入聚焦模式
     */
    enterFocusMode(dimensionPath, dimensionName) {
        console.log('🔍 Entering focus mode for:', dimensionPath, dimensionName);
        
        this.focusState.isActive = true;
        this.focusState.focusedDimension = dimensionName;
        this.focusState.focusedPath = dimensionPath;
        this.focusState.globalView = false;
        
        // 更新展开状态：只显示聚焦的维度及其子特征
        this.expandedNodes.clear();
        this.expandedNodes.add('Environmental Impact');
        this.expandedNodes.add(dimensionPath);
        
        // 更新面包屑导航
        this.updateBreadcrumb();
        
        // 更新容器边框以显示聚焦状态
        this.container.style.border = `3px solid ${this.colors.focus}`;
        this.container.style.boxShadow = `0 0 20px ${this.colors.focus}40`;
        
        // 重新渲染图表
        this.refreshChart();
    }

    /**
     * 退出聚焦模式
     */
    exitFocusMode() {
        console.log('🔙 Exiting focus mode');
        
        this.focusState.isActive = false;
        this.focusState.focusedDimension = null;
        this.focusState.focusedPath = null;
        this.focusState.globalView = true;
        
        // 恢复全局视图展开状态
        this.expandedNodes.clear();
        this.expandedNodes.add('Environmental Impact');
        this.expandedNodes.add('Environmental Impact.Climate');
        this.expandedNodes.add('Environmental Impact.Geographic');
        this.expandedNodes.add('Environmental Impact.Economic');
        
        // 更新面包屑导航
        this.updateBreadcrumb();
        
        // 恢复容器边框
        this.container.style.border = '2px solid #CD853F';
        this.container.style.boxShadow = 'none';
        
        // 重新渲染图表
        this.refreshChart();
    }

    /**
     * 渲染SHAP数据为分层泡泡图
     */
    render(shapData) {
        if (!this.chart || !shapData) {
            console.error('Chart or SHAP data not available');
            return;
        }

        try {
            // 保存原始数据供后续刷新使用
            this.rawData = shapData;
            
            // 准备数据
            const seriesData = this.prepareHierarchicalData(shapData);
            this.processedData = this.processSeriesData(seriesData);
            
            // 初始化图表
            this.initChart(this.processedData.seriesData, this.processedData.maxDepth);
            
            console.log('✅ SHAP Hierarchical Bubble Chart rendered successfully');
            
        } catch (error) {
            console.error('❌ Error rendering SHAP bubble chart:', error);
        }
    }

    /**
     * 准备层次化数据 - 基于SHAP分析结果
     */
    prepareHierarchicalData(shapData) {
        console.log('📊 Preparing hierarchical data:', shapData);
        
        // 计算总权重（用于根节点大小）
        const totalWeight = (shapData.climate_score || 0) + 
                          (shapData.geographic_score || 0) + 
                          (shapData.economic_score || 0);
        
        // 构建分层数据结构
        const hierarchicalData = [
            {
                name: 'Environmental Impact',
                value: Math.max(totalWeight * 100, 50), // 确保根节点有合理大小
                path: 'root',
                children: [
                    {
                        name: 'Climate',
                        value: Math.max((shapData.climate_score || 0) * 100, 20),
                        path: 'root.climate',
                        children: this.prepareFeatureData(shapData.hierarchical_features?.climate || {}, 'climate')
                    },
                    {
                        name: 'Geographic',
                        value: Math.max((shapData.geographic_score || 0) * 100, 20),
                        path: 'root.geographic',
                        children: this.prepareFeatureData(shapData.hierarchical_features?.geographic || {}, 'geographic')
                    },
                    {
                        name: 'Economic',
                        value: Math.max((shapData.economic_score || 0) * 100, 20),
                        path: 'root.economic',
                        children: this.prepareFeatureData(shapData.hierarchical_features?.economic || {}, 'economic')
                    }
                ]
            }
        ];
        
        console.log('📋 Prepared hierarchical data:', hierarchicalData);
        return hierarchicalData;
    }
    
    /**
     * 准备特征数据
     */
    prepareFeatureData(featuresData, dimension) {
        const features = [];
        
        for (const [featureName, featureValue] of Object.entries(featuresData)) {
            if (featureValue && typeof featureValue === 'number') {
                features.push({
                    name: featureName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    value: Math.max(Math.abs(featureValue) * 50, 8), // 确保特征有可见大小
                    path: `root.${dimension}.${featureName}`,
                    impact: featureValue > 0 ? 'positive' : 'negative',
                    originalValue: featureValue
                });
            }
        }
        
        return features;
    }

    /**
     * 处理序列数据
     */
    processSeriesData(rawData) {
        const self = this;
        const seriesData = [];
        
        function convert(source, basePath, depth) {
            for (let i = 0; i < source.length; i++) {
                const item = source[i];
                const currentPath = basePath ? `${basePath}.${item.name}` : item.name;
                
                seriesData.push({
                    id: currentPath,
                    name: item.name,
                    value: item.value,
                    depth: depth,
                    path: item.path || currentPath,
                    impact: item.impact || 'neutral',
                    originalValue: item.originalValue || item.value,
                    index: seriesData.length  // 添加索引
                });
                
                if (item.children && item.children.length > 0) {
                    convert(item.children, currentPath, depth + 1);
                }
            }
        }
        
        convert(rawData, null, 0);
        
        // 根据聚焦状态和展开状态过滤数据
        const filteredSeriesData = seriesData.filter(item => {
            // 根节点总是显示
            if (item.depth === 0) {
                return true;
            }
            
            // 如果处于聚焦状态，只显示聚焦的维度及其子特征
            if (this.focusState.isActive && this.focusState.focusedPath) {
                const focusedPath = this.focusState.focusedPath;
                
                // 第一级子节点：只显示聚焦的维度
                if (item.depth === 1) {
                    return item.id === focusedPath;
                }
                
                // 第二级子节点：只显示聚焦维度的子特征
                if (item.depth === 2) {
                    return item.id.startsWith(focusedPath + '.');
                }
                
                return false;
            }
            
            // 全局视图：根据展开状态过滤
            if (item.depth === 1) {
                return true;
            }
            
            if (item.depth === 2) {
                const parentId = item.id.substring(0, item.id.lastIndexOf('.'));
                const shouldShow = this.expandedNodes.has(parentId);
                console.log(`🔍 Checking depth 2 node: ${item.id}, parent: ${parentId}, expanded: ${shouldShow}`);
                return shouldShow;
            }
            
            return false;
        });
        
        console.log('📊 Processed series data:', filteredSeriesData);
        console.log('🔍 Expanded nodes:', Array.from(this.expandedNodes));
        console.log('🎯 Focus state:', this.focusState);
        
        const maxDepth = Math.max(...filteredSeriesData.map(item => item.depth));
        console.log('📏 Max depth:', maxDepth);
        
        return {
            seriesData: filteredSeriesData,
            maxDepth: maxDepth
        };
    }

    /**
     * 初始化图表
     */
    initChart(seriesData, maxDepth) {
        const self = this;
        
        console.log('🔧 InitChart called with:', {
            seriesData: seriesData,
            maxDepth: maxDepth,
            seriesDataLength: seriesData.length,
            focusState: this.focusState
        });
        
        // 添加调试信息
        console.log('📋 Sample seriesData item:', seriesData[0]);
        console.log('📋 All seriesData ids:', seriesData.map(item => item.id));
        
        function overallLayout(params, api) {
            const context = params.context;
            context.nodes = {};
            
            // 布局常量 - 根据聚焦状态调整
            const titleHeight = 60;  // 标题和面包屑区域高度
            const availableHeight = self.height - titleHeight - self.margin.top - self.margin.bottom;
            const availableWidth = self.width - self.margin.left - self.margin.right;
            
            // 创建层次结构
            console.log('🌳 Creating hierarchy from seriesData:', seriesData);
            const stratify = self.stratify(seriesData);
            console.log('🌳 Stratify function created:', stratify);
            
            const root = stratify.sum(function (d) {
                // 在聚焦模式下，给聚焦的维度更大的权重
                if (self.focusState.isActive && d.depth === 1) {
                    return d.value * 2; // 聚焦维度的泡泡更大
                }
                return d.value;
            });
            console.log('🌳 Root hierarchy created:', root);
            
            // 计算圆形打包布局 - 根据聚焦状态调整内边距
            const layout = d3.pack()
                .size([availableWidth, availableHeight])
                .padding(function(d) {
                    // 聚焦模式下使用更大的内边距突出聚焦维度
                    if (self.focusState.isActive) {
                        return d.depth === 0 ? 25 : d.depth === 1 ? 15 : 6;
                    }
                    return d.depth === 0 ? 15 : d.depth === 1 ? 10 : 4;
                });
            
            console.log('📏 Layout size:', availableWidth, 'x', availableHeight, 'Title height:', titleHeight);
            layout(root);
            console.log('🔄 Layout applied, root position:', root.x, root.y, root.r);
            console.log('🔄 Root children count:', root.children ? root.children.length : 0);
            
            // 调整位置到中心 - 考虑标题高度和边距
            const centerX = self.width / 2;
            const centerY = titleHeight + (self.height - titleHeight) / 2;
            
            root.descendants().forEach(node => {
                node.x = node.x - root.x + centerX;
                node.y = node.y - root.y + centerY;
                context.nodes[node.data.id] = node;
                console.log('📍 Node positioned:', node.data.id, 'x:', node.x, 'y:', node.y, 'r:', node.r);
            });
        }

        function renderItem(params, api) {
            const context = params.context;
            
            console.log('🎨 RenderItem called with params:', {
                dataIndex: params.dataIndex,
                dataIndexInside: params.dataIndexInside,
                hasData: !!params.data,
                data: params.data,
                seriesIndex: params.seriesIndex,
                actionType: params.actionType
            });
            
            // 只在每次setOption时执行一次布局
            if (!context.layout) {
                context.layout = true;
                overallLayout(params, api);
            }

            // 直接从 params.data 获取数据，添加安全检查
            const data = params.data;
            if (!data) {
                console.log('❌ params.data is undefined, trying to get data from API');
                // 尝试从 API 获取数据
                const dataIndex = params.dataIndex;
                console.log('🔍 DataIndex:', dataIndex, 'trying api.value at index:', dataIndex);
                
                // 如果 params.data 不存在，尝试从 seriesData 中获取
                if (dataIndex < seriesData.length) {
                    const fallbackData = seriesData[dataIndex];
                    console.log('🔄 Using fallback data:', fallbackData);
                    return renderNodeWithData(fallbackData, context, api);
                }
                
                return null;
            }
            
            return renderNodeWithData(data, context, api);
        }
        
        function renderNodeWithData(data, context, api) {
            const nodePath = data.id;
            console.log('🎯 Node path:', nodePath, 'Node data:', {
                id: data.id,
                name: data.name,
                depth: data.depth,
                value: data.value,
                originalValue: data.originalValue
            });
            
            const node = context.nodes[nodePath];
            console.log('🔍 Found node:', node ? 'YES' : 'NO', node ? `x:${node.x} y:${node.y} r:${node.r}` : 'undefined');
            
            if (!node) {
                console.log('❌ Node not found for path:', nodePath);
                return null;
            }

            const isLeaf = !node.children || !node.children.length;
            const focus = new Uint32Array(
                node.descendants().map(function (node) {
                    return node.data.index;
                })
            );

            // 获取节点名称和颜色
            const nodeName = self.getNodeDisplayName(nodePath, isLeaf);
            const nodeColor = self.getNodeColor(nodePath, node.depth);
            const z2 = (data.depth || 0) * 2;
            
            // 根据深度计算透明度 - 最底层透明度最高
            const textOpacity = self.getTextOpacity(node.depth, maxDepth);
            
            // 根据节点深度和屏幕尺寸调整字体大小
            const width = api.getWidth();
            const isMobile = width < 768;
            
            // 聚焦模式下调整字体大小
            const focusMultiplier = self.focusState.isActive ? 1.2 : 1;
            
            const baseFontSize = node.depth === 0 ? 
                Math.max(node.r / 8, isMobile ? 8 : 10) * focusMultiplier :
                node.depth === 1 ? 
                    Math.max(node.r / 6, isMobile ? 10 : 12) * focusMultiplier :
                    Math.max(node.r / 5, 8) * focusMultiplier;
            
            const emphasisFontSize = Math.max(baseFontSize * 1.2, 10);

            // 聚焦模式下的特殊样式
            const isFocused = self.focusState.isActive && node.depth === 1;
            const strokeWidth = isFocused ? 3 : (isLeaf ? 1 : 2);
            const strokeColor = isFocused ? self.colors.focus : '#FDF5E6';

            const baseObject = {
                type: 'circle',
                focus: focus,
                shape: {
                    cx: node.x,
                    cy: node.y,
                    r: node.r
                },
                transition: ['shape'],
                z2: z2,
                style: {
                    fill: nodeColor,
                    stroke: strokeColor,
                    strokeWidth: strokeWidth,
                    opacity: 0.8
                },
                emphasis: {
                    style: {
                        shadowBlur: isFocused ? 12 : 8,
                        shadowOffsetX: 2,
                        shadowOffsetY: 3,
                        shadowColor: isFocused ? `${self.colors.focus}60` : 'rgba(0,0,0,0.3)',
                        opacity: 0.95,
                        strokeWidth: strokeWidth + 1,
                        fill: self.getHoverColor(nodeColor)
                    }
                }
            };

            // 为所有节点添加文字内容，根据深度设置透明度和颜色
            const textColor = node.depth === 2 ? '#1a1a2e' : '#FDF5E6';
            const textShadow = node.depth === 2 ? '1px 1px 2px rgba(255,255,255,0.6)' : '1px 1px 2px rgba(0,0,0,0.8)';
            
            baseObject.textContent = {
                type: 'text',
                style: {
                    text: nodeName,
                    fontFamily: '"Crimson Text", "Times New Roman", serif',
                    width: node.r * 1.5,
                    overflow: 'truncate',
                    fontSize: baseFontSize,
                    fill: textColor,
                    textShadow: textShadow,
                    opacity: textOpacity,
                    fontWeight: isFocused ? 'bold' : 'normal'
                },
                emphasis: {
                    style: {
                        overflow: null,
                        fontSize: emphasisFontSize,
                        fontWeight: 'bold',
                        fill: textColor,
                        opacity: Math.min(textOpacity * 1.2, 1)
                    }
                }
            };
            baseObject.textConfig = {
                position: 'inside'
            };

            // 添加点击事件处理
            baseObject.onclick = function() {
                console.log('🖱️ Node clicked:', nodePath, 'depth:', node.depth);
                self.handleNodeClick(nodePath, node.depth, data.name);
            };
            
            console.log('🎨 Returning baseObject for node:', nodePath, baseObject);
            return baseObject;
        }

        // ECharts配置选项
        const option = {
            title: {
                text: this.focusState.isActive ? 
                    `Environmental Impact Analysis - ${this.focusState.focusedDimension} Focus` : 
                    'Environmental Impact Analysis',
                left: 'center',
                top: 35,
                textStyle: {
                    color: this.focusState.isActive ? this.colors.focus : '#DAA520',
                    fontSize: 18,
                    fontWeight: 'bold',
                    fontFamily: '"Crimson Text", "Times New Roman", serif'
                }
            },
            xAxis: {
                show: false,
                type: 'value'
            },
            yAxis: {
                show: false,
                type: 'value'
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    const data = params.data;
                    const impact = data.impact || 'neutral';
                    const value = data.originalValue || data.value;
                    
                    return `
                        <div style="padding: 8px; font-family: 'Crimson Text', serif;">
                            <div style="font-weight: bold; color: #DAA520; margin-bottom: 4px;">
                                ${data.name}
                            </div>
                            <div style="color: #FDF5E6; font-size: 12px;">
                                Value: ${typeof value === 'number' ? value.toFixed(3) : value}<br/>
                                Impact: ${impact}<br/>
                                Depth: ${data.depth}
                                ${self.focusState.isActive && data.depth === 2 ? '<br/>💡 点击保持聚焦' : ''}
                                ${!self.focusState.isActive && data.depth === 1 ? '<br/>💡 点击进入聚焦模式' : ''}
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                borderColor: this.focusState.isActive ? this.colors.focus : '#CD853F',
                borderWidth: 1,
                textStyle: {
                    color: '#FDF5E6'
                }
            },
            series: [
                {
                    type: 'custom',
                    renderItem: renderItem,
                    data: seriesData.map((item, index) => {
                        // 为每个数据点返回完整的对象
                        return {
                            value: item.value,  // 主要数值
                            id: item.id,
                            name: item.name,
                            depth: item.depth,
                            path: item.path,
                            impact: item.impact,
                            originalValue: item.originalValue,
                            index: item.index,
                            // 添加调试信息
                            dataIndex: index
                        };
                    }),
                    itemStyle: {
                        opacity: 0.8
                    },
                    emphasis: {
                        itemStyle: {
                            opacity: 1
                        }
                    }
                }
            ]
        };

        this.chart.setOption(option);
    }

    /**
     * 处理节点点击事件
     */
    handleNodeClick(nodePath, depth, nodeName) {
        console.log('🖱️ Handling node click:', nodePath, 'depth:', depth, 'name:', nodeName);
        
        if (depth === 0) {
            // 根节点点击：退出聚焦模式或什么都不做
            if (this.focusState.isActive) {
                this.exitFocusMode();
            }
            return;
        }
        
        if (depth === 1) {
            // 维度节点点击
            if (this.focusState.isActive) {
                // 如果已经在聚焦模式，且点击的是同一维度，则退出聚焦
                if (this.focusState.focusedPath === nodePath) {
                    this.exitFocusMode();
                } else {
                    // 切换到新的聚焦维度
                    this.enterFocusMode(nodePath, nodeName);
                }
            } else {
                // 进入聚焦模式
                this.enterFocusMode(nodePath, nodeName);
            }
            return;
        }
        
        if (depth === 2) {
            // 子特征点击
            if (this.focusState.isActive) {
                // 在聚焦状态下，点击子特征保持聚焦状态，可以显示详细信息
                console.log('🔍 Sub-feature clicked in focus mode:', nodeName);
                // 这里可以添加显示详细信息的逻辑
            } else {
                // 在全局视图中，点击子特征可能触发其他操作
                console.log('🔍 Sub-feature clicked in global view:', nodeName);
            }
            return;
        }
    }

    /**
     * 根据深度计算文字透明度
     */
    getTextOpacity(depth, maxDepth) {
        // 最底层(depth最大)透明度最高(1.0)，依次向上递减
        // 使用线性插值计算透明度
        const minOpacity = 0.3;  // 最小透明度(根节点)
        const maxOpacity = 1.0;  // 最大透明度(最底层)
        
        if (maxDepth === 0) return maxOpacity;
        
        // 计算透明度：深度越大，透明度越高
        const opacity = minOpacity + (maxOpacity - minOpacity) * (depth / maxDepth);
        
        console.log(`🎨 Node depth ${depth}/${maxDepth}, opacity: ${opacity.toFixed(2)}`);
        
        return opacity;
    }

    /**
     * 检查节点是否应该显示
     * @param {Object} node - D3 层次结构节点
     * @param {Object} data - 节点数据
     * @returns {boolean} 是否应该显示
     */
    shouldShowNode(node, data) {
        // 根节点总是显示
        if (node.depth === 0) {
            return true;
        }
        
        // 检查父节点是否被展开
        if (node.parent) {
            return this.expandedNodes.has(node.parent.data.id);
        }
        
        return false;
    }

    /**
     * 切换节点的展开/收起状态 (已废弃，使用 handleNodeClick 代替)
     */
    toggleNode(nodeId, depth) {
        console.log('⚠️ toggleNode is deprecated, use handleNodeClick instead');
        // 为了向后兼容，保留此方法但不建议使用
    }

    /**
     * 刷新图表显示
     */
    refreshChart() {
        if (this.rawData) {
            console.log('🔄 Refreshing chart with current data');
            this.render(this.rawData);
        }
    }

    /**
     * 创建分层结构
     */
    stratify(seriesData) {
        console.log('🔍 Stratify input data:', seriesData);
        
        const stratifyFunction = d3.stratify()
            .id(function (d) {
                console.log('🔑 Getting ID for:', d, 'ID:', d.id);
                return d.id;
            })
            .parentId(function (d) {
                const parts = d.id.split('.');
                const parentId = parts.length > 1 ? parts.slice(0, -1).join('.') : null;
                console.log('👨‍👩‍👧‍👦 Getting parent ID for:', d.id, 'Parent:', parentId);
                return parentId;
            });
            
        try {
            const result = stratifyFunction(seriesData);
            console.log('✅ Stratify successful:', result);
            return result;
        } catch (error) {
            console.error('❌ Stratify error:', error);
            throw error;
        }
    }

    /**
     * 获取节点显示名称
     */
    getNodeDisplayName(nodePath, isLeaf) {
        const parts = nodePath.split('.');
        const lastPart = parts[parts.length - 1];
        
        // 特殊处理根节点
        if (nodePath === 'Environmental Impact') {
            return 'Impact';
        }
        
        // 清理和格式化名称
        return lastPart
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .trim();
    }

    /**
     * 获取节点颜色
     */
    getNodeColor(nodePath, depth) {
        if (depth === 0) return this.colors.root;
        
        const parts = nodePath.split('.');
        if (parts.length >= 2) {
            const dimension = parts[1].toLowerCase();
            return this.colors[dimension] || this.colors.root;
        }
        
        return this.colors.root;
    }

    /**
     * 获取悬浮颜色
     */
    getHoverColor(baseColor) {
        // 简单的颜色变亮处理
        const hex = baseColor.replace('#', '');
        const r = Math.min(255, parseInt(hex.substr(0, 2), 16) + 30);
        const g = Math.min(255, parseInt(hex.substr(2, 2), 16) + 30);
        const b = Math.min(255, parseInt(hex.substr(4, 2), 16) + 30);
        
        return `rgb(${r}, ${g}, ${b})`;
    }

    /**
     * 处理窗口大小改变
     */
    handleResize() {
        if (this.chart) {
            this.chart.resize();
        }
    }

    /**
     * 销毁图表
     */
    destroy() {
        // 移除事件监听器
        document.removeEventListener('keydown', this.handleKeydown);
        
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
        
        // 清理面包屑导航
        if (this.breadcrumbContainer) {
            this.breadcrumbContainer.remove();
            this.breadcrumbContainer = null;
        }
    }
}

// 全局函数：初始化SHAP泡泡图
function initializeSHAPBubbleChart(shapData) {
    console.log('🔄 Initializing SHAP Bubble Chart with data:', shapData);
    
    // 检查必要的依赖
    if (typeof d3 === 'undefined') {
        console.error('❌ D3.js library not loaded');
        return;
    }
    
    if (typeof echarts === 'undefined') {
        console.error('❌ ECharts library not loaded');
        return;
    }
    
    try {
        // 清理现有图表
        const existingChart = window.shapBubbleChart;
        if (existingChart) {
            existingChart.destroy();
        }
        
        // 创建新的图表实例
        window.shapBubbleChart = new SHAPBubbleChart('packChart');
        
        // 渲染数据
        if (shapData) {
            window.shapBubbleChart.render(shapData);
        } else {
            console.warn('⚠️ No valid SHAP data provided');
        }
        
    } catch (error) {
        console.error('❌ Error initializing SHAP bubble chart:', error);
    }
}

// 为全局访问暴露退出聚焦模式的方法
window.exitFocusMode = function() {
    if (window.shapBubbleChart) {
        window.shapBubbleChart.exitFocusMode();
    }
};

console.log('✅ SHAP Bubble Chart module loaded successfully - Focus Drill-down Mode'); 