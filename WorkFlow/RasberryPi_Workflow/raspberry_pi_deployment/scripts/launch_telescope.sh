#!/bin/bash
# Obscura No.7 Virtual Telescope Launch Script

echo "🔭 Starting Obscura No.7 Virtual Telescope..."

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 检查是否在项目目录中
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in $PWD"
    echo "Please check the project structure"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "obscura_env" ]; then
    echo "🐍 Activating Python virtual environment..."
    source obscura_env/bin/activate
else
    echo "⚠️ Virtual environment not found, using system Python"
fi

# 检查依赖
echo "📦 Checking dependencies..."
python3 -c "import requests, datetime, json, os" 2>/dev/null || {
    echo "❌ Missing dependencies. Please run: ./install_dependencies.sh"
    exit 1
}

# 启动程序
echo "🚀 Launching telescope..."
python3 main.py --mode exhibition

echo "🔭 Telescope session ended." 