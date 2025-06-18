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
                
                <!-- 蒸汽朋克望远镜镜头容器 -->
                <div class="telescope-container" role="document">
                    <!-- 装饰性齿轮 -->
                    <div class="gear-decoration gear-top-left" aria-hidden="true">⚙️</div>
                    <div class="gear-decoration gear-top-right" aria-hidden="true">⚙️</div>
                    <div class="gear-decoration gear-bottom-left" aria-hidden="true">⚙️</div>
                    <div class="gear-decoration gear-bottom-right" aria-hidden="true">⚙️</div>
                    
                    <!-- 镜头边框 -->
                    <div class="telescope-frame">
                        <!-- 关闭按钮 -->
                        <button class="modal-close" aria-label="Close modal" title="Close (ESC)">
                            <span aria-hidden="true">✕</span>
                        </button>
                        
                        <!-- 导航按钮 -->
                        <button class="modal-nav modal-prev" aria-label="Previous image" title="Previous image (←)">
                            <span aria-hidden="true">‹</span>
                        </button>
                        <button class="modal-nav modal-next" aria-label="Next image" title="Next image (→)">
                            <span aria-hidden="true">›</span>
                        </button>
                        
                        <!-- 镜头内容区域 -->
                        <div class="telescope-lens">
                            <!-- 图片展示区域 -->
                            <div class="image-container">
                                <img id="modal-image" src="" alt="" class="modal-image" />
                                <div class="image-loading" style="display: none;">
                                    <div class="brass-spinner">
                                        <div class="gear-spinner" aria-hidden="true">⚙️</div>
                                    </div>
                                    <p>Loading vision...</p>
                                </div>
                            </div>
                            
                            <!-- 信息面板 -->
                            <div class="info-panel">
                                <h2 id="modal-title" class="image-title">Vision Details</h2>
                                
                                <!-- 预测概要信息 -->
                                <div class="prediction-summary">
                                    <div class="summary-grid">
                                        <div class="summary-item">
                                            <span class="summary-icon" aria-hidden="true">🌡️</span>
                                            <span class="summary-label">Temperature:</span>
                                            <span id="summary-temperature" class="summary-value">--°C</span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-icon" aria-hidden="true">💧</span>
                                            <span class="summary-label">Humidity:</span>
                                            <span id="summary-humidity" class="summary-value">--%</span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-icon" aria-hidden="true">📍</span>
                                            <span class="summary-label">Location:</span>
                                            <span id="summary-location" class="summary-value">--</span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-icon" aria-hidden="true">🔮</span>
                                            <span class="summary-label">Confidence:</span>
                                            <span id="summary-confidence" class="summary-value">--%</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 时间信息 -->
                                <div class="time-info">
                                    <p><strong>Generated:</strong> <span id="summary-time">--</span></p>
                                    <p><strong>AI Model:</strong> <span id="summary-model">DALL-E 3</span></p>
                                </div>
                                
                                <!-- 图片描述 -->
                                <div class="description-section">
                                    <h3>Vision Description</h3>
                                    <p id="image-description" class="image-description">Loading description...</p>
                                </div>
                                
                                <!-- 操作按钮 -->
                                <div class="modal-actions">
                                    <button id="view-details-btn" class="detail-button">
                                        <span class="button-icon" aria-hidden="true">🔍</span>
                                        <span>Detailed Analysis</span>
                                    </button>
                                    <button id="download-btn" class="download-button">
                                        <span class="button-icon" aria-hidden="true">⬇️</span>
                                        <span>Download</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
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
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        if (!this.modal) return;

        // 关闭按钮
        const closeBtn = this.modal.querySelector('.modal-close');
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
            this.hideLoading();
            this.showError('Failed to load image details');
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
        const description = this.modal.querySelector('#image-description');
        if (description) {
            description.textContent = `Error: ${message}`;
            description.style.color = 'var(--amber)';
        }
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
