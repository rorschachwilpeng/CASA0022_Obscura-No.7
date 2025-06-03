#!/bin/bash

# 天气艺术生成器自动更新脚本
# 此脚本用于定期生成新的天气艺术图像并显示在电子墨水屏幕上
# 推荐添加到crontab中，例如每6小时更新一次

# 确保工作目录是脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 设置配置参数（可根据需要修改）
CITY="London"  # 城市名称
OUTPUT_FILE="weather_art.png"  # 输出文件路径
LOG_FILE="weather_art.log"     # 日志文件路径

# 记录更新时间
echo "=========================================" >> "$LOG_FILE"
echo "开始更新: $(date)" >> "$LOG_FILE"

# 检查.env文件是否存在
if [ ! -f .env ]; then
  echo "错误：.env文件不存在。请确保已创建.env文件并填入API密钥。" >> "$LOG_FILE"
  exit 1
fi

# 运行Python脚本生成图像
echo "正在生成天气艺术..." >> "$LOG_FILE"
python3 weather_art_generator.py --city "$CITY" --output "$OUTPUT_FILE" >> "$LOG_FILE" 2>&1

# 检查是否成功生成图像
if [ ! -f "$OUTPUT_FILE" ]; then
  echo "错误：图像生成失败，请检查日志获取详情。" >> "$LOG_FILE"
  exit 1
fi

echo "成功生成图像: $OUTPUT_FILE" >> "$LOG_FILE"

# 在电子墨水屏幕上显示图像
echo "正在更新电子墨水屏幕..." >> "$LOG_FILE"

# 根据实际情况选择是否使用模拟模式
# 在实际部署时，移除--simulate参数
python3 display_on_eink.py --image "$OUTPUT_FILE" --simulate >> "$LOG_FILE" 2>&1

echo "更新完成: $(date)" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE" 