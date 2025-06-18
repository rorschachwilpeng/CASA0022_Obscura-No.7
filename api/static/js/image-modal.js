/**
 * Obscura No.7 - Image Modal JavaScript
 * 蒸汽朋克风格的图片模态框交互逻辑
 */

class ImageModal {
    constructor() {
        this.modal = null;
        this.currentImageData = null;
        this.isVisible = false;
        this.keydownHandler = null;
        
        this.init();
    }

    /**
     * 初始化模态框
     */
    init() {
        this.createModalHTML();
        this.bindEvents();
        console.log('🔭 Image Modal initialized');
    }

    /**
     * 创建模态框HTML结构
     */
    createModalHTML() {
        const modalHTML = `
            <div id="image-modal" class="image-modal" style="display: none;" aria-hidden="true" role="dialog" aria-labelledby="modal-title">
                <!-- 模态框背景遮罩 -->
                <div class="modal-backdrop" aria-hidden="true"></div>
                
                <!-- 主容器 -->
                <div class="modal-container" role="document">
                    <!-- 关闭按钮 -->
                    <button class="modal-close-btn" aria-label="Close modal" title="Close (ESC)">
                        <span aria-hidden="true">✕</span>
                    </button>
                    
                    <!-- 模态框标题 -->
                    <h1 class="modal-main-title">🔭 Environmental Vision Analysis</h1>
                    
                    <!-- 上半部分：图片展示区 -->
                    <div class="image-section">
                        <div class="telescope-viewer">
                            <!-- 装饰性齿轮 -->
                            <div class="gear-decoration gear-top-left" aria-hidden="true">⚙️</div>
                            <div class="gear-decoration gear-top-right" aria-hidden="true">⚙️</div>
                            <div class="gear-decoration gear-bottom-left" aria-hidden="true">⚙️</div>
                            <div class="gear-decoration gear-bottom-right" aria-hidden="true">⚙️</div>
                            
                            <!-- 圆形图片容器 -->
                            <div class="image-frame">
                                <img id="modal-image" src="" alt="" class="vision-image" />
                                <div class="image-loading" style="display: none;">
                                    <div class="brass-spinner">
                                        <div class="gear-spinner" aria-hidden="true">⚙️</div>
                                    </div>
                                    <p>Loading vision...</p>
                                </div>
                            </div>
                            
                            <!-- 图片标题 -->
                            <h2 id="modal-title" class="vision-title">Vision Details</h2>
                        </div>
                    </div>
                    
                    <!-- 下半部分：信息面板 -->
                    <div class="info-section">
                        <div class="info-panel-container">
                            <h3 class="section-title">📊 Prediction Data & Analysis</h3>
                            
                            <!-- 核心预测数据 -->
                            <div class="prediction-grid">
                                <div class="data-group">
                                    <h4 class="group-title">🌡️ Environmental Conditions</h4>
                                    <div class="data-items">
                                        <div class="data-item">
                                            <span class="data-icon">🌡️</span>
                                            <span class="data-label">Temperature:</span>
                                            <span id="summary-temperature" class="data-value">--°C</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">💧</span>
                                            <span class="data-label">Humidity:</span>
                                            <span id="summary-humidity" class="data-value">--%</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">📍</span>
                                            <span class="data-label">Location:</span>
                                            <span id="summary-location" class="data-value">--</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">🔮</span>
                                            <span class="data-label">Confidence:</span>
                                            <span id="summary-confidence" class="data-value">--%</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="data-group">
                                    <h4 class="group-title">🤖 Generation Info</h4>
                                    <div class="data-items">
                                        <div class="data-item">
                                            <span class="data-icon">📅</span>
                                            <span class="data-label">Generated:</span>
                                            <span id="summary-time" class="data-value">--</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">🧠</span>
                                            <span class="data-label">AI Model:</span>
                                            <span id="summary-model" class="data-value">DALL-E 3</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">🔢</span>
                                            <span class="data-label">Prediction ID:</span>
                                            <span id="prediction-id" class="data-value">--</span>
                                        </div>
                                        <div class="data-item">
                                            <span class="data-icon">⏱️</span>
                                            <span class="data-label">Process Time:</span>
                                            <span id="processing-time" class="data-value">--</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 描述部分 -->
                            <div class="description-group">
                                <h4 class="group-title">📝 Vision Description</h4>
                                <p id="image-description" class="vision-description">Loading description...</p>
                            </div>
                            
                            <!-- 操作按钮 -->
                            <div class="action-group">
                                <h4 class="group-title">🔧 Available Actions</h4>
                                <div class="action-buttons">
                                    <button id="view-details-btn" class="action-button primary">
                                        <span class="button-icon">🔍</span>
                                        <div class="button-content">
                                            <span class="button-label">Detailed Analysis</span>
                                            <span class="button-subtitle">View comprehensive analysis</span>
                                        </div>
                                    </button>
                                    <button id="download-btn" class="action-button secondary">
                                        <span class="button-icon">⬇️</span>
                                        <div class="button-content">
                                            <span class="button-label">Download Vision</span>
                                            <span class="button-subtitle">Save to your device</span>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 导航按钮 -->
                    <button class="modal-nav modal-prev" aria-label="Previous image" title="Previous image (←)">
                        <span aria-hidden="true">‹</span>
                    </button>
                    <button class="modal-nav modal-next" aria-label="Next image" title="Next image (→)">
                        <span aria-hidden="true">›</span>
                    </button>
                </div>
                
                <!-- 加载状态指示器 -->
                <div class="modal-loading" style="display: none;">
                    <div class="loading-content">
                        <div class="brass-spinner">
                            <div class="gear-spinner" aria-hidden="true">⚙️</div>
                        </div>
                        <p>Accessing temporal archive...</p>
                    </div>
                </div>
            </div>
        `;
        
        // 插入到页面
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('image-modal');
        
        // 添加Tab样式
        this.addTabStyles();
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        if (!this.modal) return;

        // 关闭按钮
        const closeBtn = this.modal.querySelector('.modal-close-btn');
        closeBtn?.addEventListener('click', () => this.hide());

        // 背景点击关闭
        const backdrop = this.modal.querySelector('.modal-backdrop');
        backdrop?.addEventListener('click', () => this.hide());

        // 导航按钮
        const prevBtn = this.modal.querySelector('.modal-prev');
        const nextBtn = this.modal.querySelector('.modal-next');
        prevBtn?.addEventListener('click', () => this.navigatePrevious());
        nextBtn?.addEventListener('click', () => this.navigateNext());

        // 详细分析按钮
        const detailBtn = this.modal.querySelector('#view-details-btn');
        detailBtn?.addEventListener('click', () => this.openDetailPage());

        // 下载按钮
        const downloadBtn = this.modal.querySelector('#download-btn');
        downloadBtn?.addEventListener('click', () => this.downloadImage());



        // 键盘导航
        this.keydownHandler = (e) => this.handleKeydown(e);
    }

    /**
     * 显示模态框
     * @param {Object} imageData - 图片数据
     * @param {Array} galleryImages - 画廊中所有图片（用于导航）
     * @param {number} currentIndex - 当前图片索引
     */
    async show(imageData, galleryImages = [], currentIndex = 0) {
        if (!this.modal || !imageData) return;

        this.currentImageData = imageData;
        this.galleryImages = galleryImages;
        this.currentIndex = currentIndex;

        // 显示加载状态
        this.showLoading();
        
        // 显示模态框
        this.modal.style.display = 'flex';
        this.modal.setAttribute('aria-hidden', 'false');
        this.isVisible = true;

        // 添加键盘监听
        document.addEventListener('keydown', this.keydownHandler);
        
        // 禁用页面滚动
        document.body.style.overflow = 'hidden';

        // 获取完整图片数据
        try {
            const fullData = await this.fetchImageData(imageData.id);
            await this.populateModal(fullData);
            this.hideLoading();
            
            // 动画效果
            requestAnimationFrame(() => {
                this.modal.classList.add('modal-visible');
            });
            
        } catch (error) {
            console.error('Error loading image data:', error);
            console.warn('Using basic image data as fallback');
            
            // Fallback: 使用基础图片数据填充模态框
            await this.populateModal({ image: imageData });
            this.hideLoading();
            
            // 动画效果
            requestAnimationFrame(() => {
                this.modal.classList.add('modal-visible');
            });
        }
    }

    /**
     * 隐藏模态框
     */
    hide() {
        if (!this.modal || !this.isVisible) return;

        // 移除动画类
        this.modal.classList.remove('modal-visible');
        
        // 延迟隐藏以完成动画
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.setAttribute('aria-hidden', 'true');
            this.isVisible = false;
            
            // 移除键盘监听
            document.removeEventListener('keydown', this.keydownHandler);
            
            // 恢复页面滚动
            document.body.style.overflow = '';
            
            // 清理数据
            this.currentImageData = null;
            this.galleryImages = [];
            this.currentIndex = 0;
        }, 300);
    }

    /**
     * 获取图片详细数据
     * @param {number} imageId - 图片ID
     */
    async fetchImageData(imageId) {
        const response = await fetch(`/api/v1/images/${imageId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * 填充模态框内容
     * @param {Object} data - 图片完整数据
     */
    async populateModal(data) {
        console.log('Populating modal with data:', data);
        
        // 处理不同的数据结构
        const image = data.image || data;
        const prediction = data.prediction || {};

        // 设置图片
        const modalImage = this.modal.querySelector('#modal-image');
        if (modalImage && image.url) {
            modalImage.src = image.url;
            modalImage.alt = image.description || 'AI Generated Environmental Vision';
            
            // 图片加载处理
            try {
                await new Promise((resolve, reject) => {
                    modalImage.onload = resolve;
                    modalImage.onerror = reject;
                    // 设置超时
                    setTimeout(reject, 10000);
                });
            } catch (error) {
                console.warn('Image loading timeout or error:', error);
            }
        }

        // 填充基本信息
        const titleElement = this.modal.querySelector('#modal-title');
        if (titleElement) {
            titleElement.textContent = image.description || 'Environmental Vision';
        }
        
        // 填充预测数据（从prediction或input_data中提取）
        const resultData = prediction.result_data || {};
        const inputData = prediction.input_data || {};
        
        // 温度信息
        const tempElement = this.modal.querySelector('#summary-temperature');
        if (tempElement) {
            const temp = resultData.temperature || inputData.temperature || prediction.temperature;
            tempElement.textContent = temp ? `${Math.round(temp)}°C` : '--°C';
        }
        
        // 湿度信息
        const humidityElement = this.modal.querySelector('#summary-humidity');
        if (humidityElement) {
            const humidity = resultData.humidity || inputData.humidity || prediction.humidity;
            humidityElement.textContent = humidity ? `${Math.round(humidity)}%` : '--%';
        }
        
        // 位置信息
        const locationElement = this.modal.querySelector('#summary-location');
        if (locationElement) {
            const location = prediction.location || inputData.location || 'Global';
            locationElement.textContent = location;
        }
        
        // 置信度信息
        const confidenceElement = this.modal.querySelector('#summary-confidence');
        if (confidenceElement) {
            const confidence = resultData.confidence || prediction.confidence || 0.85;
            confidenceElement.textContent = `${Math.round(confidence * 100)}%`;
        }
        
        // 时间信息
        const timeElement = this.modal.querySelector('#summary-time');
        if (timeElement) {
            const date = new Date(image.created_at);
            timeElement.textContent = date.toLocaleString();
        }
        
        // 描述信息
        const descElement = this.modal.querySelector('#image-description');
        if (descElement) {
            descElement.textContent = image.description || 
                'A glimpse into a possible environmental future, generated by AI based on predictive environmental data.';
        }

        // 更新导航按钮状态
        this.updateNavigationButtons();
        
        // 设置详细分析按钮
        const detailBtn = this.modal.querySelector('#view-details-btn');
        if (detailBtn) {
            detailBtn.dataset.imageId = image.id;
        }
        
        // 填充技术信息
        const predictionIdElement = this.modal.querySelector('#prediction-id');
        if (predictionIdElement) {
            predictionIdElement.textContent = image.prediction_id || '--';
        }
        
        const processingTimeElement = this.modal.querySelector('#processing-time');
        if (processingTimeElement) {
            // 简单的处理时间估算
            processingTimeElement.textContent = '~2-3 minutes';
        }
    }

    /**
     * 更新导航按钮状态
     */
    updateNavigationButtons() {
        const prevBtn = this.modal.querySelector('.modal-prev');
        const nextBtn = this.modal.querySelector('.modal-next');
        
        if (this.galleryImages.length <= 1) {
            prevBtn.style.display = 'none';
            nextBtn.style.display = 'none';
        } else {
            prevBtn.style.display = 'block';
            nextBtn.style.display = 'block';
            
            prevBtn.disabled = this.currentIndex === 0;
            nextBtn.disabled = this.currentIndex === this.galleryImages.length - 1;
        }
    }

    /**
     * 导航到上一张图片
     */
    async navigatePrevious() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            const imageData = this.galleryImages[this.currentIndex];
            await this.show(imageData, this.galleryImages, this.currentIndex);
        }
    }

    /**
     * 导航到下一张图片
     */
    async navigateNext() {
        if (this.currentIndex < this.galleryImages.length - 1) {
            this.currentIndex++;
            const imageData = this.galleryImages[this.currentIndex];
            await this.show(imageData, this.galleryImages, this.currentIndex);
        }
    }

    /**
     * 打开详细分析页面
     */
    openDetailPage() {
        if (this.currentImageData) {
            const imageId = this.currentImageData.id;
            window.location.href = `/image/${imageId}`;
        }
    }

    /**
     * 下载图片
     */
    async downloadImage() {
        if (!this.currentImageData) return;

        try {
            const image = this.modal.querySelector('#modal-image');
            const link = document.createElement('a');
            link.href = image.src;
            link.download = `obscura-vision-${this.currentImageData.id}.jpg`;
            link.target = '_blank';
            link.click();
        } catch (error) {
            console.error('Download failed:', error);
        }
    }

    /**
     * 处理键盘事件
     * @param {KeyboardEvent} e - 键盘事件
     */
    handleKeydown(e) {
        if (!this.isVisible) return;

        switch (e.key) {
            case 'Escape':
                e.preventDefault();
                this.hide();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.navigatePrevious();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.navigateNext();
                break;
            case 'Enter':
                if (e.target.classList.contains('detail-button')) {
                    e.preventDefault();
                    this.openDetailPage();
                }
                break;
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loading = this.modal.querySelector('.modal-loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loading = this.modal.querySelector('.modal-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    showError(message) {
        console.error('Modal error:', message);
        
        // 显示错误通知
        if (window.showNotification) {
            window.showNotification(message, 'error');
        }
        
        // 隐藏模态框
        this.hide();
    }

    /**
     * 添加模态框样式
     */
    addTabStyles() {
        const modalStyles = `
            <style id="modal-tab-styles">
                /* CSS变量定义 */
                :root {
                    --brass: #B8860B;
                    --brass-gradient: linear-gradient(45deg, #B8860B, #DAA520);
                    --brass-dark: #8B7D3A;
                    --copper: #B87333;
                    --copper-gradient: linear-gradient(45deg, #B87333, #CD7F32);
                    --copper-light: #D2B48C;
                    --amber: #FFB347;
                    --coal: #2c2c2c;
                }
                
                /* 模态框基础样式 */
                .image-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-backdrop {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(5px);
                }
                
                .modal-container {
                    position: relative;
                    width: 90vw;
                    max-width: 1200px;
                    height: 90vh;
                    display: flex;
                    flex-direction: column;
                    background: linear-gradient(135deg, #2c2c2c, #1a1a1a);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                }
                
                /* 关闭按钮 */
                .modal-close-btn {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    background: var(--brass-gradient);
                    border: 3px solid var(--brass-dark);
                    color: var(--coal);
                    font-size: 1.8rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    z-index: 100;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-close-btn:hover {
                    background: var(--copper-gradient);
                    transform: scale(1.1) rotate(90deg);
                    box-shadow: 0 5px 15px rgba(255, 107, 53, 0.4);
                }
                
                /* 主标题 */
                .modal-main-title {
                    text-align: center;
                    color: var(--amber);
                    font-size: 2rem;
                    font-weight: bold;
                    margin: 20px 0;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                    letter-spacing: 1px;
                }
                
                /* 上半部分：图片展示区 */
                .image-section {
                    flex: 0 0 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: radial-gradient(circle, #3a3a3a, #2c2c2c);
                    position: relative;
                    padding: 20px;
                }
                
                .telescope-viewer {
                    position: relative;
                    width: 400px;
                    height: 400px;
                }
                
                /* 装饰齿轮 */
                .gear-decoration {
                    position: absolute;
                    font-size: 2rem;
                    color: var(--brass);
                    animation: rotate 20s linear infinite;
                    opacity: 0.6;
                }
                
                .gear-top-left { top: -10px; left: -10px; }
                .gear-top-right { top: -10px; right: -10px; animation-direction: reverse; }
                .gear-bottom-left { bottom: -10px; left: -10px; animation-direction: reverse; }
                .gear-bottom-right { bottom: -10px; right: -10px; }
                
                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                
                /* 圆形图片框 */
                .image-frame {
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    border: 8px solid var(--brass);
                    overflow: hidden;
                    box-shadow: 
                        0 0 30px rgba(255, 179, 71, 0.3),
                        inset 0 0 20px rgba(0, 0, 0, 0.3);
                    position: relative;
                }
                
                .vision-image {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 50%;
                }
                
                .vision-title {
                    position: absolute;
                    bottom: -50px;
                    left: 50%;
                    transform: translateX(-50%);
                    color: var(--amber);
                    font-size: 1.5rem;
                    font-weight: bold;
                    text-align: center;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
                    margin: 0;
                }
                
                /* 下半部分：信息面板 */
                .info-section {
                    flex: 0 0 50%;
                    background: linear-gradient(135deg, var(--brass), var(--copper));
                    padding: 30px;
                    overflow-y: auto;
                }
                
                .info-panel-container {
                    background: rgba(44, 44, 44, 0.9);
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.3);
                }
                
                .section-title {
                    color: var(--amber);
                    font-size: 1.5rem;
                    font-weight: bold;
                    margin-bottom: 20px;
                    text-align: center;
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
                }
                
                /* 预测数据网格 */
                .prediction-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 25px;
                }
                
                .data-group {
                    background: rgba(255, 179, 71, 0.1);
                    border-radius: 10px;
                    padding: 15px;
                    border: 2px solid var(--brass-dark);
                }
                
                .group-title {
                    color: var(--amber);
                    font-size: 1.1rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                    text-align: center;
                }
                
                .data-items {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                
                .data-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 5px;
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 5px;
                }
                
                .data-icon {
                    font-size: 1.2rem;
                }
                
                .data-label {
                    color: var(--copper-light);
                    font-weight: bold;
                    flex: 1;
                }
                
                .data-value {
                    color: var(--amber);
                    font-weight: bold;
                }
                
                /* 描述组 */
                .description-group {
                    background: rgba(255, 179, 71, 0.1);
                    border-radius: 10px;
                    padding: 15px;
                    border: 2px solid var(--brass-dark);
                    margin-bottom: 20px;
                }
                
                .vision-description {
                    color: var(--copper-light);
                    line-height: 1.6;
                    margin: 10px 0 0 0;
                    font-style: italic;
                }
                
                /* 操作按钮组 */
                .action-group {
                    background: rgba(255, 179, 71, 0.1);
                    border-radius: 10px;
                    padding: 15px;
                    border: 2px solid var(--brass-dark);
                }
                
                .action-buttons {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                }
                
                .action-button {
                    flex: 1;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid var(--brass-dark);
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: bold;
                }
                
                .action-button.primary {
                    background: var(--brass-gradient);
                    color: var(--coal);
                }
                
                .action-button.secondary {
                    background: var(--copper-gradient);
                    color: var(--coal);
                }
                
                .action-button:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                }
                
                .button-icon {
                    font-size: 1.5rem;
                }
                
                .button-content {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .button-label {
                    font-size: 1rem;
                    font-weight: bold;
                }
                
                .button-subtitle {
                    font-size: 0.8rem;
                    opacity: 0.8;
                    font-weight: normal;
                }
                
                /* 导航按钮 */
                .modal-nav {
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: var(--brass-gradient);
                    border: 3px solid var(--brass-dark);
                    color: var(--coal);
                    font-size: 2rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    z-index: 50;
                }
                
                .modal-prev { left: 20px; }
                .modal-next { right: 20px; }
                
                .modal-nav:hover {
                    background: var(--copper-gradient);
                    transform: translateY(-50%) scale(1.1);
                }
                
                .modal-nav:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                /* 响应式设计 */
                @media (max-width: 768px) {
                    .modal-container {
                        width: 95vw;
                        height: 95vh;
                    }
                    
                    .prediction-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .action-buttons {
                        flex-direction: column;
                    }
                    
                    .telescope-viewer {
                        width: 300px;
                        height: 300px;
                    }
                }
            </style>
        `;
        
        // 移除旧样式
        const existingStyles = document.getElementById('modal-tab-styles');
        if (existingStyles) {
            existingStyles.remove();
        }
        
        // 添加新样式
        document.head.insertAdjacentHTML('beforeend', modalStyles);
    }
}

// 全局实例和类
window.ImageModal = ImageModal;
window.imageModal = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.imageModal = new ImageModal();
    
    // 为了向后兼容，也设置为ImageModal
    window.ImageModal.instance = window.imageModal;
    window.ImageModal.show = (imageData, galleryImages, currentIndex) => {
        return window.imageModal.show(imageData, galleryImages, currentIndex);
    };
});

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageModal;
}
