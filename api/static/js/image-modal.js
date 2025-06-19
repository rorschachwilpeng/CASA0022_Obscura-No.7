/**
 * Obscura No.7 - Image Modal JavaScript
 * 蒸汽朋克风格的图片模态框交互逻辑 - 重新设计为上下分离布局
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
        this.applyUIOptimizations();
        console.log('🔭 Image Modal initialized with optimized layout');
    }

    /**
     * 创建模态框HTML结构 - 新的上下分离布局 + UI优化
     */
    createModalHTML() {
        const modalHTML = `
            <div id="image-modal" class="image-modal" style="display: none;" aria-hidden="true" role="dialog" aria-labelledby="modal-title">
                <!-- 模态框背景遮罩 -->
                <div class="modal-backdrop" aria-hidden="true"></div>
                
                <!-- 新的模态框容器 - 垂直布局 -->
                <div class="new-modal-container" role="document">
                    <!-- 优化的外部关闭按钮 -->
                    <button class="modal-close" aria-label="Close modal" title="Close (ESC)">
                        <span aria-hidden="true">✕</span>
                    </button>
                    
                    <!-- 上部分：望远镜圆形区域 -->
                    <div class="telescope-section">
                        <!-- 装饰性齿轮 -->
                        <div class="gear-decoration gear-top-left" aria-hidden="true">⚙️</div>
                        <div class="gear-decoration gear-top-right" aria-hidden="true">⚙️</div>
                        <div class="gear-decoration gear-bottom-left" aria-hidden="true">⚙️</div>
                        <div class="gear-decoration gear-bottom-right" aria-hidden="true">⚙️</div>
                        
                        <!-- 导航按钮 -->
                        <button class="modal-nav modal-prev" aria-label="Previous image" title="Previous image (←)">
                            <span aria-hidden="true">‹</span>
                        </button>
                        <button class="modal-nav modal-next" aria-label="Next image" title="Next image (→)">
                            <span aria-hidden="true">›</span>
                        </button>
                        
                        <!-- 望远镜框架 -->
                        <div class="telescope-frame">
                            <!-- 望远镜镜头（只包含图片） -->
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
                            </div>
                        </div>
                    </div>
                    
                    <!-- 连接线装饰 -->
                    <div class="connection-line"></div>
                    
                    <!-- 下部分：数据矩形区域 -->
                    <div class="data-section">
                        <!-- 信息面板 -->
                        <div class="info-panel">
                            <h2 id="modal-title" class="image-title">Environmental Vision</h2>
                            
                            <!-- 主要内容区：左右分栏布局 -->
                            <div class="main-content-grid">
                                <!-- 左侧：数据列表 -->
                                <div class="data-list-section">
                                    <div class="summary-item">
                                        <span class="summary-icon" aria-hidden="true">🌡️</span>
                                        <div class="data-content">
                                            <div class="summary-label">Temperature</div>
                                            <div id="summary-temperature" class="summary-value">--°C</div>
                                        </div>
                                    </div>
                                    <div class="summary-item">
                                        <span class="summary-icon" aria-hidden="true">💧</span>
                                        <div class="data-content">
                                            <div class="summary-label">Humidity</div>
                                            <div id="summary-humidity" class="summary-value">--%</div>
                                        </div>
                                    </div>
                                    <div class="summary-item">
                                        <span class="summary-icon" aria-hidden="true">📍</span>
                                        <div class="data-content">
                                            <div class="summary-label">Location</div>
                                            <div id="summary-location" class="summary-value">--</div>
                                        </div>
                                    </div>
                                    <div class="summary-item">
                                        <span class="summary-icon" aria-hidden="true">🔮</span>
                                        <div class="data-content">
                                            <div class="summary-label">Confidence</div>
                                            <div id="summary-confidence" class="summary-value">--%</div>
                                        </div>
                                    </div>
                                    
                                    <!-- 生成时间 -->
                                    <div class="time-info">
                                        <p><strong>Generated:</strong> <span id="summary-time">--</span></p>
                                    </div>
                                </div>
                                
                                <!-- 右侧：操作按钮 -->
                                <div class="actions-section">
                                    <button id="view-details-btn" class="detail-button">
                                        <span class="button-icon" aria-hidden="true">🔍</span>
                                        <span class="button-text">Detailed<br/>Analysis</span>
                                    </button>
                                    <button id="download-btn" class="download-button">
                                        <span class="button-icon" aria-hidden="true">💾</span>
                                        <span class="button-text">Download<br/>Image</span>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- 底部：描述区域 -->
                            <div class="description-section">
                                <h3>Vision Description</h3>
                                <div id="image-description" class="image-description">Loading description...</div>
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
     * 应用UI优化设置
     */
    applyUIOptimizations() {
        if (!this.modal) return;

        // 应用优化的CSS样式
        const telescopeFrame = this.modal.querySelector('.telescope-frame');
        const telescopeLens = this.modal.querySelector('.telescope-lens');
        const modalContainer = this.modal.querySelector('.new-modal-container');
        const connectionLine = this.modal.querySelector('.connection-line');

        // 望远镜尺寸优化
        if (telescopeFrame && telescopeLens) {
            telescopeFrame.style.width = '400px';
            telescopeFrame.style.height = '400px';
            telescopeLens.style.width = '340px';
            telescopeLens.style.height = '340px';
        }

        // 容器布局优化
        if (modalContainer) {
            modalContainer.style.gap = '15px';
            modalContainer.style.maxHeight = '90vh';
            modalContainer.style.justifyContent = 'flex-start';
            modalContainer.style.paddingTop = '20px';
            modalContainer.style.position = 'relative';
        }

        if (connectionLine) {
            connectionLine.style.height = '20px';
        }

        // 齿轮装饰优化
        const gears = this.modal.querySelectorAll('.gear-decoration');
        gears.forEach(gear => {
            gear.style.fontSize = '2.5rem';
            if (gear.classList.contains('gear-top-left')) {
                gear.style.top = '-40px';
                gear.style.left = '-40px';
            }
            if (gear.classList.contains('gear-top-right')) {
                gear.style.top = '-40px';
                gear.style.right = '-40px';
            }
            if (gear.classList.contains('gear-bottom-left')) {
                gear.style.bottom = '-40px';
                gear.style.left = '-40px';
            }
            if (gear.classList.contains('gear-bottom-right')) {
                gear.style.bottom = '-40px';
                gear.style.right = '-40px';
            }
        });

        // 关闭按钮优化
        const closeBtn = this.modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.style.position = 'absolute';
            closeBtn.style.top = '10px';
            closeBtn.style.right = '10px';
            closeBtn.style.width = '45px';
            closeBtn.style.height = '45px';
            closeBtn.style.border = '3px solid var(--amber)';
            closeBtn.style.background = 'rgba(28, 28, 28, 0.95)';
            closeBtn.style.fontSize = '1.4rem';
            closeBtn.style.zIndex = '10003';
            closeBtn.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 191, 0, 0.3)';
        }

        // 数据区域优化
        const dataSection = this.modal.querySelector('.data-section');
        if (dataSection) {
            dataSection.style.width = '650px';
            dataSection.style.maxWidth = '85vw';
            dataSection.style.padding = '25px';
            dataSection.style.position = 'relative';
            dataSection.style.overflowY = 'auto';
            dataSection.style.maxHeight = 'none';
        }

        console.log('✅ UI optimizations applied to modal');
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
        console.log('🔭 Modal: show() called with new layout:', {
            imageData: imageData,
            galleryImagesCount: galleryImages.length,
            currentIndex: currentIndex
        });
        
        if (!this.modal || !imageData) {
            console.error('❌ Modal: Missing modal or imageData', {
                hasModal: !!this.modal,
                hasImageData: !!imageData
            });
            return;
        }

        this.currentImageData = imageData;
        this.galleryImages = galleryImages;
        this.currentIndex = currentIndex;
        
        // 显示模态框
        this.modal.style.display = 'flex';
        this.modal.setAttribute('aria-hidden', 'false');
        
        // 显示加载状态
        this.showLoading();
        
        try {
            // 获取详细图片数据
            const detailData = await this.fetchImageData(imageData.id);
            
            // 填充模态框内容
            await this.populateModal(detailData);
            
            // 更新导航按钮状态
            this.updateNavigationButtons();
            
            // 隐藏加载状态
            this.hideLoading();
            
            // 添加可见类以触发动画
            setTimeout(() => {
                this.modal.classList.add('modal-visible');
                this.isVisible = true;
            }, 50);
            
            // 绑定键盘事件
            document.addEventListener('keydown', this.keydownHandler);
            
            // 焦点管理
            const closeButton = this.modal.querySelector('.modal-close');
            closeButton?.focus();
            
        } catch (error) {
            console.error('❌ Modal: Error loading image data:', error);
            this.hideLoading();
            this.showError('Failed to load image details');
        }
    }

    /**
     * 隐藏模态框
     */
    hide() {
        if (!this.modal || !this.isVisible) return;

        console.log('🔭 Modal: Hiding modal');
        
        // 移除可见类
        this.modal.classList.remove('modal-visible');
        
        // 延迟隐藏以允许动画完成
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.setAttribute('aria-hidden', 'true');
            this.isVisible = false;
        }, 300);
            
        // 移除键盘事件监听
            document.removeEventListener('keydown', this.keydownHandler);
            
            // 清理数据
            this.currentImageData = null;
            this.galleryImages = [];
            this.currentIndex = 0;
    }

    /**
     * 从API获取图片详细数据
     */
    async fetchImageData(imageId) {
        console.log('🔭 Modal: Fetching image data for ID:', imageId);
        
        const response = await fetch(`/api/v1/images/${imageId}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch image data');
        }
        
        return data.image;
    }

    /**
     * 填充模态框内容
     */
    async populateModal(data) {
        console.log('🔭 Modal: Populating modal with data:', data);

        if (!this.modal) return;

        // 更新图片
        const imageElement = this.modal.querySelector('#modal-image');
        if (imageElement && data.url) {
            imageElement.src = data.url;
            imageElement.alt = data.description || 'AI Generated Environmental Vision';
        }

        // 更新标题
        const titleElement = this.modal.querySelector('#modal-title');
        if (titleElement) {
            titleElement.textContent = 'Environmental Vision';
        }
        
        // 安全的元素更新函数
        const updateElement = (selector, content) => {
            const element = this.modal.querySelector(selector);
            if (element) {
                element.textContent = content;
            }
        };

        // 更新预测数据
        if (data.prediction_data) {
            updateElement('#summary-temperature', data.prediction_data.temperature || '--°C');
            updateElement('#summary-humidity', data.prediction_data.humidity || '--%');
            updateElement('#summary-location', data.prediction_data.location || '--');
            updateElement('#summary-confidence', data.prediction_data.confidence || '--%');
        }

        // 更新时间信息
        if (data.created_at) {
            const date = new Date(data.created_at);
            const formattedDate = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            updateElement('#summary-time', formattedDate);
        }

        // 更新描述
        const descriptionElement = this.modal.querySelector('#image-description');
        if (descriptionElement) {
            descriptionElement.textContent = data.description || 
                'This vision represents a potential future environmental state based on AI predictions and environmental data analysis.';
        }

        // 更新详细分析按钮链接
        const detailButton = this.modal.querySelector('#view-details-btn');
        if (detailButton && data.id) {
            detailButton.onclick = () => this.openDetailPage();
        }
    }

    /**
     * 更新导航按钮状态
     */
    updateNavigationButtons() {
        const prevBtn = this.modal?.querySelector('.modal-prev');
        const nextBtn = this.modal?.querySelector('.modal-next');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentIndex <= 0;
            prevBtn.style.opacity = this.currentIndex <= 0 ? '0.5' : '1';
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentIndex >= (this.galleryImages.length - 1);
            nextBtn.style.opacity = this.currentIndex >= (this.galleryImages.length - 1) ? '0.5' : '1';
        }
    }

    /**
     * 导航到上一张图片
     */
    async navigatePrevious() {
        if (this.currentIndex > 0 && this.galleryImages.length > 0) {
            this.currentIndex--;
            const prevImageData = this.galleryImages[this.currentIndex];
            await this.show(prevImageData, this.galleryImages, this.currentIndex);
        }
    }

    /**
     * 导航到下一张图片
     */
    async navigateNext() {
        if (this.currentIndex < this.galleryImages.length - 1) {
            this.currentIndex++;
            const nextImageData = this.galleryImages[this.currentIndex];
            await this.show(nextImageData, this.galleryImages, this.currentIndex);
        }
    }

    /**
     * 打开详细分析页面
     */
    openDetailPage() {
        if (this.currentImageData?.id) {
            const detailUrl = `/image/${this.currentImageData.id}`;
            console.log('🔭 Modal: Opening detail page:', detailUrl);
            window.open(detailUrl, '_blank');
        }
    }

    /**
     * 下载图片
     */
    async downloadImage() {
        if (!this.currentImageData?.id) return;

        try {
            console.log('🔭 Modal: Downloading image:', this.currentImageData.id);
            const response = await fetch(`/api/v1/images/${this.currentImageData.id}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `obscura-vision-${this.currentImageData.id}.jpg`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('❌ Modal: Download error:', error);
            alert('Download failed. Please try again.');
        }
    }

    /**
     * 处理键盘事件
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
            case ' ':
                if (e.target.classList.contains('modal-close')) {
                    e.preventDefault();
                    this.hide();
                }
                break;
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loadingElement = this.modal?.querySelector('.modal-loading');
        const imageLoading = this.modal?.querySelector('.image-loading');
        
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
        if (imageLoading) {
            imageLoading.style.display = 'block';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loadingElement = this.modal?.querySelector('.modal-loading');
        const imageLoading = this.modal?.querySelector('.image-loading');
        
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        if (imageLoading) {
            imageLoading.style.display = 'none';
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        console.error('🔭 Modal: Error:', message);
        const descriptionElement = this.modal?.querySelector('#image-description');
        if (descriptionElement) {
            descriptionElement.textContent = `Error: ${message}`;
            descriptionElement.style.color = '#ff6b6b';
        }
    }
}

// 确保在窗口加载时可用
if (typeof window !== 'undefined') {
    window.ImageModal = ImageModal;
}
