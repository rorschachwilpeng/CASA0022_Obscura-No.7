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
            
            console.log('🎨 Adding modal-visible animation class (fallback)...');
            // 动画效果
            requestAnimationFrame(() => {
                this.modal.classList.add('modal-visible');
                console.log('✅ modal-visible class added (fallback)');
                console.log('🔍 Modal final state (fallback):', {
                    display: this.modal.style.display,
                    visibility: window.getComputedStyle(this.modal).visibility,
                    opacity: window.getComputedStyle(this.modal).opacity,
                    zIndex: window.getComputedStyle(this.modal).zIndex,
                    classes: this.modal.className
                });
            });
        }
        
        console.log('🏁 ImageModal.show() method completed');
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
        
        // 添加调试信息
        console.log('🔭 Modal: Received image data:', data.image);
        
        // 如果没有环境数据，添加一些模拟数据用于演示
        if (data.image && (!data.image.prediction || !data.image.prediction.input_data)) {
            console.log('🔭 Modal: Adding mock environmental data');
            data.image.prediction = {
                id: 1,
                input_data: {
                    temperature: 22.5,
                    humidity: 65,
                    latitude: 51.5074,
                    longitude: -0.1278,
                    wind_speed: 8.2,
                    pressure: 1013.25
                },
                result_data: {},
                prompt: "Environmental prediction based on current conditions",
                location: "London Observatory"
            };
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

        // 更新环境数据 - 只保留核心三项信息
        if (data.prediction && data.prediction.input_data) {
            const inputData = data.prediction.input_data;
            const resultData = data.prediction.result_data || {};
            
            // 温度
            const temperature = inputData.temperature || '--';
            updateElement('#summary-temperature', temperature !== '--' ? `${temperature}°C` : '--°C');
            
            // 湿度
            const humidity = inputData.humidity || '--';
            updateElement('#summary-humidity', humidity !== '--' ? `${humidity}%` : '--%');
            
            // 地理位置 - 使用格式化的位置名称
            const locationName = this.formatLocationName(data);
            updateElement('#summary-location', locationName);
            
        } else {
            // 如果没有预测数据，显示默认值
            updateElement('#summary-temperature', '--°C');
            updateElement('#summary-humidity', '--%');
            updateElement('#summary-location', '--');
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

        // 更新描述 - 显示Prompt信息而不是description
        const descriptionElement = this.modal.querySelector('#image-description');
        if (descriptionElement) {
            let visionDescription = 'AI environmental prediction prompt not available';
            
            if (data.prediction && data.prediction.prompt) {
                visionDescription = data.prediction.prompt;
            } else if (data.prediction && data.prediction.result_data && data.prediction.result_data.ai_story) {
                visionDescription = data.prediction.result_data.ai_story;
            } else if (data.description) {
                visionDescription = data.description;
            }
            
            descriptionElement.textContent = visionDescription;
        }

        // 更新详细分析按钮链接
        const detailButton = this.modal.querySelector('#view-details-btn');
        if (detailButton && data.id) {
            detailButton.onclick = () => this.openDetailPage();
        }
    }

    /**
     * 格式化地理位置名称为简洁的"City, Region"格式  
     * @param {Object} data - 图片数据
     * @returns {string} 格式化后的位置名称
     */
    formatLocationName(data) {
        if (!data.prediction) {
            return 'Unknown Location';
        }

        let locationName = '';
        const prediction = data.prediction;
        const inputData = prediction.input_data || {};
        const resultData = prediction.result_data || {};

        // 优先使用已经格式化好的location字段
        if (prediction.location) {
            locationName = prediction.location;
        } else if (inputData.location) {
            locationName = inputData.location;
        } else if (resultData.city) {
            locationName = resultData.city;
        } else if (inputData.latitude && inputData.longitude) {
            // 如果只有坐标，尝试转换为城市名（这里用简化处理）
            const lat = inputData.latitude;
            const lon = inputData.longitude;
            
            // 简化的城市识别（基于坐标范围）
            if (lat >= 51.3 && lat <= 51.7 && lon >= -0.5 && lon <= 0.3) {
                locationName = 'London, UK';
            } else if (lat >= 55.8 && lat <= 56.0 && lon >= -3.4 && lon <= -3.0) {
                locationName = 'Edinburgh, UK';
            } else if (lat >= 53.4 && lat <= 53.6 && lon >= -2.4 && lon <= -2.1) {
                locationName = 'Manchester, UK';
            } else {
                locationName = `${lat.toFixed(1)}°, ${lon.toFixed(1)}°`;
            }
        } else {
            locationName = 'Unknown Location';
        }

        // 确保格式统一：如果不包含逗号且不是坐标，尝试添加默认区域
        if (locationName && !locationName.includes(',') && !locationName.includes('°')) {
            // 检查是否是已知城市名，如果是就添加国家/地区
            const knownCities = {
                'London': 'London, UK',
                'Edinburgh': 'Edinburgh, UK', 
                'Manchester': 'Manchester, UK',
                'Birmingham': 'Birmingham, UK',
                'Glasgow': 'Glasgow, UK',
                'Liverpool': 'Liverpool, UK',
                'Bristol': 'Bristol, UK',
                'Stratford': 'Stratford, London'
            };
            
            const cityName = locationName.charAt(0).toUpperCase() + locationName.slice(1).toLowerCase();
            if (knownCities[cityName]) {
                locationName = knownCities[cityName];
            }
        }

        return locationName || 'Unknown Location';
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
            window.location.href = detailUrl;
        }
    }

    /**
     * 下载图片
     */
    async downloadImage() {
        if (!this.currentImageData?.id) return;

        try {
            console.log('🔭 Modal: Downloading image:', this.currentImageData.id);
            
            // 调用后端下载API获取图片文件流
            const response = await fetch(`/api/v1/images/${this.currentImageData.id}/download`);
            
            if (!response.ok) {
                // 安全地获取错误信息
                let errorText = 'Unknown error';
                try {
                    errorText = await response.text();
                } catch (e) {
                    errorText = `Response read failed: ${e.message}`;
                }
                throw new Error(`Download failed: ${response.status} ${response.statusText} - ${errorText}`);
            }
            
            // 获取文件blob
            const blob = await response.blob();
            
            // 验证blob是否为有效的图片
            if (blob.size === 0) {
                throw new Error('Downloaded file is empty');
            }
            
            const url = window.URL.createObjectURL(blob);
            
            // 创建下载链接
            const a = document.createElement('a');
            a.href = url;
            a.download = `obscura-vision-${this.currentImageData.id}.jpg`;
            document.body.appendChild(a);
            a.click();
            
            // 清理URL对象和DOM元素
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('✅ Modal: Image download completed');
            
        } catch (error) {
            console.error('❌ Modal: Download error:', error || 'Unknown error occurred');
            
            // 更好的用户反馈
            const errorMessage = error?.message || 'Unknown error';
            if (errorMessage.includes('403')) {
                alert('Download not allowed. Please check permissions.');
            } else if (errorMessage.includes('404')) {
                alert('Image not found. It may have been removed.');
            } else if (errorMessage.includes('500')) {
                alert('Server error. Please try again later.');
            } else {
                alert(`Download failed: ${errorMessage}`);
            }
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

// 确保在窗口加载时可用
if (typeof window !== 'undefined') {
    window.ImageModal = ImageModal;
}
