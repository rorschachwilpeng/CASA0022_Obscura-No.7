// Obscura No.7 - Main JavaScript

/**
 * Main application JavaScript for Obscura No.7 Virtual Telescope
 * Handles navigation, system status monitoring, and shared functionality
 */

class ObscuraApp {
    constructor() {
        this.systemStatus = {
            online: false,
            services: {}
        };
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.initializeStatusMonitor();
        this.setupSteampunkEffects();
        console.log('🔭 Obscura No.7 - Virtual Telescope System Initialized');
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Navigation active state management
        this.updateNavActiveState();
        
        // System status refresh
        const refreshButton = document.getElementById('refresh-status');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshSystemStatus());
        }

        // Smooth scrolling for anchor links
        this.setupSmoothScrolling();

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Window resize handler
        window.addEventListener('resize', this.handleResize.bind(this));
    }

    /**
     * Update navigation active state based on current page
     */
    updateNavActiveState() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath || (currentPath === '/' && href === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    /**
     * Initialize system status monitoring
     */
    initializeStatusMonitor() {
        this.refreshSystemStatus();
        
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            this.refreshSystemStatus();
        }, 30000);
    }

    /**
     * Refresh system status from API
     */
    async refreshSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.systemStatus = data;
            this.updateStatusDisplay(data);
            this.updateStatusIndicator(data.status === 'online');
            
        } catch (error) {
            console.error('Failed to fetch system status:', error);
            this.updateStatusIndicator(false);
        }
    }

    /**
     * Update status display on the page
     */
    updateStatusDisplay(statusData) {
        const services = statusData.services || {};
        
        // Update individual service status cards
        this.updateServiceCard('openweather', services.openweather);
        this.updateServiceCard('openai', services.openai);
        this.updateServiceCard('google_maps', services.google_maps);
        this.updateServiceCard('cloudinary', services.cloudinary);
        this.updateServiceCard('database', services.database);
        this.updateServiceCard('ml_workflow', services.ml_workflow);

        // Update timestamp if present
        const timestampElement = document.querySelector('.info-value[data-timestamp]');
        if (timestampElement && statusData.timestamp) {
            const date = new Date(statusData.timestamp);
            timestampElement.textContent = date.toLocaleString();
        }
    }

    /**
     * Update individual service status card
     */
    updateServiceCard(serviceName, isOnline) {
        const card = document.querySelector(`[data-service="${serviceName}"]`);
        if (!card) return;

        const statusLight = card.querySelector('.status-light');
        const statusText = card.querySelector('.status-text');

        if (isOnline) {
            card.classList.add('operational');
            card.classList.remove('malfunction');
            if (statusText) statusText.textContent = 'OPERATIONAL';
        } else {
            card.classList.add('malfunction');
            card.classList.remove('operational');
            if (statusText) statusText.textContent = 'DISCONNECTED';
        }
    }

    /**
     * Update main status indicator in navigation
     */
    updateStatusIndicator(isOnline) {
        const statusIndicator = document.getElementById('system-status');
        const statusLight = statusIndicator?.querySelector('.status-light');
        const statusText = statusIndicator?.querySelector('.status-text');

        if (isOnline) {
            statusIndicator?.classList.add('online');
            statusIndicator?.classList.remove('offline');
            if (statusText) statusText.textContent = 'ONLINE';
        } else {
            statusIndicator?.classList.add('offline');
            statusIndicator?.classList.remove('online');
            if (statusText) statusText.textContent = 'OFFLINE';
        }
    }

    /**
     * Setup steampunk visual effects
     */
    setupSteampunkEffects() {
        // Gear rotation animation
        this.setupGearAnimations();
        
        // Steam particle effects
        this.setupSteamEffects();
        
        // Brass shine effects
        this.setupBrassShineEffects();
        
        // Mechanical sound effects (optional)
        this.setupSoundEffects();
    }

    /**
     * Setup gear rotation animations
     */
    setupGearAnimations() {
        const gears = document.querySelectorAll('.gear-spinner, .gear-icon');
        
        gears.forEach((gear, index) => {
            // Randomize rotation speed and direction
            const speed = 2 + Math.random() * 3; // 2-5 seconds
            const direction = index % 2 === 0 ? 'normal' : 'reverse';
            
            gear.style.animation = `spin ${speed}s linear infinite ${direction}`;
        });
    }

    /**
     * Setup steam particle effects
     */
    setupSteamEffects() {
        const steamContainers = document.querySelectorAll('.steam-effect');
        
        steamContainers.forEach(container => {
            this.createSteamParticles(container);
        });
    }

    /**
     * Create steam particles for steampunk effect
     */
    createSteamParticles(container) {
        const particleCount = 5;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'steam-particle';
            particle.style.cssText = `
                position: absolute;
                width: ${4 + Math.random() * 8}px;
                height: ${4 + Math.random() * 8}px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                animation: steam-rise ${3 + Math.random() * 4}s ease-out infinite;
                animation-delay: ${Math.random() * 2}s;
                left: ${Math.random() * 100}%;
                bottom: 0;
            `;
            
            container.appendChild(particle);
        }
    }

    /**
     * Setup brass shine effects
     */
    setupBrassShineEffects() {
        const brassElements = document.querySelectorAll('.brass-panel, .brass-plate, .control-button');
        
        brassElements.forEach(element => {
            element.addEventListener('mouseenter', this.addBrassShine);
            element.addEventListener('mouseleave', this.removeBrassShine);
        });
    }

    /**
     * Add brass shine effect
     */
    addBrassShine(event) {
        const element = event.target;
        const shine = document.createElement('div');
        shine.className = 'brass-shine';
        shine.style.cssText = `
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            animation: shine-sweep 0.8s ease-out;
            pointer-events: none;
            z-index: 1;
        `;
        
        element.style.position = 'relative';
        element.appendChild(shine);
        
        setTimeout(() => {
            if (shine.parentNode) {
                shine.parentNode.removeChild(shine);
            }
        }, 800);
    }

    /**
     * Remove brass shine effect
     */
    removeBrassShine(event) {
        // Cleanup is handled in addBrassShine timeout
    }

    /**
     * Setup sound effects (optional)
     */
    setupSoundEffects() {
        // Mechanical click sounds for buttons
        const buttons = document.querySelectorAll('.control-button, .filter-button, .nav-button');
        
        buttons.forEach(button => {
            button.addEventListener('click', this.playMechanicalClick);
        });
    }

    /**
     * Play mechanical click sound
     */
    playMechanicalClick() {
        // Placeholder for sound effect
        // Can be implemented with Web Audio API or audio elements
        console.log('🔧 Mechanical click sound');
    }

    /**
     * Setup smooth scrolling for anchor links
     */
    setupSmoothScrolling() {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        
        anchorLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + H: Home
            if (e.altKey && e.key === 'h') {
                e.preventDefault();
                window.location.href = '/';
            }
            
            // Alt + G: Gallery
            if (e.altKey && e.key === 'g') {
                e.preventDefault();
                window.location.href = '/gallery';
            }
            
            // Alt + R: Refresh status
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                this.refreshSystemStatus();
            }
        });
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Recalculate layout if needed
        this.updateLayout();
    }

    /**
     * Update layout on resize
     */
    updateLayout() {
        // Update masonry layout if on gallery page
        if (window.location.pathname === '/gallery' && window.galleryApp) {
            window.galleryApp.updateMasonryLayout();
        }
    }

    /**
     * Utility: Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * Utility: Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--brass-gradient);
            color: var(--coal);
            padding: 1rem 2rem;
            border-radius: 8px;
            border: 2px solid var(--brass-dark);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slide-in 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slide-out 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Utility: API request helper
     */
    async apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }
}

// CSS Animations (to be added via JavaScript)
const additionalStyles = `
    @keyframes shine-sweep {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    @keyframes steam-rise {
        0% {
            opacity: 0;
            transform: translateY(0) scale(1);
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            opacity: 0;
            transform: translateY(-100px) scale(1.5);
        }
    }
    
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slide-out {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .status-indicator.online .status-light {
        background: #44cc44;
        box-shadow: 0 0 12px #44cc44;
    }
    
    .status-indicator.offline .status-light {
        background: #cc4444;
        box-shadow: 0 0 12px #cc4444;
        animation: pulse-warning 1s infinite;
    }
    
    @keyframes pulse-warning {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.obscuraApp = new ObscuraApp();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ObscuraApp;
}
