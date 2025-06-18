/**
 * Obscura No.7 - Data Visualization Components
 * 蒸汽朋克风格的数据可视化组件
 */

class DataVisualization {
    constructor() {
        this.charts = new Map();
        this.steampunkTheme = {
            colors: {
                primary: '#CD853F',    // brass-primary
                secondary: '#D2691E',  // copper
                accent: '#FFBF00',     // amber
                background: '#1C1C1C', // coal
                text: '#FDF5E6',       // warm-white
                grid: '#4F4F4F'        // steel
            },
            fonts: {
                family: '"Crimson Text", "Times New Roman", serif',
                size: 14,
                weight: 'normal'
            }
        };
        
        this.init();
    }

    /**
     * 初始化数据可视化模块
     */
    init() {
        this.loadChartLibrary();
        console.log('🔭 Data Visualization initialized');
    }

    /**
     * 动态加载Chart.js库
     */
    async loadChartLibrary() {
        if (typeof Chart !== 'undefined') {
            this.configureChartDefaults();
            return;
        }

        try {
            // 动态加载Chart.js
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js';
            script.onload = () => {
                this.configureChartDefaults();
                console.log('📊 Chart.js loaded');
            };
            script.onerror = () => {
                console.warn('Failed to load Chart.js, using fallback visualizations');
                this.useCanvasFallback = true;
            };
            document.head.appendChild(script);
        } catch (error) {
            console.warn('Chart.js loading failed:', error);
            this.useCanvasFallback = true;
        }
    }

    /**
     * 配置Chart.js默认设置
     */
    configureChartDefaults() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.font.family = this.steampunkTheme.fonts.family;
        Chart.defaults.font.size = this.steampunkTheme.fonts.size;
        Chart.defaults.color = this.steampunkTheme.colors.text;
        Chart.defaults.backgroundColor = this.steampunkTheme.colors.background;
        Chart.defaults.borderColor = this.steampunkTheme.colors.grid;
        Chart.defaults.scale.grid.color = this.steampunkTheme.colors.grid;
    }

    /**
     * 创建环境趋势图表
     * @param {string} containerId - 容器ID
     * @param {Object} predictionData - 预测数据
     */
    async createEnvironmentTrendChart(containerId, predictionData) {
        const container = document.querySelector(containerId);
        if (!container) return null;

        if (this.useCanvasFallback) {
            return this.createCanvasEnvironmentChart(container, predictionData);
        }

        try {
            // 创建canvas元素
            const canvas = document.createElement('canvas');
            canvas.width = 400;
            canvas.height = 300;
            container.appendChild(canvas);

            const ctx = canvas.getContext('2d');

            // 模拟时间序列数据
            const timeLabels = this.generateTimeLabels();
            const temperatureData = this.generateTrendData(
                predictionData.temperature || 20, 5, timeLabels.length
            );
            const humidityData = this.generateTrendData(
                predictionData.humidity || 60, 15, timeLabels.length
            );

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [
                        {
                            label: 'Temperature (°C)',
                            data: temperatureData,
                            borderColor: this.steampunkTheme.colors.primary,
                            backgroundColor: this.addAlpha(this.steampunkTheme.colors.primary, 0.1),
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Humidity (%)',
                            data: humidityData,
                            borderColor: this.steampunkTheme.colors.secondary,
                            backgroundColor: this.addAlpha(this.steampunkTheme.colors.secondary, 0.1),
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Environmental Trend Prediction',
                            color: this.steampunkTheme.colors.text,
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        legend: {
                            labels: {
                                color: this.steampunkTheme.colors.text,
                                usePointStyle: true
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: this.steampunkTheme.colors.grid
                            },
                            ticks: {
                                color: this.steampunkTheme.colors.text
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            grid: {
                                color: this.steampunkTheme.colors.grid
                            },
                            ticks: {
                                color: this.steampunkTheme.colors.text
                            },
                            title: {
                                display: true,
                                text: 'Temperature (°C)',
                                color: this.steampunkTheme.colors.text
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false,
                            },
                            ticks: {
                                color: this.steampunkTheme.colors.text
                            },
                            title: {
                                display: true,
                                text: 'Humidity (%)',
                                color: this.steampunkTheme.colors.text
                            }
                        }
                    }
                }
            });

            this.charts.set(containerId, chart);
            return chart;

        } catch (error) {
            console.error('Error creating environment trend chart:', error);
            return this.createCanvasEnvironmentChart(container, predictionData);
        }
    }

    /**
     * 创建置信度图表
     * @param {string} containerId - 容器ID
     * @param {Object} predictionData - 预测数据
     */
    async createConfidenceChart(containerId, predictionData) {
        const container = document.querySelector(containerId);
        if (!container) return null;

        if (this.useCanvasFallback) {
            return this.createCanvasConfidenceChart(container, predictionData);
        }

        try {
            const canvas = document.createElement('canvas');
            canvas.width = 300;
            canvas.height = 300;
            container.appendChild(canvas);

            const ctx = canvas.getContext('2d');
            
            const confidence = predictionData.confidence || 0.75;
            const remaining = 1 - confidence;

            const chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Confidence', 'Uncertainty'],
                    datasets: [{
                        data: [confidence * 100, remaining * 100],
                        backgroundColor: [
                            this.steampunkTheme.colors.primary,
                            this.steampunkTheme.colors.grid
                        ],
                        borderColor: [
                            this.steampunkTheme.colors.primary,
                            this.steampunkTheme.colors.grid
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Prediction Confidence',
                            color: this.steampunkTheme.colors.text,
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        legend: {
                            labels: {
                                color: this.steampunkTheme.colors.text
                            }
                        }
                    }
                }
            });

            this.charts.set(containerId, chart);
            return chart;

        } catch (error) {
            console.error('Error creating confidence chart:', error);
            return this.createCanvasConfidenceChart(container, predictionData);
        }
    }

    /**
     * 创建ML处理流程图
     * @param {string} containerId - 容器ID
     * @param {Object} predictionData - 预测数据
     */
    async createProcessFlowChart(containerId, predictionData) {
        const container = document.querySelector(containerId);
        if (!container) return null;

        // 处理流程图使用SVG实现
        const flowSteps = [
            { id: 'input', label: 'Environmental\nData Input', icon: '🌍' },
            { id: 'process', label: 'ML Model\nProcessing', icon: '🧠' },
            { id: 'predict', label: 'Future State\nPrediction', icon: '🔮' },
            { id: 'generate', label: 'AI Image\nGeneration', icon: '🎨' },
            { id: 'output', label: 'Vision\nOutput', icon: '🖼️' }
        ];

        const svg = this.createProcessFlowSVG(flowSteps, 600, 200);
        container.appendChild(svg);

        return svg;
    }

    /**
     * 创建流程图SVG
     * @param {Array} steps - 流程步骤
     * @param {number} width - 宽度
     * @param {number} height - 高度
     */
    createProcessFlowSVG(steps, width, height) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.style.background = this.steampunkTheme.colors.background;

        const stepWidth = width / steps.length;
        const centerY = height / 2;

        steps.forEach((step, index) => {
            const x = (index + 0.5) * stepWidth;
            
            // 创建步骤圆圈
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', centerY);
            circle.setAttribute('r', 30);
            circle.setAttribute('fill', this.steampunkTheme.colors.primary);
            circle.setAttribute('stroke', this.steampunkTheme.colors.accent);
            circle.setAttribute('stroke-width', 2);
            svg.appendChild(circle);

            // 添加图标文本
            const iconText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            iconText.setAttribute('x', x);
            iconText.setAttribute('y', centerY - 5);
            iconText.setAttribute('text-anchor', 'middle');
            iconText.setAttribute('fill', this.steampunkTheme.colors.background);
            iconText.setAttribute('font-size', '20');
            iconText.textContent = step.icon;
            svg.appendChild(iconText);

            // 添加标签
            const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            labelText.setAttribute('x', x);
            labelText.setAttribute('y', centerY + 50);
            labelText.setAttribute('text-anchor', 'middle');
            labelText.setAttribute('fill', this.steampunkTheme.colors.text);
            labelText.setAttribute('font-size', '12');
            labelText.setAttribute('font-family', this.steampunkTheme.fonts.family);
            
            // 处理多行文本
            const lines = step.label.split('\n');
            lines.forEach((line, lineIndex) => {
                const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                tspan.setAttribute('x', x);
                tspan.setAttribute('dy', lineIndex === 0 ? 0 : 15);
                tspan.textContent = line;
                labelText.appendChild(tspan);
            });
            
            svg.appendChild(labelText);

            // 添加连接箭头（除了最后一个步骤）
            if (index < steps.length - 1) {
                const arrow = this.createArrow(x + 30, centerY, stepWidth - 60, 0);
                svg.appendChild(arrow);
            }
        });

        return svg;
    }

    /**
     * 创建箭头SVG元素
     * @param {number} startX - 起始X坐标
     * @param {number} startY - 起始Y坐标
     * @param {number} length - 长度
     * @param {number} angle - 角度
     */
    createArrow(startX, startY, length, angle) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        // 箭头线
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', startX);
        line.setAttribute('y1', startY);
        line.setAttribute('x2', startX + length);
        line.setAttribute('y2', startY);
        line.setAttribute('stroke', this.steampunkTheme.colors.accent);
        line.setAttribute('stroke-width', 2);
        group.appendChild(line);

        // 箭头头部
        const arrowHead = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const headX = startX + length;
        const headY = startY;
        arrowHead.setAttribute('points', `${headX},${headY} ${headX-8},${headY-4} ${headX-8},${headY+4}`);
        arrowHead.setAttribute('fill', this.steampunkTheme.colors.accent);
        group.appendChild(arrowHead);

        return group;
    }

    /**
     * Canvas备用方案 - 环境图表
     */
    createCanvasEnvironmentChart(container, predictionData) {
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 300;
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        
        // 绘制背景
        ctx.fillStyle = this.steampunkTheme.colors.background;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制标题
        ctx.fillStyle = this.steampunkTheme.colors.text;
        ctx.font = '16px ' + this.steampunkTheme.fonts.family;
        ctx.textAlign = 'center';
        ctx.fillText('Environmental Data Overview', canvas.width / 2, 30);

        // 绘制环境数据
        const data = [
            { label: 'Temperature', value: predictionData.temperature || 20, unit: '°C', color: this.steampunkTheme.colors.primary },
            { label: 'Humidity', value: predictionData.humidity || 60, unit: '%', color: this.steampunkTheme.colors.secondary },
            { label: 'Pressure', value: predictionData.pressure || 1013, unit: 'hPa', color: this.steampunkTheme.colors.accent }
        ];

        data.forEach((item, index) => {
            const y = 80 + index * 60;
            
            // 绘制标签
            ctx.fillStyle = this.steampunkTheme.colors.text;
            ctx.font = '14px ' + this.steampunkTheme.fonts.family;
            ctx.textAlign = 'left';
            ctx.fillText(item.label, 50, y);

            // 绘制数值条
            const barWidth = (item.value / 100) * 200; // 简单的比例
            ctx.fillStyle = item.color;
            ctx.fillRect(50, y + 10, Math.max(barWidth, 20), 20);

            // 绘制数值
            ctx.fillStyle = this.steampunkTheme.colors.text;
            ctx.textAlign = 'left';
            ctx.fillText(`${item.value}${item.unit}`, 260, y + 25);
        });

        return canvas;
    }

    /**
     * Canvas备用方案 - 置信度图表
     */
    createCanvasConfidenceChart(container, predictionData) {
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 300;
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;

        // 绘制背景
        ctx.fillStyle = this.steampunkTheme.colors.background;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制标题
        ctx.fillStyle = this.steampunkTheme.colors.text;
        ctx.font = '16px ' + this.steampunkTheme.fonts.family;
        ctx.textAlign = 'center';
        ctx.fillText('Prediction Confidence', centerX, 30);

        const confidence = predictionData.confidence || 0.75;
        const confidenceAngle = confidence * 2 * Math.PI;

        // 绘制置信度弧
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + confidenceAngle);
        ctx.lineWidth = 20;
        ctx.strokeStyle = this.steampunkTheme.colors.primary;
        ctx.stroke();

        // 绘制剩余弧
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, -Math.PI / 2 + confidenceAngle, -Math.PI / 2 + 2 * Math.PI);
        ctx.strokeStyle = this.steampunkTheme.colors.grid;
        ctx.stroke();

        // 绘制中心文本
        ctx.fillStyle = this.steampunkTheme.colors.text;
        ctx.font = 'bold 24px ' + this.steampunkTheme.fonts.family;
        ctx.textAlign = 'center';
        ctx.fillText(`${Math.round(confidence * 100)}%`, centerX, centerY + 8);

        return canvas;
    }

    /**
     * 生成时间标签
     */
    generateTimeLabels() {
        const labels = [];
        const now = new Date();
        for (let i = -12; i <= 12; i += 3) {
            const time = new Date(now.getTime() + i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
        }
        return labels;
    }

    /**
     * 生成趋势数据
     * @param {number} baseValue - 基础值
     * @param {number} variance - 变化范围
     * @param {number} count - 数据点数量
     */
    generateTrendData(baseValue, variance, count) {
        const data = [];
        let current = baseValue;
        
        for (let i = 0; i < count; i++) {
            // 添加一些随机变化
            const change = (Math.random() - 0.5) * variance * 0.3;
            current += change;
            
            // 确保数据在合理范围内
            current = Math.max(0, Math.min(current, baseValue * 2));
            data.push(parseFloat(current.toFixed(1)));
        }
        
        return data;
    }

    /**
     * 为颜色添加透明度
     * @param {string} color - 颜色值
     * @param {number} alpha - 透明度
     */
    addAlpha(color, alpha) {
        // 简单的十六进制到rgba转换
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /**
     * 调整所有图表大小
     */
    resizeAllCharts() {
        this.charts.forEach((chart, containerId) => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    /**
     * 销毁图表
     * @param {string} containerId - 容器ID
     */
    destroyChart(containerId) {
        const chart = this.charts.get(containerId);
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
            this.charts.delete(containerId);
        }
    }

    /**
     * 销毁所有图表
     */
    destroyAllCharts() {
        this.charts.forEach((chart, containerId) => {
            this.destroyChart(containerId);
        });
    }
}

// 全局实例
window.dataVisualization = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.dataVisualization = new DataVisualization();
});

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataVisualization;
}
