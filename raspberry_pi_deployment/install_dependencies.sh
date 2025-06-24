#!/bin/bash
# Obscura No.7 Virtual Telescope - Raspberry Pi Installation Script

echo "🔭 Installing Obscura No.7 Virtual Telescope on Raspberry Pi..."
echo "========================================================"

# 更新系统
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# 安装Python3和pip（如果还没有）
echo "🐍 Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# 安装系统级依赖
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    git \
    curl \
    i2c-tools \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5

# 启用I2C和SPI（用于硬件通信）
echo "⚡ Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# 创建Python虚拟环境
echo "🐍 Creating Python virtual environment..."
python3 -m venv obscura_env
source obscura_env/bin/activate

# 安装Python依赖
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 尝试安装树莓派专用库（如果失败则跳过）
echo "🍓 Installing Raspberry Pi specific libraries..."
pip install RPi.GPIO gpiozero spidev smbus || echo "⚠️ Some Pi-specific libraries failed to install (normal if not on Pi)"

# 创建目录结构
echo "📁 Creating directory structure..."
mkdir -p logs
mkdir -p outputs/images
mkdir -p outputs/workflow_results

# 设置权限
echo "🔒 Setting permissions..."
chmod +x main_telescope.py
chmod +x telescope_workflow.py

# 创建启动脚本
echo "🚀 Creating launch script..."
cat > launch_telescope.sh << 'EOF'
#!/bin/bash
# Obscura No.7 启动脚本
cd /home/pi/obscura_telescope
source obscura_env/bin/activate
python3 main_telescope.py
EOF

chmod +x launch_telescope.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Test hardware connections"
echo "3. Run: ./launch_telescope.sh"
echo ""
echo "🌟 Happy stargazing! 🔭" 