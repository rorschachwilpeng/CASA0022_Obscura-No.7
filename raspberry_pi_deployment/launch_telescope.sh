#!/bin/bash
# Obscura No.7 Virtual Telescope Launch Script

echo "🔭 Starting Obscura No.7 Virtual Telescope..."

# 检查是否在项目目录中
if [ ! -f "main_telescope.py" ]; then
    echo "❌ Error: main_telescope.py not found"
    echo "Please run this script from the raspberry_pi_deployment directory"
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
python3 main_telescope.py

echo "🔭 Telescope session ended." 