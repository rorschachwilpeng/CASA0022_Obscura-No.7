#!/bin/bash

# 天气艺术生成器树莓派运行脚本
# 此脚本用于在树莓派上运行weather_art_generator.py

echo "正在启动天气艺术生成器..."

# 确保工作目录是脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查依赖是否已安装
echo "检查依赖..."
pip3 install requests pillow python-dotenv argparse

# 检查.env文件是否存在
if [ ! -f .env ]; then
  echo "错误：.env文件不存在。请确保已创建.env文件并填入API密钥。"
  exit 1
fi

# 运行Python脚本
echo "开始生成天气艺术..."
python3 weather_art_generator.py --city "London" --output "weather_art.png"

# 检查是否成功生成图像
if [ -f weather_art.png ]; then
  echo "成功生成图像：weather_art.png"
  echo "要在屏幕上显示图像，请使用适合您树莓派屏幕的显示方法。"
else
  echo "图像生成失败，请检查错误信息。"
fi 