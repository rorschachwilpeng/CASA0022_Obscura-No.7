/**
 * Obscura No.7 - Image Detail Page JavaScript
 * 图片详情页的交互逻辑和数据处理
 */

class ImageDetailPage {
    constructor() {
        this.imageId = null;
        this.imageData = null;
        this.predictionData = null;
        this.relatedImages = [];
        
        this.init();
    }

    /**
     * 初始化详情页
     */
    init() {
        this.extractImageId();
        this.bindEvents();
        this.loadImageData();
        console.log('🔭 Image Detail Page initialized');
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
        // 返回按钮
        const backButton = document.querySelector('.back-button');
        backButton?.addEventListener('click', () => this.goBack());

        // 下载按钮
        const downloadButton = document.querySelector('.download-button');
        downloadButton?.addEventListener('click', () => this.downloadImage());

        // 分享按钮
        const shareButton = document.querySelector('.share-button');
        shareButton?.addEventListener('click', () => this.shareImage());

        // 全屏查看按钮
        const fullscreenButton = document.querySelector('.fullscreen-button');
        fullscreenButton?.addEventListener('click', () => this.toggleFullscreen());

        // 刷新数据按钮
        const refreshButton = document.querySelector('.refresh-button');
        refreshButton?.addEventListener('click', () => this.refreshData());

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
        // 主图片
        const mainImage = document.querySelector('#main-image');
        if (mainImage && this.imageData.url) {
            mainImage.src = this.imageData.url;
            mainImage.alt = this.imageData.description || 'AI Generated Environmental Vision';
        }

        // 图片描述
        const description = document.querySelector('#image-description');
        if (description) {
            description.textContent = this.imageData.description || 
                'A glimpse into a possible environmental future, generated by AI based on predictive environmental data.';
        }

        // 创建时间
        const createdTime = document.querySelector('#created-time');
        if (createdTime && this.imageData.created_at) {
            const date = new Date(this.imageData.created_at);
            createdTime.textContent = date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        // 图片ID
        const imageId = document.querySelector('#image-id');
        if (imageId) {
            imageId.textContent = `#${this.imageData.id}`;
        }
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
     * 填充SHAP分析数据
     */
    populateSHAPAnalysis() {
        if (!this.shapAnalysisData || !this.shapAnalysisData.shap_analysis) {
            console.log('No SHAP analysis data available');
            // 隐藏SHAP分析部分
            const shapSection = document.querySelector('.shap-analysis-section');
            if (shapSection) {
                shapSection.style.display = 'none';
            }
            return;
        }

        const shapData = this.shapAnalysisData.shap_analysis;
        
        // 填充三个维度评分（简化版）
        this.populateSimplifiedScores(shapData);
        
        // 填充AI故事（新格式）
        this.populateAIStory(shapData);
        
        // 准备圆形打包图数据（稍后实现）
        this.preparePackChartData(shapData);
        
        // 🎯 存储SHAP数据供bubble chart使用
        window.currentShapData = {
            final_score: shapData.final_score || 0.69,
            climate_score: shapData.climate_score || 0.72,
            geographic_score: shapData.geographic_score || 0.69,
            economic_score: shapData.economic_score || 0.66,
            city: shapData.city || "Unknown Location",
            coordinates: shapData.coordinates || { latitude: 51.5074, longitude: -0.1278 },
            shap_analysis: {
                feature_importance: shapData.shap_analysis?.feature_importance || {}
            },
            ai_story: shapData.ai_story || {}
        };
        
        // 🎯 触发bubble chart渲染
        this.renderBubbleChart();
        
        console.log('🧠 SHAP analysis populated successfully');
    }
    
    /**
     * 渲染SHAP Bubble Chart
     */
    renderBubbleChart() {
        try {
            console.log('🎯 Attempting to render bubble chart...');
            
            // 检查bubble chart是否可用
            if (typeof window.shapBubbleChart === 'undefined') {
                console.log('⏳ Bubble chart not yet initialized, waiting...');
                // 延迟重试
                setTimeout(() => this.renderBubbleChart(), 500);
                return;
            }
            
            // 检查数据是否可用
            if (!window.currentShapData) {
                console.warn('⚠️ No SHAP data available for bubble chart');
                return;
            }
            
            console.log('🎯 Rendering bubble chart with data:', window.currentShapData);
            
            // 隐藏loading，显示图表
            const loading = document.getElementById('bubbleChartLoading');
            const chart = document.getElementById('shapBubbleChart');
            
            if (loading) {
                loading.style.display = 'none';
            }
            if (chart) {
                chart.style.display = 'block';
            }
            
            // 渲染bubble chart
            window.shapBubbleChart.render(window.currentShapData);
            console.log('✅ Bubble chart rendered successfully');
            
        } catch (error) {
            console.error('❌ Error rendering bubble chart:', error);
            
            // 显示错误消息
            const loading = document.getElementById('bubbleChartLoading');
            if (loading) {
                loading.innerHTML = '<div class="shap-bubble-error">Visualization temporarily unavailable</div>';
            }
        }
    }

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
     * 填充简化的三维度评分
     */
    populateSimplifiedScores(shapData) {
        // 气候评分
        const climateScore = document.querySelector('#climateScore');
        if (climateScore && shapData.climate_score !== undefined) {
            climateScore.textContent = `${(shapData.climate_score * 100).toFixed(1)}%`;
        }

        // 地理评分
        const geographicScore = document.querySelector('#geographicScore');
        if (geographicScore && shapData.geographic_score !== undefined) {
            geographicScore.textContent = `${(shapData.geographic_score * 100).toFixed(1)}%`;
        }

        // 经济评分
        const economicScore = document.querySelector('#economicScore');
        if (economicScore && shapData.economic_score !== undefined) {
            economicScore.textContent = `${(shapData.economic_score * 100).toFixed(1)}%`;
        }

        console.log('✅ Simplified scores populated');
    }

    /**
     * 准备圆形打包图数据
     */
    preparePackChartData(shapData) {
        if (!shapData.shap_analysis || !shapData.shap_analysis.feature_importance) {
            console.log('No feature importance data for pack chart');
            return;
        }

        const features = shapData.shap_analysis.feature_importance;
        
        // 构建层次化数据结构
        const packData = {
            name: "Environmental Impact",
            value: shapData.final_score || 0.7,
            children: [
                {
                    name: "Climate",
                    value: shapData.climate_score || 0.7,
                    children: []
                },
                {
                    name: "Geographic", 
                    value: shapData.geographic_score || 0.7,
                    children: []
                },
                {
                    name: "Economic",
                    value: shapData.economic_score || 0.7,
                    children: []
                }
            ]
        };

        // 将特征分配到相应的维度
        for (const [feature, importance] of Object.entries(features)) {
            const featureNode = {
                name: this.formatFeatureName(feature),
                value: Math.abs(importance),
                impact: importance
            };

            // 简单的特征分类逻辑
            if (feature.includes('temperature') || feature.includes('humidity') || feature.includes('climate')) {
                packData.children[0].children.push(featureNode);
            } else if (feature.includes('location') || feature.includes('pressure') || feature.includes('geographic')) {
                packData.children[1].children.push(featureNode);
            } else {
                packData.children[2].children.push(featureNode);
            }
        }

        // 存储数据供后续可视化使用
        window.currentPackData = packData;
        console.log('✅ Pack chart data prepared:', packData);

        // 初始化并渲染圆形打包图
        this.initializePackChart(packData);

        // 隐藏loading，显示控制按钮
        this.showPackChartControls();
    }

    /**
     * 初始化并渲染圆形打包图
     */
    initializePackChart(data) {
        if (typeof PackChart === 'undefined') {
            console.error('❌ PackChart component not loaded');
            return;
        }

        try {
            // 创建圆形打包图实例
            if (!window.packChartInstance) {
                window.packChartInstance = new PackChart('packChart', {
                    width: 600,
                    height: 500
                });
            }

            // 渲染数据
            window.packChartInstance.render(data);
            console.log('✅ Pack chart rendered with SHAP data');

        } catch (error) {
            console.error('❌ Error initializing pack chart:', error);
            this.showPackChartError();
        }
    }

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
     * 显示圆形打包图错误
     */
    showPackChartError() {
        const loading = document.querySelector('#packChartLoading');
        if (loading) {
            loading.innerHTML = `
                <div class="chart-error">
                    <span aria-hidden="true">❌</span>
                    <p>Visualization loading failed</p>
                </div>
            `;
        }
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
     * 下载图片
     */
    async downloadImage() {
        if (!this.imageData) return;

        try {
            const link = document.createElement('a');
            link.href = this.imageData.url;
            link.download = `obscura-vision-${this.imageData.id}-detailed.jpg`;
            link.target = '_blank';
            link.click();

            // 显示下载成功提示
            this.showNotification('Image download started', 'success');
        } catch (error) {
            console.error('Download failed:', error);
            this.showNotification('Download failed', 'error');
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
        const mainImage = document.querySelector('#main-image');
        if (!mainImage) return;

        if (!document.fullscreenElement) {
            mainImage.requestFullscreen().catch(err => {
                console.error('Fullscreen failed:', err);
            });
        } else {
            document.exitFullscreen();
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
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                } else {
                    this.goBack();
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
            case 's':
            case 'S':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.shareImage();
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
        const loader = document.querySelector('.page-loader');
        if (loader) {
            loader.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loader = document.querySelector('.page-loader');
        if (loader) {
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
