/**
 * Obscura No.7 - WebSocket Client for Real-time Updates
 * 实时更新的WebSocket客户端
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3秒
        
        this.init();
    }

    /**
     * 初始化WebSocket连接
     */
    init() {
        try {
            // 检查Socket.IO是否已加载
            if (typeof io === 'undefined') {
                console.warn('⚠️ Socket.IO library not loaded, attempting to load...');
                this.loadSocketIOLibrary();
                return;
            }

            this.connect();
        } catch (error) {
            console.error('❌ WebSocket initialization failed:', error);
        }
    }

    /**
     * 动态加载Socket.IO库
     */
    loadSocketIOLibrary() {
        const script = document.createElement('script');
        script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js';
        script.onload = () => {
            console.log('✅ Socket.IO library loaded');
            this.connect();
        };
        script.onerror = () => {
            console.error('❌ Failed to load Socket.IO library');
        };
        document.head.appendChild(script);
    }

    /**
     * 建立WebSocket连接
     */
    connect() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 20000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay
            });

            this.setupEventListeners();
            
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 连接成功
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('✅ WebSocket connected');
            this.showConnectionStatus('connected');
        });

        // 连接断开
        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            console.log('⚠️ WebSocket disconnected:', reason);
            this.showConnectionStatus('disconnected');
        });

        // 连接错误
        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket connection error:', error);
            this.showConnectionStatus('error');
        });

        // 监听新图片上传事件
        this.socket.on('new_image_uploaded', (data) => {
            console.log('📸 New image uploaded:', data);
            this.handleNewImageUploaded(data);
        });

        // 重连尝试
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`🔄 Reconnecting... Attempt ${attemptNumber}`);
            this.showConnectionStatus('reconnecting');
        });

        // 重连成功
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`✅ Reconnected after ${attemptNumber} attempts`);
            this.showConnectionStatus('connected');
        });

        // 重连失败
        this.socket.on('reconnect_failed', () => {
            console.error('❌ Failed to reconnect after maximum attempts');
            this.showConnectionStatus('failed');
        });
    }

    /**
     * 处理新图片上传事件
     */
    handleNewImageUploaded(data) {
        // 显示通知
        this.showNotification(`New environmental vision uploaded: ${data.description}`, 'info');

        // 根据当前页面决定如何响应
        const currentPath = window.location.pathname;

        if (currentPath === '/gallery' || currentPath === '/') {
            // 在Gallery页面，重新加载图片列表
            this.refreshGallery();
        } else {
            // 在其他页面，显示提示用户可以前往Gallery查看
            this.showNotification('New image available in gallery!', 'update', () => {
                window.location.href = '/gallery';
            });
        }
    }

    /**
     * 刷新Gallery页面
     */
    refreshGallery() {
        // 检查是否存在Gallery相关的刷新函数
        if (typeof window.galleryPage !== 'undefined' && window.galleryPage.loadImages) {
            // 如果存在Gallery实例，调用其刷新方法
            window.galleryPage.loadImages();
            console.log('🔄 Gallery refreshed via instance method');
        } else {
            // 否则重新加载整个页面
            setTimeout(() => {
                window.location.reload();
            }, 1000); // 延迟1秒让用户看到通知
            console.log('🔄 Gallery page reloading');
        }
    }

    /**
     * 显示连接状态
     */
    showConnectionStatus(status) {
        // 查找状态指示器元素
        let statusIndicator = document.getElementById('websocket-status');
        
        if (!statusIndicator) {
            // 如果不存在，创建一个简单的状态指示器
            statusIndicator = document.createElement('div');
            statusIndicator.id = 'websocket-status';
            statusIndicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10000;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(statusIndicator);
        }

        // 根据状态设置样式和文本
        switch (status) {
            case 'connected':
                statusIndicator.style.background = '#4CAF50';
                statusIndicator.style.color = 'white';
                statusIndicator.textContent = '🔗 Live Updates Active';
                // 3秒后隐藏
                setTimeout(() => {
                    statusIndicator.style.opacity = '0';
                }, 3000);
                break;
            case 'disconnected':
            case 'error':
                statusIndicator.style.background = '#f44336';
                statusIndicator.style.color = 'white';
                statusIndicator.style.opacity = '1';
                statusIndicator.textContent = '❌ Connection Lost';
                break;
            case 'reconnecting':
                statusIndicator.style.background = '#FF9800';
                statusIndicator.style.color = 'white';
                statusIndicator.style.opacity = '1';
                statusIndicator.textContent = '🔄 Reconnecting...';
                break;
            case 'failed':
                statusIndicator.style.background = '#9E9E9E';
                statusIndicator.style.color = 'white';
                statusIndicator.style.opacity = '1';
                statusIndicator.textContent = '⚠️ Offline Mode';
                break;
        }
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info', action = null) {
        const notification = document.createElement('div');
        notification.className = `websocket-notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 50px;
            right: 20px;
            max-width: 300px;
            padding: 15px;
            border-radius: 8px;
            color: white;
            z-index: 10001;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            cursor: ${action ? 'pointer' : 'default'};
        `;

        // 根据类型设置背景色
        switch (type) {
            case 'info':
                notification.style.background = '#2196F3';
                break;
            case 'update':
                notification.style.background = '#4CAF50';
                break;
            case 'warning':
                notification.style.background = '#FF9800';
                break;
            case 'error':
                notification.style.background = '#f44336';
                break;
        }

        notification.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">
                ${type === 'update' ? '🔄' : type === 'info' ? 'ℹ️' : '⚠️'} Real-time Update
            </div>
            <div>${message}</div>
            ${action ? '<div style="margin-top: 10px; font-size: 12px;">Click to view →</div>' : ''}
        `;

        // 添加点击事件
        if (action) {
            notification.addEventListener('click', action);
        }

        document.body.appendChild(notification);

        // 动画显示
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // 自动移除
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, action ? 10000 : 5000); // 如果有动作，显示更长时间
    }

    /**
     * 计划重连
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Maximum reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);

        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);

        // 增加延迟时间（指数退避）
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
    }

    /**
     * 手动重连
     */
    reconnect() {
        this.reconnectAttempts = 0;
        this.reconnectDelay = 3000;
        this.connect();
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
        }
    }

    /**
     * 获取连接状态
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            socketId: this.socket?.id || null,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// 全局实例
window.wsClient = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保其他脚本已加载
    setTimeout(() => {
        window.wsClient = new WebSocketClient();
        console.log('🔭 WebSocket client initialized for Obscura No.7');
    }, 1000);
});

// 页面卸载时断开连接
window.addEventListener('beforeunload', () => {
    if (window.wsClient) {
        window.wsClient.disconnect();
    }
});

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
} 