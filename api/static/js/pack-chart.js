/**
 * 圆形打包图可视化组件
 * 基于D3.js和ECharts实现SHAP特征重要性的层次化可视化
 */

class PackChart {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 800,
            height: options.height || 600,
            padding: options.padding || 20,
            colors: {
                climate: '#FF6B6B',    // 红色 - 气候
                geographic: '#4ECDC4', // 青色 - 地理  
                economic: '#45B7D1',   // 蓝色 - 经济
                root: '#FFA726',       // 橙色 - 根节点
                positive: '#4CAF50',   // 绿色 - 正向影响
                negative: '#F44336'    // 红色 - 负向影响
            },
            steampunkColors: {
                brass: '#B8860B',      // 黄铜色
                copper: '#CD7F32',     // 铜色  
                bronze: '#8C6239',     // 青铜色
                steam: '#708090',      // 蒸汽灰
                gear: '#2F4F4F'        // 齿轮色
            },
            ...options
        };
        
        this.chart = null;
        this.currentData = null;
        this.currentFocus = 'overview';
        
        this.initChart();
    }

    /**
     * 初始化ECharts实例
     */
    initChart() {
        if (!this.container) {
            console.error(`Container ${this.containerId} not found`);
            return;
        }

        // 初始化ECharts
        this.chart = echarts.init(this.container);
        
        // 设置响应式
        window.addEventListener('resize', () => {
            this.chart.resize();
        });

        console.log('✅ Pack chart initialized');
    }

    /**
     * 渲染圆形打包图
     */
    render(data) {
        if (!this.chart || !data) {
            console.error('Chart or data not available');
            return;
        }

        this.currentData = data;
        
        // 处理数据为ECharts格式
        const chartData = this.processData(data);
        
        // 配置ECharts选项
        const option = this.buildChartOption(chartData);
        
        // 渲染图表
        this.chart.setOption(option);
        
        // 绑定交互事件
        this.bindEvents();
        
        console.log('✅ Pack chart rendered successfully');
    }

    /**
     * 处理数据为ECharts层次结构
     */
    processData(rawData) {
        const processNode = (node, depth = 0) => {
            const processed = {
                name: node.name,
                value: node.value * 1000, // 放大以便显示
                depth: depth,
                originalValue: node.value,
                impact: node.impact || node.value,
                itemStyle: {
                    color: this.getNodeColor(node, depth)
                }
            };

            if (node.children && node.children.length > 0) {
                processed.children = node.children.map(child => 
                    processNode(child, depth + 1)
                );
            }

            return processed;
        };

        return processNode(rawData);
    }

    /**
     * 获取节点颜色
     */
    getNodeColor(node, depth) {
        // 根节点
        if (depth === 0) {
            return this.options.steampunkColors.brass;
        }
        
        // 维度节点
        if (depth === 1) {
            switch (node.name.toLowerCase()) {
                case 'climate':
                    return this.options.colors.climate;
                case 'geographic':
                    return this.options.colors.geographic;
                case 'economic':
                    return this.options.colors.economic;
                default:
                    return this.options.steampunkColors.copper;
            }
        }
        
        // 特征节点 - 根据影响方向着色
        if (depth === 2) {
            const impact = node.impact || 0;
            if (impact > 0) {
                return this.options.colors.positive;
            } else if (impact < 0) {
                return this.options.colors.negative;
            } else {
                return this.options.steampunkColors.steam;
            }
        }
        
        return this.options.steampunkColors.gear;
    }

    /**
     * 构建ECharts配置选项
     */
    buildChartOption(data) {
        return {
            title: {
                text: 'Environmental Feature Impact',
                left: 'center',
                top: 20,
                textStyle: {
                    color: this.options.steampunkColors.brass,
                    fontSize: 18,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    const data = params.data;
                    const impact = data.impact || data.originalValue || 0;
                    const impactText = impact > 0 ? 'Positive' : impact < 0 ? 'Negative' : 'Neutral';
                    
                    return `
                        <div style="padding: 10px;">
                            <strong>${data.name}</strong><br/>
                            Impact: ${(impact * 100).toFixed(1)}%<br/>
                            Influence: ${impactText}<br/>
                            Depth Level: ${data.depth}
                        </div>
                    `;
                },
                backgroundColor: 'rgba(0,0,0,0.8)',
                borderColor: this.options.steampunkColors.brass,
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            series: [{
                type: 'sunburst',
                data: [data],
                radius: [0, '90%'],
                center: ['50%', '55%'],
                sort: null,
                emphasis: {
                    focus: 'ancestor'
                },
                label: {
                    fontSize: 12,
                    fontWeight: 'bold',
                    color: '#fff',
                    textShadowColor: 'rgba(0, 0, 0, 0.5)',
                    textShadowBlur: 2
                },
                levels: [
                    {},
                    {
                        r0: '15%',
                        r: '35%',
                        itemStyle: {
                            borderWidth: 2,
                            borderColor: this.options.steampunkColors.bronze
                        },
                        label: {
                            fontSize: 14,
                            fontWeight: 'bold'
                        }
                    },
                    {
                        r0: '35%',
                        r: '70%',
                        itemStyle: {
                            borderWidth: 1,
                            borderColor: '#fff'
                        },
                        label: {
                            fontSize: 10
                        }
                    },
                    {
                        r0: '70%',
                        r: '90%',
                        label: {
                            position: 'outside',
                            fontSize: 8,
                            silent: false
                        },
                        itemStyle: {
                            borderWidth: 1
                        }
                    }
                ]
            }]
        };
    }

    /**
     * 绑定交互事件
     */
    bindEvents() {
        // 点击事件 - 钻取
        this.chart.off('click');
        this.chart.on('click', (params) => {
            if (params.data.children) {
                console.log(`🎯 Drilling down into: ${params.data.name}`);
                // 这里可以实现钻取逻辑
                this.focusDimension(params.data.name.toLowerCase());
            }
        });

        // 鼠标悬停事件
        this.chart.off('mouseover');
        this.chart.on('mouseover', (params) => {
            // 高亮效果已由ECharts内置处理
        });
    }

    /**
     * 聚焦特定维度
     */
    focusDimension(dimension) {
        if (!this.currentData) return;

        this.currentFocus = dimension;
        
        console.log(`🎯 Focusing on dimension: ${dimension}`);
        
        // 根据维度调整数据视图
        let focusedData;
        
        if (dimension === 'overview') {
            focusedData = this.currentData;
        } else {
            // 找到特定维度的数据
            const dimensionData = this.currentData.children?.find(
                child => child.name.toLowerCase() === dimension
            );
            
            if (dimensionData) {
                focusedData = {
                    name: dimensionData.name + ' Analysis',
                    value: dimensionData.value,
                    children: dimensionData.children || []
                };
            } else {
                focusedData = this.currentData;
            }
        }
        
        // 重新渲染
        const chartData = this.processData(focusedData);
        const option = this.buildChartOption(chartData);
        
        this.chart.setOption(option, true);
        
        // 更新UI按钮状态
        this.updateControlButtons(dimension);
    }

    /**
     * 更新控制按钮状态
     */
    updateControlButtons(activeDimension) {
        const buttons = document.querySelectorAll('.viz-control-btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-dimension') === activeDimension) {
                btn.classList.add('active');
            }
        });
    }

    /**
     * 更新数据
     */
    updateData(newData) {
        this.render(newData);
    }

    /**
     * 销毁图表
     */
    dispose() {
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
    }

    /**
     * 获取当前图表状态
     */
    getState() {
        return {
            focus: this.currentFocus,
            data: this.currentData
        };
    }
}

// 将类暴露到全局作用域
window.PackChart = PackChart; 