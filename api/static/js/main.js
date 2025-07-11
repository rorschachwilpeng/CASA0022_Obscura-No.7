// Obscura No.7 - Main JavaScript

/**
 * Main application JavaScript for Obscura No.7 Virtual Telescope
 * Handles navigation, steampunk effects, and shared functionality
 */

class ObscuraApp {
    constructor() {
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.setupSteampunkEffects();
        console.log('🔭 Obscura No.7 - Virtual Telescope Gallery Initialized');
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Navigation active state management
        this.updateNavActiveState();

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
            if (href === currentPath || (currentPath === '/' && href === '/') || 
                (currentPath === '/gallery' && href === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
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
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.className = 'steam-particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 2 + 's';
            particle.style.animationDuration = (3 + Math.random() * 2) + 's';
            
            container.appendChild(particle);
            
            // Remove particle after animation
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 5000);
        }
    }

    /**
     * Setup brass shine effects on hover
     */
    setupBrassShineEffects() {
        const brassElements = document.querySelectorAll('.brass-panel, .nav-button, .action-button');
        
        brassElements.forEach(element => {
            element.addEventListener('mouseenter', this.addBrassShine.bind(this));
            element.addEventListener('mouseleave', this.removeBrassShine.bind(this));
        });
    }

    /**
     * Add brass shine effect
     */
    addBrassShine(event) {
        const element = event.target.closest('.brass-panel, .nav-button, .action-button');
        if (!element) return;

        const shine = document.createElement('div');
        shine.className = 'brass-shine';
        shine.style.cssText = `
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            animation: brassShine 0.6s ease-out;
            pointer-events: none;
            z-index: 1;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(shine);
        
        setTimeout(() => {
            if (shine.parentNode) {
                shine.parentNode.removeChild(shine);
            }
        }, 600);
    }

    /**
     * Remove brass shine effect
     */
    removeBrassShine(event) {
        // Shine removal is handled by timeout in addBrassShine
    }

    /**
     * Setup mechanical sound effects (optional)
     */
    setupSoundEffects() {
        const clickableElements = document.querySelectorAll('button, .nav-link, .action-button');
        
        clickableElements.forEach(element => {
            element.addEventListener('click', this.playMechanicalClick.bind(this));
        });
    }

    /**
     * Play mechanical click sound
     */
    playMechanicalClick() {
        // Audio could be implemented here for better UX
        // For now, just a console log for debugging
        console.log('🔧 Mechanical click');
    }

    /**
     * Setup smooth scrolling for anchor links
     */
    setupSmoothScrolling() {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        
        anchorLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href === '#') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
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
            // Gallery shortcut: Alt + G
            if (e.altKey && (e.key === 'g' || e.key === 'G')) {
                e.preventDefault();
                window.location.href = '/';
            }
            
            // Refresh shortcut: F5 or Ctrl + R
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                // Allow default browser refresh
                return;
            }
        });
    }

    /**
     * Handle window resize events
     */
    handleResize() {
        this.updateLayout();
    }

    /**
     * Update layout based on screen size
     */
    updateLayout() {
        // Add responsive layout adjustments here
        const isMobile = window.innerWidth <= 768;
        document.body.classList.toggle('mobile-layout', isMobile);
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return 'Invalid Date';
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Close notification">✕</button>
            </div>
        `;

        container.appendChild(notification);

        // Add event listener for close button
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
    }

    /**
     * Make API requests with proper error handling
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
                throw new Error(`API request failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            this.showNotification('Network error occurred', 'error');
            throw error;
        }
    }

    /**
     * Utility method to format file sizes
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Check if user prefers reduced motion
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /**
     * Utility method to debounce function calls
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
}

// CSS for steampunk effects
const steampunkStyles = `
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes brassShine {
    from { left: -100%; }
    to { left: 100%; }
}

@keyframes steamRise {
    from {
        opacity: 0.8;
        transform: translateY(0) scale(0.5);
    }
    to {
        opacity: 0;
        transform: translateY(-50px) scale(1.5);
    }
}

.steam-particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 50%;
    animation: steamRise 3s linear infinite;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--brass-gradient);
    border: 2px solid var(--bronze);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    transform: translateX(400px);
    transition: transform 0.3s ease;
}

.notification.show {
    transform: translateX(0);
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.notification-message {
    color: var(--coal);
    font-weight: bold;
}

.notification-close {
    background: none;
    border: none;
    color: var(--coal);
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0;
}

.mobile-layout .nav-menu {
    flex-direction: column;
}

@media (prefers-reduced-motion: reduce) {
    .gear-spinner,
    .steam-particle,
    .brass-shine {
        animation: none !important;
    }
}
`;

// Inject steampunk styles
const styleSheet = document.createElement('style');
styleSheet.textContent = steampunkStyles;
document.head.appendChild(styleSheet);

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.obscuraApp = new ObscuraApp();
});

// Make the app globally accessible
window.ObscuraApp = ObscuraApp;
