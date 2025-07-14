// Gallery functionality for Obscura No.7

/**
 * Gallery management class for Obscura No.7 Virtual Telescope
 * Handles image loading, filtering, layout management, and interactions
 */

class GalleryApp {
    constructor() {
        this.images = [];
        this.filteredImages = [];
        this.currentFilter = 'all';
        this.currentView = 'masonry';
        this.isLoading = false;
        this.imageModal = null;
        this.init();
    }

    /**
     * Initialize the gallery application
     */
    init() {
        this.setupEventListeners();
        this.loadImages();
        this.updateStats();
        console.log('🖼️ Gallery System Initialized');
    }

    /**
     * Setup event listeners for gallery controls
     */
    setupEventListeners() {
        // Filter buttons
        const filterButtons = document.querySelectorAll('.filter-button');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.setFilter(filter);
            });
        });

        // View toggle buttons
        const viewToggleButtons = document.querySelectorAll('.view-toggle');
        viewToggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const viewType = e.target.id.replace('-view', '');
                this.setView(viewType);
            });
        });

        // Window resize handler for masonry layout
        window.addEventListener('resize', this.debounce(() => {
            this.updateMasonryLayout();
        }, 250));

        // Infinite scroll (optional)
        this.setupInfiniteScroll();
    }

    /**
     * Load images from API
     */
    async loadImages() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await fetch('/api/v1/images');
            const data = await response.json();

            if (data.success) {
                this.images = data.images || [];
                this.applyFilter();
                this.hideLoadingState();
                this.updateStats();
                
                if (this.images.length === 0) {
                    this.showEmptyState();
                }
            } else {
                throw new Error(data.error || 'Failed to load images');
            }

        } catch (error) {
            console.error('Failed to load images:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Apply current filter to images
     */
    applyFilter() {
        switch (this.currentFilter) {
            case 'recent':
                this.filteredImages = this.images
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .slice(0, 20);
                break;
            case 'all':
            default:
                this.filteredImages = [...this.images];
                break;
        }

        this.renderImages();
    }

    /**
     * Set active filter
     */
    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update filter button states
        const filterButtons = document.querySelectorAll('.filter-button');
        filterButtons.forEach(button => {
            if (button.dataset.filter === filter) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        this.applyFilter();
    }

    /**
     * Set view type (grid or masonry)
     */
    setView(viewType) {
        this.currentView = viewType;
        
        // Update view toggle button states
        const viewButtons = document.querySelectorAll('.view-toggle');
        viewButtons.forEach(button => {
            const buttonViewType = button.id.replace('-view', '');
            if (buttonViewType === viewType) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Update gallery container class
        const galleryContainer = document.getElementById('gallery-container');
        galleryContainer.className = `gallery-grid ${viewType}`;

        this.renderImages();
    }

    /**
     * Render images in the gallery
     */
    renderImages() {
        const galleryContainer = document.getElementById('gallery-container');
        
        if (this.filteredImages.length === 0) {
            this.showEmptyState();
            return;
        }

        galleryContainer.innerHTML = '';

        this.filteredImages.forEach((image, index) => {
            const imageElement = this.createImageElement(image, index);
            galleryContainer.appendChild(imageElement);
        });

        // 确保事件绑定在DOM更新后执行
        setTimeout(() => {
            this.rebindClickEvents();
            
            // Update layout for masonry view
            if (this.currentView === 'masonry') {
                this.updateMasonryLayout();
            }
        }, 100);
    }

    /**
     * Create individual image element
     */
    createImageElement(image, index) {
        const imageItem = document.createElement('div');
        imageItem.className = 'gallery-item';
        imageItem.style.animationDelay = `${index * 0.1}s`;

        const imageDate = new Date(image.created_at);
        const formattedDate = imageDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        const formattedTime = imageDate.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // 提取地理位置信息
        let locationName = 'Unknown Location';
        if (image.prediction && image.prediction.location) {
            locationName = image.prediction.location;
        } else if (image.prediction && image.prediction.input_data && image.prediction.input_data.location_name) {
            locationName = image.prediction.input_data.location_name;
        } else if (image.prediction && image.prediction.result_data && image.prediction.result_data.city) {
            locationName = image.prediction.result_data.city;
        }

        imageItem.innerHTML = `
            <div class="image-container">
                <img src="${image.url}" alt="${locationName}" class="gallery-image" loading="lazy">
                <div class="image-overlay">
                    <div class="overlay-content">
                        <div class="image-title">${locationName}</div>
                        <div class="image-meta">${formattedDate} • ${formattedTime}</div>
                    </div>
                </div>
            </div>
            <div class="item-details">
                <p class="item-description">${image.description || 'A glimpse through the temporal lens...'}</p>
                <div class="item-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Image ID:</span>
                        <span class="metadata-value">#${String(image.id).padStart(4, '0')}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Prediction:</span>
                        <span class="metadata-value">#${String(image.prediction_id).padStart(4, '0')}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Generated:</span>
                        <span class="metadata-value">${formattedDate}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Time:</span>
                        <span class="metadata-value">${formattedTime}</span>
                    </div>
                </div>
            </div>
        `;

        // Add click handler for future detail view
        imageItem.addEventListener('click', () => {
            this.showImageDetail(image);
        });

        // Add image load animation
        const img = imageItem.querySelector('.gallery-image');
        img.addEventListener('load', () => {
            imageItem.classList.add('loaded');
        });

        return imageItem;
    }

    /**
     * Show image detail modal
     */
    showImageDetail(image) {
        console.log('🖼️ Gallery: Showing image detail for:', image);
        
        // 找到当前图片在filteredImages中的索引
        const currentIndex = this.filteredImages.findIndex(img => img.id === image.id);
        
        console.log('🖼️ Gallery: Current index:', currentIndex);
        console.log('🖼️ Gallery: Total images:', this.filteredImages.length);
        console.log('🖼️ Gallery: Passing gallery images to modal:', this.filteredImages);
        
        // 确保ImageModal实例存在
        if (!window.imageModal) {
            console.error('❌ Gallery: ImageModal instance not found');
            return;
        }
        
        // 调用模态框显示方法，传递正确的参数
        window.imageModal.show(image, this.filteredImages, currentIndex)
            .then(() => {
                console.log('✅ Gallery: Modal shown successfully');
            })
            .catch(error => {
                console.error('❌ Gallery: Error showing modal:', error);
            });
    }

    /**
     * Update masonry layout
     */
    updateMasonryLayout() {
        if (this.currentView !== 'masonry') return;

        const galleryContainer = document.getElementById('gallery-container');
        const items = galleryContainer.querySelectorAll('.gallery-item');

        if (items.length === 0) return;

        // Simple masonry layout implementation
        const columns = this.calculateColumns();
        const columnHeights = new Array(columns).fill(0);

        items.forEach(item => {
            // Find the shortest column
            const shortestColumnIndex = columnHeights.indexOf(Math.min(...columnHeights));
            
            // Position the item
            const columnWidth = galleryContainer.offsetWidth / columns;
            const gap = 32; // 2rem gap
            
            item.style.position = 'absolute';
            item.style.left = `${shortestColumnIndex * (columnWidth + gap)}px`;
            item.style.top = `${columnHeights[shortestColumnIndex]}px`;
            item.style.width = `${columnWidth - gap}px`;

            // Update column height
            columnHeights[shortestColumnIndex] += item.offsetHeight + gap;
        });

        // Set container height
        galleryContainer.style.height = `${Math.max(...columnHeights)}px`;
        galleryContainer.style.position = 'relative';
    }

    /**
     * Calculate optimal number of columns for masonry
     */
    calculateColumns() {
        const containerWidth = document.getElementById('gallery-container').offsetWidth;
        const minColumnWidth = 300;
        const gap = 32;
        
        const columns = Math.max(1, Math.floor((containerWidth + gap) / (minColumnWidth + gap)));
        return columns;
    }

    /**
     * Update gallery statistics
     */
    async updateStats() {
        const totalImagesElement = document.getElementById('total-images');
        const totalPredictionsElement = document.getElementById('total-predictions');
        const locationsExploredElement = document.getElementById('locations-explored');

        if (totalImagesElement) {
            totalImagesElement.textContent = this.images.length;
        }

        // Get unique prediction IDs for prediction count
        if (totalPredictionsElement) {
            const uniquePredictions = new Set(this.images.map(img => img.prediction_id));
            totalPredictionsElement.textContent = uniquePredictions.size;
        }

        // Placeholder for locations (would need additional data)
        if (locationsExploredElement) {
            locationsExploredElement.textContent = Math.min(this.images.length, 12);
        }
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const galleryContainer = document.getElementById('gallery-container');
        galleryContainer.innerHTML = `
            <div class="loading-placeholder">
                <div class="brass-spinner">
                    <div class="gear-spinner">⚙️</div>
                </div>
                <p class="loading-text">Loading visions from the temporal archive...</p>
            </div>
        `;
    }

    /**
     * Hide loading state
     */
    hideLoadingState() {
        const loadingPlaceholder = document.querySelector('.loading-placeholder');
        if (loadingPlaceholder) {
            loadingPlaceholder.remove();
        }
    }

    /**
     * Show empty state
     */
    showEmptyState() {
        const galleryContainer = document.getElementById('gallery-container');
        const noImagesMessage = document.getElementById('no-images');
        
        galleryContainer.innerHTML = '';
        if (noImagesMessage) {
            noImagesMessage.style.display = 'block';
        }
    }

    /**
     * Show error state
     */
    showErrorState(message) {
        const galleryContainer = document.getElementById('gallery-container');
        galleryContainer.innerHTML = `
            <div class="error-placeholder">
                <div class="brass-panel error-panel">
                    <div class="error-content">
                        <span class="error-icon">⚠️</span>
                        <h3>System Malfunction</h3>
                        <p>Failed to load visions: ${message}</p>
                        <button class="retry-button" onclick="window.galleryApp.loadImages()">
                            Retry Loading
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Setup infinite scroll (optional feature)
     */
    setupInfiniteScroll() {
        let isScrolling = false;

        window.addEventListener('scroll', () => {
            if (isScrolling) return;
            
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = document.documentElement.scrollTop;
            const clientHeight = document.documentElement.clientHeight;

            if (scrollTop + clientHeight >= scrollHeight - 1000) {
                isScrolling = true;
                // Load more images if available
                setTimeout(() => {
                    isScrolling = false;
                }, 1000);
            }
        });
    }

    /**
     * Utility: Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Position notification at top right
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--brass-gradient);
            border: 2px solid var(--brass-dark);
            color: var(--coal);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            z-index: 10000;
            font-weight: bold;
            animation: notification-slide-in 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'notification-slide-out 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Refresh gallery data
     */
    refresh() {
        this.loadImages();
    }
}

// Additional CSS for gallery animations
const galleryStyles = `
    .gallery-item {
        opacity: 0;
        transform: translateY(20px);
        animation: gallery-item-appear 0.6s ease-out forwards;
    }
    
    .gallery-item.loaded {
        opacity: 1;
        transform: translateY(0);
    }
    
    @keyframes gallery-item-appear {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .error-panel {
        padding: 3rem;
        text-align: center;
    }
    
    .error-icon {
        font-size: 3rem;
        display: block;
        margin-bottom: 1rem;
        color: #cc4444;
    }
    
    .retry-button {
        background: var(--brass-gradient);
        border: 2px solid var(--brass-dark);
        padding: 1rem 2rem;
        border-radius: 8px;
        color: var(--coal);
        font-weight: bold;
        cursor: pointer;
        margin-top: 1rem;
        transition: all 0.3s ease;
    }
    
    .retry-button:hover {
        background: var(--copper-gradient);
        transform: translateY(-2px);
    }
    
    @keyframes notification-slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes notification-slide-out {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;

// Inject gallery-specific styles
const galleryStyleSheet = document.createElement('style');
galleryStyleSheet.textContent = galleryStyles;
document.head.appendChild(galleryStyleSheet);

// Initialize gallery when DOM is loaded (only on gallery page)
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/gallery') {
        window.galleryApp = new GalleryApp();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GalleryApp;
}
