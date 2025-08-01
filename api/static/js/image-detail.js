/**
 * Obscura No.7 - Image Detail Page JavaScript
 * 图片详情页的交互逻辑和数据处理
 */

class ImageDetailPage {
    constructor(imageId = null) {
        this.imageId = imageId;
        this.imageData = null;
        this.predictionData = null;
        this.shapAnalysisData = null;
        
        this.init();
    }

    /**
     * 初始化详情页
     */
    init() {
        if (!this.imageId) {
            this.extractImageId();
        }
        this.bindEvents();
        this.loadImageData();
        console.log('🎬 Cinema-style Image Detail Page initialized');
    }

    /**
     * 从URL中提取图片ID
     */
    extractImageId() {
        const path = window.location.pathname;
        const matches = path.match(/\/image\/(\d+)/);
        if (matches) {
            this.imageId = parseInt(matches[1]);
        } else {
            console.error('No image ID found in URL');
            this.showError('Invalid image URL');
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 下载按钮（新的cinema布局）
        const downloadButton = document.querySelector('#downloadBtn');
        downloadButton?.addEventListener('click', () => this.downloadImage());

        // 图片点击全屏查看
        const cinemaImage = document.querySelector('#mainImage');
        cinemaImage?.addEventListener('click', () => this.toggleFullscreen());

        // 全屏关闭按钮
        const fullscreenClose = document.querySelector('#fullscreenClose');
        fullscreenClose?.addEventListener('click', () => this.closeFullscreen());

        // 刷新故事按钮
        const refreshStoryBtn = document.querySelector('#refreshStoryBtn');
        refreshStoryBtn?.addEventListener('click', () => this.refreshStory());

        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // 图片懒加载
        this.initializeLazyLoading();

        // 窗口大小改变时重新调整图表
        window.addEventListener('resize', () => this.resizeCharts());
    }

    /**
     * 加载图片数据
     */
    async loadImageData() {
        if (!this.imageId) return;

        try {
            this.showLoading();

            // 并行加载多个数据源，包括SHAP分析
            const [imageResponse, relatedResponse, shapResponse] = await Promise.all([
                fetch(`/api/v1/images/${this.imageId}`),
                fetch(`/api/v1/images/${this.imageId}/related`),
                fetch(`/api/v1/images/${this.imageId}/shap-analysis`)
            ]);

            if (!imageResponse.ok) {
                throw new Error(`Failed to load image: ${imageResponse.status}`);
            }

            const imageData = await imageResponse.json();
            this.imageData = imageData.image;
            this.predictionData = imageData.prediction;

            // 相关图片可能不存在，不强制要求
            if (relatedResponse.ok) {
                const relatedData = await relatedResponse.json();
                this.relatedImages = relatedData.images || [];
            }

            // 加载SHAP分析数据
            if (shapResponse.ok) {
                const shapData = await shapResponse.json();
                this.shapAnalysisData = shapData.data;
                console.log('🧠 SHAP analysis data loaded successfully');
            } else {
                console.warn('SHAP analysis not available for this image');
                this.shapAnalysisData = null;
            }

            await this.populatePageContent();
            this.hideLoading();

        } catch (error) {
            console.error('Error loading image data:', error);
            this.hideLoading();
            this.showError('Failed to load image details');
        }
    }

    /**
     * 填充页面内容
     */
    async populatePageContent() {
        if (!this.imageData) return;

        // 更新页面标题
        document.title = `${this.imageData.description || 'Environmental Vision'} - Obscura No.7`;

        // 填充基本信息
        this.populateBasicInfo();

        // 填充预测数据
        this.populatePredictionData();

        // 填充SHAP分析数据
        this.populateSHAPAnalysis();

        // 创建数据可视化
        await this.createDataVisualizations();

        // 填充相关图片
        this.populateRelatedImages();

        // 更新分享数据
        this.updateShareData();
    }

    /**
     * 填充基本信息
     */
    populateBasicInfo() {
        // 主图片（cinema风格）
        const mainImage = document.querySelector('#mainImage');
        if (mainImage && this.imageData.url) {
            // 添加图片加载事件
            mainImage.onload = () => {
                console.log('✅ 图片加载成功:', this.imageData.url);
                mainImage.style.display = 'block';
            };
            mainImage.onerror = () => {
                console.error('❌ 图片加载失败:', this.imageData.url);
                mainImage.alt = '图片加载失败';
                mainImage.style.background = 'linear-gradient(45deg, #1a1a2e, #16213e)';
                mainImage.style.display = 'flex';
                mainImage.style.alignItems = 'center';
                mainImage.style.justifyContent = 'center';
                mainImage.style.color = '#CD853F';
                mainImage.style.fontSize = '16px';
                mainImage.innerHTML = '🖼️ 图片加载失败';
            };
            
            mainImage.src = this.imageData.url;
            mainImage.alt = this.imageData.description || 'AI Generated Environmental Vision';
            console.log('🖼️ 设置图片URL:', this.imageData.url);
        }

        // 更新页面标题
        const pageTitle = document.querySelector('#imageTitle');
        if (pageTitle) {
            pageTitle.textContent = this.imageData.description || 'Environmental Vision Analysis';
        }

        // 全屏图片
        const fullscreenImage = document.querySelector('#fullscreenImage');
        if (fullscreenImage && this.imageData.url) {
            fullscreenImage.src = this.imageData.url;
            fullscreenImage.alt = this.imageData.description || 'AI Generated Environmental Vision';
        }

        console.log('✅ Basic image info populated');
    }

    /**
     * 填充预测数据
     */
    populatePredictionData() {
        if (!this.predictionData) return;

        // 环境参数
        const envData = [
            { key: 'temperature', label: 'Temperature', unit: '°C', icon: '🌡️' },
            { key: 'humidity', label: 'Humidity', unit: '%', icon: '💧' },
            { key: 'pressure', label: 'Pressure', unit: 'hPa', icon: '🌀' },
            { key: 'wind_speed', label: 'Wind Speed', unit: 'm/s', icon: '💨' },
            { key: 'visibility', label: 'Visibility', unit: 'km', icon: '👁️' }
        ];

        const envContainer = document.querySelector('#environment-data');
        if (envContainer) {
            envContainer.innerHTML = '';
            
            envData.forEach(item => {
                const value = this.predictionData[item.key];
                if (value !== undefined && value !== null) {
                    const envItem = document.createElement('div');
                    envItem.className = 'env-data-item';
                    envItem.innerHTML = `
                        <div class="env-icon">${item.icon}</div>
                        <div class="env-content">
                            <div class="env-label">${item.label}</div>
                            <div class="env-value">${value}${item.unit}</div>
                        </div>
                    `;
                    envContainer.appendChild(envItem);
                }
            });
        }

        // 位置信息
        const location = document.querySelector('#prediction-location');
        if (location && this.predictionData.location) {
            location.textContent = this.predictionData.location;
        }

        // 置信度
        const confidence = document.querySelector('#prediction-confidence');
        if (confidence && this.predictionData.confidence) {
            const confidencePercent = Math.round(this.predictionData.confidence * 100);
            confidence.textContent = `${confidencePercent}%`;
            
            // 添加置信度颜色
            const confidenceBar = document.querySelector('#confidence-bar');
            if (confidenceBar) {
                confidenceBar.style.width = `${confidencePercent}%`;
                if (confidencePercent >= 80) {
                    confidenceBar.className = 'confidence-bar high';
                } else if (confidencePercent >= 60) {
                    confidenceBar.className = 'confidence-bar medium';
                } else {
                    confidenceBar.className = 'confidence-bar low';
                }
            }
        }
    }

    /**
     * 填充SHAP分析数据（Task 5.1: 更新为层次化数据处理）
     */
    populateSHAPAnalysis() {
        if (!this.shapAnalysisData) {
            console.log('No SHAP analysis data available');
            // 隐藏SHAP分析部分
            const shapSection = document.querySelector('.shap-analysis-section');
            if (shapSection) {
                shapSection.style.display = 'none';
            }
            return;
        }

        // 新的数据结构：shapAnalysisData直接包含所有字段
        const shapData = this.shapAnalysisData;
        
        // 检查数据验证结果
        if (shapData.data_validation && !shapData.data_validation.is_valid) {
            console.warn('⚠️ SHAP data validation failed:', shapData.data_validation.errors);
        }
        
        // 填充三个维度评分
        this.populateSimplifiedScores(shapData);
        
        // 填充AI故事
        this.populateAIStory(shapData);
        
        // 使用新的层次化数据准备圆形打包图 
        this.prepareHierarchicalPackChart(shapData);
        
        // 填充技术信息
        this.populateSHAPTechnicalInfo(shapData);
        
        console.log('🧠 Enhanced SHAP analysis populated successfully');
        console.log('📊 Data validation:', shapData.data_validation);
    }
    
    // Task 5.2: Bubble chart code removed - replaced with hierarchical pack chart

    /**
     * Task 5.3: 准备分层泡泡图数据（重新实现为真正的泡泡图效果）
     */
    prepareHierarchicalPackChart(shapData) {
        // 显示加载状态
        this.showPackChartLoading('Preparing hierarchical bubble chart...');
        
        // 显示数据验证结果
        if (shapData.data_validation) {
            this.showDataValidation(shapData.data_validation);
        }
        
        try {
            // 使用新的分层泡泡图实现
            console.log('🎯 Initializing SHAP Hierarchical Bubble Chart');
            console.log('📊 SHAP Data structure:', shapData);
            
            // 修复：传递正确的数据结构
            this.initializeSHAPBubbleChart(shapData);
            
        } catch (error) {
            console.error('❌ Error in prepareHierarchicalPackChart:', error);
            this.showPackChartError(`Bubble chart error: ${error.message}`);
        }
    }

    /**
     * 初始化SHAP分层泡泡图
     */
    initializeSHAPBubbleChart(shapData) {
        try {
            // 检查SHAPBubbleChart是否已加载
            if (typeof SHAPBubbleChart === 'undefined') {
                console.warn('⚠️ SHAPBubbleChart component not loaded, attempting to load...');
                this.loadSHAPBubbleChartScript(() => this.initializeSHAPBubbleChart(shapData));
                return;
            }

            // 隐藏加载状态，显示图表容器
            this.showPackChartLoading('Rendering bubble chart...');

            // 创建或更新分层泡泡图实例
            if (!window.shapBubbleChartInstance) {
                const container = document.getElementById('packChart');
                if (!container) {
                    console.error('❌ Bubble chart container not found');
                    this.showPackChartError('Container not found');
                    return;
                }

                window.shapBubbleChartInstance = new SHAPBubbleChart('packChart', {
                    width: 600,
                    height: 500
                });
            }

            // 渲染数据 - 传递正确的数据结构
            console.log('🔄 Rendering SHAP data:', shapData);
            window.shapBubbleChartInstance.render(shapData);
            console.log('✅ SHAP Hierarchical Bubble Chart rendered successfully');

            // 显示控制按钮和图表
            this.showPackChartControls();

        } catch (error) {
            console.error('❌ Error initializing SHAP bubble chart:', error);
            this.showPackChartError(`Initialization error: ${error.message}`);
        }
    }

    /**
     * 动态加载SHAPBubbleChart脚本
     */
    loadSHAPBubbleChartScript(callback) {
        const script = document.createElement('script');
        script.src = '/static/js/shap-bubble-chart.js';
        script.onload = callback;
        script.onerror = () => {
            console.error('❌ Failed to load shap-bubble-chart.js');
            this.showPackChartError('Script loading failed');
        };
        document.head.appendChild(script);
    }

    // PackChart相关代码已移除，使用SHAPBubbleChart替代

    /**
     * 填充SHAP分数卡片
     */
    populateSHAPScores(shapData) {
        // 气候分数
        const climateScore = document.querySelector('#shapClimateScore');
        const climateScoreFill = document.querySelector('#climateScoreFill');
        if (climateScore && shapData.climate_score !== undefined) {
            const score = (shapData.climate_score * 100).toFixed(1);
            climateScore.textContent = `${score}%`;
            climateScoreFill.style.width = `${score}%`;
        }

        // 地理分数
        const geographicScore = document.querySelector('#shapGeographicScore');
        const geographicScoreFill = document.querySelector('#geographicScoreFill');
        if (geographicScore && shapData.geographic_score !== undefined) {
            const score = (shapData.geographic_score * 100).toFixed(1);
            geographicScore.textContent = `${score}%`;
            geographicScoreFill.style.width = `${score}%`;
        }

        // 经济分数
        const economicScore = document.querySelector('#shapEconomicScore');
        const economicScoreFill = document.querySelector('#economicScoreFill');
        if (economicScore && shapData.economic_score !== undefined) {
            const score = (shapData.economic_score * 100).toFixed(1);
            economicScore.textContent = `${score}%`;
            economicScoreFill.style.width = `${score}%`;
        }

        // 最终分数
        const finalScore = document.querySelector('#shapFinalScore');
        const finalScoreFill = document.querySelector('#finalScoreFill');
        if (finalScore && shapData.final_score !== undefined) {
            const score = (shapData.final_score * 100).toFixed(1);
            finalScore.textContent = `${score}%`;
            finalScoreFill.style.width = `${score}%`;
        }
    }

    /**
     * 填充特征重要性
     */
    populateFeatureImportance(shapData) {
        const featureBarsContainer = document.querySelector('#shapFeatureBars');
        const featureLoading = document.querySelector('#shapFeatureLoading');
        
        if (!featureBarsContainer) return;

        // 隐藏loading，显示内容
        if (featureLoading) featureLoading.style.display = 'none';
        featureBarsContainer.style.display = 'block';

        // 清空容器
        featureBarsContainer.innerHTML = '';

        // 检查是否有特征重要性数据
        const featureImportance = shapData.shap_analysis?.feature_importance || {};
        const features = Object.entries(featureImportance).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));

        if (features.length === 0) {
            featureBarsContainer.innerHTML = '<p class="no-data">No feature importance data available</p>';
            return;
        }

        // 创建特征重要性条形图
        features.forEach(([feature, importance]) => {
            const featureBar = document.createElement('div');
            featureBar.className = 'feature-bar-item';
            
            const absoluteImportance = Math.abs(importance);
            const maxImportance = Math.abs(features[0][1]);
            const width = (absoluteImportance / maxImportance) * 100;
            const isPositive = importance >= 0;
            
            featureBar.innerHTML = `
                <div class="feature-label">${this.formatFeatureName(feature)}</div>
                <div class="feature-bar-track">
                    <div class="feature-bar-fill ${isPositive ? 'positive' : 'negative'}" 
                         style="width: ${width}%"></div>
                </div>
                <div class="feature-value">${importance.toFixed(3)}</div>
            `;
            
            featureBarsContainer.appendChild(featureBar);
        });
    }

    /**
     * 填充简化的三维度评分和总体分数
     */
    populateSimplifiedScores(shapData) {
        // 🔧 修复：使用正确的字段名
        // 计算总体分数 (Final Score)
        const overallScore = shapData.final_score || 
                           ((shapData.climate_score + shapData.geographic_score + shapData.economic_score) / 3);
        
        // 总体分数（保持绝对值显示）
        const overallScoreElement = document.querySelector('#overallScore');
        if (overallScoreElement) {
            // 🔧 修复：数据库中的值已经是百分比，不需要再乘以100
            overallScoreElement.textContent = `${overallScore.toFixed(1)}%`;
        }
        
        // 🔧 修复：使用正确的字段名 - climate_score 而不是 climate_change
        const climateScore = document.querySelector('#climateScore');
        if (climateScore && shapData.climate_score !== undefined) {
            const score = shapData.climate_score;
            const sign = score >= 0 ? '+' : '';
            const colorClass = score >= 0 ? 'positive-change' : 'negative-change';
            // 🔧 修复：数据库中的值已经是百分比，不需要再乘以100
            climateScore.innerHTML = `<span class="${colorClass}">${sign}${score.toFixed(1)}%</span>`;
        }

        // 🔧 修复：使用正确的字段名 - geographic_score 而不是 geographic_change
        const geographicScore = document.querySelector('#geographicScore');
        if (geographicScore && shapData.geographic_score !== undefined) {
            const score = shapData.geographic_score;
            const sign = score >= 0 ? '+' : '';
            const colorClass = score >= 0 ? 'positive-change' : 'negative-change';
            // 🔧 修复：数据库中的值已经是百分比，不需要再乘以100
            geographicScore.innerHTML = `<span class="${colorClass}">${sign}${score.toFixed(1)}%</span>`;
        }

        // 🔧 修复：使用正确的字段名 - economic_score 而不是 economic_change
        const economicScore = document.querySelector('#economicScore');
        if (economicScore && shapData.economic_score !== undefined) {
            const score = shapData.economic_score;
            const sign = score >= 0 ? '+' : '';
            const colorClass = score >= 0 ? 'positive-change' : 'negative-change';
            // 🔧 修复：数据库中的值已经是百分比，不需要再乘以100
            economicScore.innerHTML = `<span class="${colorClass}">${sign}${score.toFixed(1)}%</span>`;
        }

        console.log('✅ Simplified scores populated with correct field names and unit conversion:', {
            climate: shapData.climate_score,
            geographic: shapData.geographic_score,
            economic: shapData.economic_score,
            overall: overallScore
        });
    }

    // 原有的PackChart相关方法已移除，使用SHAPBubbleChart替代

    /**
     * 显示圆形打包图控制按钮
     */
    showPackChartControls() {
        const loading = document.querySelector('#packChartLoading');
        const chart = document.querySelector('#packChart');
        const controls = document.querySelector('#vizControls');

        if (loading) loading.style.display = 'none';
        if (chart) chart.style.display = 'block';
        if (controls) controls.style.display = 'flex';

        console.log('✅ Pack chart UI updated');
    }

    /**
     * 显示圆形打包图错误（Task 6.3: 增强错误处理）
     */
    showPackChartError(errorMessage = 'Visualization loading failed') {
        const loading = document.querySelector('#packChartLoading');
        const container = document.querySelector('.pack-chart-container');
        
        if (loading) {
            loading.innerHTML = `
                <div class="chart-error steampunk-error">
                    <div class="error-icon">⚙️</div>
                    <h4 class="error-title">Visualization Malfunction</h4>
                    <p class="error-message">${errorMessage}</p>
                    <button class="retry-button" onclick="window.location.reload()">
                        <span>🔄</span> Retry Analysis
                    </button>
                </div>
            `;
        }
        
        // 添加数据验证失败指示器
        if (container && !container.querySelector('.data-validation-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'data-validation-indicator';
            indicator.innerHTML = `
                <span class="validation-icon invalid">❌</span>
                <span class="validation-text">Error</span>
            `;
            container.appendChild(indicator);
        }
        
        console.error('🔧 Pack chart error:', errorMessage);
    }

    /**
     * 显示加载状态（Task 6.3: 增强加载体验）
     */
    showPackChartLoading(message = 'Analyzing environmental data...') {
        const loading = document.querySelector('#packChartLoading');
        if (loading) {
            loading.style.display = 'flex';
            loading.innerHTML = `
                <div class="chart-loading steampunk-loading">
                    <div class="loading-gears">
                        <span class="gear gear-1">⚙️</span>
                        <span class="gear gear-2">⚙️</span>
                        <span class="gear gear-3">⚙️</span>
                    </div>
                    <p class="loading-message">${message}</p>
                    <div class="loading-progress">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * 显示数据验证结果（Task 6.3: 新增）
     */
    showDataValidation(validationResult) {
        const container = document.querySelector('.pack-chart-container');
        if (!container || !validationResult) return;

        // 移除现有指示器
        const existingIndicator = container.querySelector('.data-validation-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // 创建新的验证指示器
        const indicator = document.createElement('div');
        indicator.className = 'data-validation-indicator';
        
        const isValid = validationResult.is_valid;
        const featureCount = validationResult.completeness_report?.total_features || 0;
        
        indicator.innerHTML = `
            <span class="validation-icon ${isValid ? 'valid' : 'invalid'}">
                ${isValid ? '✅' : '⚠️'}
            </span>
            <span class="validation-text">
                ${featureCount} features
            </span>
        `;
        
        // 添加工具提示
        if (validationResult.errors?.length > 0 || validationResult.warnings?.length > 0) {
            indicator.title = [
                ...validationResult.errors.map(e => `Error: ${e}`),
                ...validationResult.warnings.map(w => `Warning: ${w}`)
            ].join('\n');
        }
        
        container.appendChild(indicator);
    }

    /**
     * 填充AI故事（新格式：单一英文故事）
     */
    populateAIStory(shapData) {
        const storyContent = document.querySelector('#storyContent');
        const storyLoading = document.querySelector('#storyLoading');
        const narrativeText = document.querySelector('#narrativeText');
        
        if (!shapData.ai_story) {
            console.log('No AI story data available');
            return;
        }

        // 隐藏loading，显示内容
        if (storyLoading) storyLoading.style.display = 'none';
        if (storyContent) storyContent.style.display = 'block';

        const story = shapData.ai_story;

        // 新格式：故事是简单字符串
        if (typeof story === 'string') {
            if (narrativeText) {
                narrativeText.textContent = story;
            }
            console.log('✅ AI story populated (string format)');
            return;
        }

        // 兼容旧格式：故事是对象（用于向后兼容）
        if (typeof story === 'object') {
            let combinedStory = '';
            
            if (story.introduction) combinedStory += story.introduction + ' ';
            if (story.main_findings) combinedStory += story.main_findings + ' ';
            if (story.feature_analysis) combinedStory += story.feature_analysis + ' ';
            if (story.risk_assessment) combinedStory += story.risk_assessment + ' ';
            if (story.conclusion) combinedStory += story.conclusion + ' ';
            if (story.summary) combinedStory += story.summary;
            
            if (narrativeText && combinedStory.trim()) {
                narrativeText.textContent = combinedStory.trim();
            }
            console.log('✅ AI story populated (object format - legacy)');
        }
    }

    /**
     * 填充SHAP技术信息
     */
    populateSHAPTechnicalInfo(shapData) {
        // 模型精度
        const modelAccuracy = document.querySelector('#shapModelAccuracy');
        if (modelAccuracy && shapData.model_accuracy !== undefined) {
            modelAccuracy.textContent = `${(shapData.model_accuracy * 100).toFixed(2)}%`;
        }

        // 处理时间
        const processingTime = document.querySelector('#shapProcessingTime');
        if (processingTime && shapData.processing_time !== undefined) {
            processingTime.textContent = `${shapData.processing_time.toFixed(2)}s`;
        }

        // 分析时间戳
        const timestamp = document.querySelector('#shapTimestamp');
        if (timestamp && this.shapAnalysisData.integration_metadata?.analysis_timestamp) {
            const date = new Date(this.shapAnalysisData.integration_metadata.analysis_timestamp);
            timestamp.textContent = date.toLocaleString();
        }

        // 模型版本
        const modelVersion = document.querySelector('#shapModelVersion');
        if (modelVersion && this.shapAnalysisData.integration_metadata?.model_version) {
            modelVersion.textContent = this.shapAnalysisData.integration_metadata.model_version;
        }
    }

    /**
     * 格式化特征名称
     */
    formatFeatureName(feature) {
        const featureNames = {
            'temperature': 'Temperature',
            'humidity': 'Humidity', 
            'pressure': 'Pressure',
            'location_factor': 'Location Factor',
            'seasonal_factor': 'Seasonal Factor',
            'climate_zone': 'Climate Zone',
            'vegetation_index': 'Vegetation Index',
            'urban_density': 'Urban Density'
        };
        
        return featureNames[feature] || feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * 创建数据可视化
     */
    async createDataVisualizations() {
        if (!window.dataVisualization) {
            console.warn('Data visualization module not loaded');
            return;
        }

        try {
            // 环境趋势图表
            await window.dataVisualization.createEnvironmentTrendChart(
                '#env-trend-chart',
                this.predictionData
            );

            // 预测准确度图表
            await window.dataVisualization.createConfidenceChart(
                '#confidence-chart',
                this.predictionData
            );

            // ML处理流程图
            await window.dataVisualization.createProcessFlowChart(
                '#process-flow-chart',
                this.predictionData
            );

        } catch (error) {
            console.error('Error creating visualizations:', error);
        }
    }

    /**
     * 绘制SHAP图表
     */
    drawSHAPCharts() {
        if (!this.shapAnalysisData) return;

        const featureImportanceData = this.shapAnalysisData.feature_importance;
        const predictionValueData = this.shapAnalysisData.prediction_value;
        const interactionData = this.shapAnalysisData.interaction_effects;

        // 特征重要性图表
        if (featureImportanceData && featureImportanceData.length > 0) {
            window.dataVisualization.createFeatureImportanceChart(
                '#shap-feature-importance-chart',
                featureImportanceData
            );
        }

        // 预测值图表
        if (predictionValueData && predictionValueData.length > 0) {
            window.dataVisualization.createPredictionValueChart(
                '#shap-prediction-value-chart',
                predictionValueData
            );
        }

        // 交互作用图表
        if (interactionData && interactionData.length > 0) {
            window.dataVisualization.createInteractionChart(
                '#shap-interaction-chart',
                interactionData
            );
        }
    }

    /**
     * 填充相关图片
     */
    populateRelatedImages() {
        const relatedContainer = document.querySelector('#related-images');
        if (!relatedContainer || this.relatedImages.length === 0) {
            // 隐藏相关图片部分
            const relatedSection = document.querySelector('.related-section');
            if (relatedSection) {
                relatedSection.style.display = 'none';
            }
            return;
        }

        relatedContainer.innerHTML = '';
        
        this.relatedImages.forEach(image => {
            const imageItem = document.createElement('div');
            imageItem.className = 'related-image-item';
            imageItem.innerHTML = `
                <a href="/image/${image.id}" class="related-image-link">
                    <img src="${image.thumbnail_url || image.url}" 
                         alt="${image.description || 'Related vision'}"
                         loading="lazy"
                         class="related-image">
                    <div class="related-image-overlay">
                        <div class="related-image-title">${image.description || 'Environmental Vision'}</div>
                        <div class="related-image-time">${new Date(image.created_at).toLocaleDateString()}</div>
                    </div>
                </a>
            `;
            relatedContainer.appendChild(imageItem);
        });
    }

    /**
     * 更新分享数据
     */
    updateShareData() {
        if (!this.imageData) return;

        // 更新Open Graph meta标签
        this.updateMetaTag('og:title', this.imageData.description || 'Environmental Vision - Obscura No.7');
        this.updateMetaTag('og:description', 'AI-generated vision of environmental future based on predictive data');
        this.updateMetaTag('og:image', this.imageData.url);
        this.updateMetaTag('og:url', window.location.href);

        // 更新Twitter Card meta标签
        this.updateMetaTag('twitter:title', this.imageData.description || 'Environmental Vision');
        this.updateMetaTag('twitter:description', 'AI-generated environmental prediction visualization');
        this.updateMetaTag('twitter:image', this.imageData.url);
    }

    /**
     * 更新meta标签
     */
    updateMetaTag(property, content) {
        let meta = document.querySelector(`meta[property="${property}"]`) || 
                   document.querySelector(`meta[name="${property}"]`);
        
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute(property.startsWith('og:') ? 'property' : 'name', property);
            document.head.appendChild(meta);
        }
        
        meta.setAttribute('content', content);
    }

    /**
     * 返回上一页
     */
    goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/gallery';
        }
    }

    /**
     * 刷新AI故事
     */
    async refreshStory() {
        if (!this.imageId) return;
        
        try {
            const refreshBtn = document.querySelector('#refreshStoryBtn');
            const storyContent = document.querySelector('#storyContent');
            const storyLoading = document.querySelector('#storyLoading');
            
            // 显示加载状态
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="refresh-icon">🔄</span><span class="refresh-text">Refreshing...</span>';
            storyContent.style.display = 'none';
            storyLoading.style.display = 'block';
            
            console.log(`🔄 Refreshing story for image ${this.imageId}`);
            
            // 调用刷新API
            const response = await fetch(`/api/v1/images/${this.imageId}/refresh-story`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // 重新加载图片数据以获取新故事
                    await this.loadImageData();
                    console.log('✅ Story refreshed successfully');
                    
                    // 显示成功提示
                    this.showTemporaryMessage('Story refreshed successfully! 🎉');
                } else {
                    throw new Error(result.error || 'Failed to refresh story');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ Error refreshing story:', error);
            this.showTemporaryMessage('Failed to refresh story. Please try again. ❌');
        } finally {
            // 恢复按钮状态
            const refreshBtn = document.querySelector('#refreshStoryBtn');
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<span class="refresh-icon">🔄</span><span class="refresh-text">Refresh Story</span>';
        }
    }

    /**
     * 显示临时消息
     */
    showTemporaryMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'temporary-message';
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2d4a2b;
            color: #c9a961;
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid #c9a961;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }

    /**
     * 下载图片
     */
    async downloadImage() {
        if (!this.imageData) return;

        try {
            console.log('🔭 Detail: Downloading image:', this.imageData.id);
            
            // 调用后端下载API获取图片文件流
            const response = await fetch(`/api/v1/images/${this.imageData.id}/download`);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status} ${response.statusText}`);
            }
            
            // 获取文件blob
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // 创建下载链接
            const link = document.createElement('a');
            link.href = url;
            link.download = `obscura-vision-${this.imageData.id}-detailed.jpg`;
            document.body.appendChild(link);
            link.click();
            
            // 清理URL对象和DOM元素
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            // 显示下载成功提示
            this.showNotification('Image download started', 'success');
            console.log('✅ Detail: Image download completed');
            
        } catch (error) {
            console.error('❌ Detail: Download failed:', error);
            this.showNotification('Download failed: ' + error.message, 'error');
        }
    }

    /**
     * 分享图片
     */
    async shareImage() {
        if (!this.imageData) return;

        const shareData = {
            title: this.imageData.description || 'Environmental Vision - Obscura No.7',
            text: 'Check out this AI-generated environmental prediction!',
            url: window.location.href
        };

        try {
            if (navigator.share) {
                await navigator.share(shareData);
            } else {
                // 备用方案：复制链接到剪贴板
                await navigator.clipboard.writeText(window.location.href);
                this.showNotification('Link copied to clipboard', 'success');
            }
        } catch (error) {
            console.error('Share failed:', error);
            this.showNotification('Share failed', 'error');
        }
    }

    /**
     * 切换全屏模式
     */
    toggleFullscreen() {
        const overlay = document.querySelector('#fullscreenOverlay');
        const fullscreenImage = document.querySelector('#fullscreenImage');
        
        if (!overlay || !this.imageData) return;

        if (fullscreenImage && this.imageData.url) {
            fullscreenImage.src = this.imageData.url;
            fullscreenImage.alt = this.imageData.description || 'Environmental Vision';
        }
        
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
        
        // 阻止背景滚动
        document.body.style.overflow = 'hidden';
    }

    /**
     * 关闭全屏模式
     */
    closeFullscreen() {
        const overlay = document.querySelector('#fullscreenOverlay');
        
        if (overlay) {
            overlay.classList.remove('active');
            overlay.setAttribute('aria-hidden', 'true');
            
            // 恢复背景滚动
            document.body.style.overflow = '';
        }
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        const refreshButton = document.querySelector('.refresh-button');
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.innerHTML = '<span>🔄</span> Refreshing...';
        }

        try {
            await this.loadImageData();
            this.showNotification('Data refreshed successfully', 'success');
        } catch (error) {
            this.showNotification('Failed to refresh data', 'error');
        } finally {
            if (refreshButton) {
                refreshButton.disabled = false;
                refreshButton.innerHTML = '<span>🔄</span> Refresh';
            }
        }
    }

    /**
     * 处理键盘快捷键
     */
    handleKeydown(e) {
        switch (e.key) {
            case 'Escape':
                const overlay = document.querySelector('#fullscreenOverlay');
                if (overlay && overlay.classList.contains('active')) {
                    this.closeFullscreen();
                }
                break;
            case 'f':
            case 'F':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
                break;
            case 'd':
            case 'D':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.downloadImage();
                }
                break;
        }
    }

    /**
     * 初始化懒加载
     */
    initializeLazyLoading() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        }
    }

    /**
     * 调整图表大小
     */
    resizeCharts() {
        if (window.dataVisualization) {
            window.dataVisualization.resizeAllCharts();
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loader = document.querySelector('#pageLoading');
        if (loader) {
            loader.setAttribute('aria-hidden', 'false');
            loader.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loader = document.querySelector('#pageLoading');
        if (loader) {
            loader.setAttribute('aria-hidden', 'true');
            loader.style.display = 'none';
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        const errorContainer = document.querySelector('.error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="error-message">
                    <span class="error-icon">⚠️</span>
                    <span>${message}</span>
                </div>
            `;
            errorContainer.style.display = 'block';
        }
    }

    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">✕</button>
        `;
        
        document.body.appendChild(notification);
        
        // 自动移除通知
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// 全局实例
window.imageDetailPage = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在详情页面
    if (window.location.pathname.includes('/image/')) {
        window.imageDetailPage = new ImageDetailPage();
    }
});

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageDetailPage;
}
