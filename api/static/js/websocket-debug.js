/**
 * WebSocket Debug Tool for Render Deployment
 * 用于Render部署环境的WebSocket调试工具
 */

class WebSocketDebugTool {
    constructor() {
        this.testResults = {};
        this.init();
    }

    init() {
        console.log('🔍 WebSocket Debug Tool initialized');
        this.createDebugUI();
        this.runDiagnostics();
    }

    createDebugUI() {
        // 创建调试面板
        const debugPanel = document.createElement('div');
        debugPanel.id = 'websocket-debug-panel';
        debugPanel.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            width: 400px;
            max-height: 500px;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            z-index: 99999;
            font-family: monospace;
            font-size: 12px;
            overflow-y: auto;
        `;
        
        debugPanel.innerHTML = `
            <h3>🔍 WebSocket Debug Panel</h3>
            <div id="debug-content">
                <p>🔄 Running diagnostics...</p>
            </div>
            <button onclick="wsDebug.refresh()" style="margin-top:10px; padding:5px;">Refresh</button>
            <button onclick="wsDebug.hide()" style="margin-top:10px; padding:5px; margin-left:5px;">Hide</button>
        `;
        
        document.body.appendChild(debugPanel);
        this.panel = debugPanel;
    }

    async runDiagnostics() {
        const content = document.getElementById('debug-content');
        content.innerHTML = '<p>🔄 Running diagnostics...</p>';
        
        const results = [];
        
        // 1. 检查Socket.IO库加载
        results.push(`1. Socket.IO Library: ${typeof io !== 'undefined' ? '✅ Loaded' : '❌ Not loaded'}`);
        
        // 2. 检查后端WebSocket状态端点
        try {
            const response = await fetch('/debug/websocket-status');
            if (response.ok) {
                const data = await response.json();
                results.push(`2. Backend Status: ✅ Available`);
                results.push(`   - SocketIO Imported: ${data.websocket_status.socketio_imported ? '✅' : '❌'}`);
                results.push(`   - SocketIO Version: ${data.websocket_status.socketio_version || 'N/A'}`);
                results.push(`   - App Has SocketIO: ${data.websocket_status.app_has_socketio ? '✅' : '❌'}`);
                if (data.websocket_status.socketio_import_error) {
                    results.push(`   - Import Error: ${data.websocket_status.socketio_import_error}`);
                }
            } else {
                results.push(`2. Backend Status: ❌ Error ${response.status}`);
            }
        } catch (error) {
            results.push(`2. Backend Status: ❌ ${error.message}`);
        }
        
        // 3. 尝试WebSocket连接
        if (typeof io !== 'undefined') {
            results.push(`3. WebSocket Connection Test:`);
            try {
                const testSocket = io({
                    timeout: 5000,
                    reconnection: false
                });
                
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        testSocket.disconnect();
                        reject(new Error('Connection timeout'));
                    }, 5000);
                    
                    testSocket.on('connect', () => {
                        clearTimeout(timeout);
                        results.push(`   - Connection: ✅ Success`);
                        results.push(`   - Socket ID: ${testSocket.id}`);
                        testSocket.disconnect();
                        resolve();
                    });
                    
                    testSocket.on('connect_error', (error) => {
                        clearTimeout(timeout);
                        results.push(`   - Connection: ❌ Failed - ${error.message}`);
                        reject(error);
                    });
                });
            } catch (error) {
                results.push(`   - Connection: ❌ Failed - ${error.message}`);
            }
        } else {
            results.push(`3. WebSocket Connection Test: ❌ Skip (No Socket.IO)`);
        }
        
        // 4. 检查环境信息
        results.push(`4. Environment Info:`);
        results.push(`   - URL: ${window.location.href}`);
        results.push(`   - Protocol: ${window.location.protocol}`);
        results.push(`   - User Agent: ${navigator.userAgent.substring(0, 50)}...`);
        
        // 显示结果
        content.innerHTML = `<pre>${results.join('\n')}</pre>`;
        
        // 自动隐藏面板（10秒后）
        setTimeout(() => {
            if (this.panel) {
                this.panel.style.opacity = '0.7';
            }
        }, 10000);
    }

    refresh() {
        this.runDiagnostics();
    }

    hide() {
        if (this.panel) {
            this.panel.remove();
        }
    }

    show() {
        if (!document.getElementById('websocket-debug-panel')) {
            this.createDebugUI();
            this.runDiagnostics();
        }
    }
}

// 全局实例
window.wsDebug = new WebSocketDebugTool();

// 控制台快捷命令
console.log('🔍 WebSocket Debug Tool loaded. Use wsDebug.show() to display panel.'); 