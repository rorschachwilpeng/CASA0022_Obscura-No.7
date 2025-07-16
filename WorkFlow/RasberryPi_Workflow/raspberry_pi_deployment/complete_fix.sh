#!/bin/bash
# Obscura No.7 完整修复脚本 v2.0
# 解决触摸屏精度、方向参数和pygame初始化问题

echo "🔧 Obscura No.7 完整修复启动 v2.0"
echo "=========================================="

# 设置工作目录
cd "$(dirname "$0")"

echo "📝 已修复的问题:"
echo "   ✅ pygame字体初始化问题"
echo "   ✅ 触摸坐标映射偏置问题（+30像素X轴校准）"
echo "   ✅ 方向传感器容错处理增强"
echo "   ✅ 硬件参数读取优化"
echo "   ✅ 详细调试日志系统"
echo ""

echo "🔧 新增的诊断工具:"
echo "   🎯 快速触摸测试工具"
echo "   📐 触摸偏置诊断器"
echo "   🧭 方向传感器状态监控"
echo ""

# 1. 环境变量设置
echo "🖱️ 配置触摸屏环境..."
export SDL_VIDEODRIVER=x11
export SDL_MOUSEDEV=/dev/input/event0
export DISPLAY=:0
export PYGAME_HIDE_SUPPORT_PROMPT=1

# 2. 检查pygame环境和字体修复
echo "📦 检查pygame环境和字体修复..."
python3 -c "
import pygame
print(f'✅ Pygame版本: {pygame.version.ver}')
pygame.init()
print('✅ pygame初始化: 成功')
pygame.font.init()
print('✅ 字体系统初始化: 成功')
info = pygame.display.Info()
print(f'✅ 显示信息: {info.current_w}x{info.current_h}')

# 测试字体创建（测试修复效果）
try:
    font1 = pygame.font.Font(None, 32)
    print('✅ 默认字体创建: 成功')
except:
    try:
        font2 = pygame.font.SysFont('arial', 32)
        print('✅ 系统arial字体创建: 成功')
    except:
        font3 = pygame.font.SysFont(None, 32)
        print('✅ 系统默认字体创建: 成功')

pygame.quit()
print('✅ pygame清理: 成功')
" 2>/dev/null || echo "⚠️ pygame环境检查失败"

# 3. 检查硬件设备
echo "🔌 检查硬件设备..."
if [ -c "/dev/input/event0" ]; then
    echo "✅ 输入设备 /dev/input/event0 存在"
else
    echo "⚠️ 输入设备 /dev/input/event0 不存在"
fi

# 检查I2C设备
for bus in 3 4 5; do
    if [ -c "/dev/i2c-$bus" ]; then
        echo "✅ I2C总线 $bus 可用"
    else
        echo "⚠️ I2C总线 $bus 不可用"
    fi
done

# 4. 生成修复状态报告
echo ""
echo "🔍 生成修复状态报告..."
cat > fix_status_report.txt << EOF
Obscura No.7 修复状态报告 v2.0
生成时间: $(date)
========================================

已应用的修复:
✅ pygame字体初始化顺序修复
✅ 触摸坐标校准偏移（+30px X轴）
✅ 屏幕分辨率自动检测
✅ 方向传感器容错处理增强
✅ 硬件参数读取逻辑完善
✅ 详细调试日志系统

新增的工具:
🎯 quick_touch_test.py - 快速触摸测试
📐 touch_calibration.py - 触摸偏置诊断
🔧 fix_verification.py - 功能验证工具

系统信息:
- 系统: $(uname -a)
- Python版本: $(python3 --version)
- 屏幕分辨率: $(python3 -c "import pygame; pygame.init(); info = pygame.display.Info(); print(f'{info.current_w}x{info.current_h}'); pygame.quit()" 2>/dev/null || echo "检测失败")

硬件状态:
- 触摸设备: $([ -c "/dev/input/event0" ] && echo "✅ 正常" || echo "❌ 不可用")
- I2C总线3: $([ -c "/dev/i2c-3" ] && echo "✅ 正常" || echo "❌ 不可用")
- I2C总线4: $([ -c "/dev/i2c-4" ] && echo "✅ 正常" || echo "❌ 不可用")
- I2C总线5: $([ -c "/dev/i2c-5" ] && echo "✅ 正常" || echo "❌ 不可用")

修复验证建议:
1. 运行快速触摸测试: python3 quick_touch_test.py
2. 运行完整校准: python3 touch_calibration.py
3. 启动展览模式: python3 main.py --mode exhibition

EOF

echo "✅ 修复状态报告已生成: fix_status_report.txt"

# 5. 交互式选择
echo ""
echo "🚀 选择要执行的操作:"
echo "1. 快速触摸测试（推荐先执行）"
echo "2. 完整功能验证"
echo "3. 触摸校准和偏置诊断"
echo "4. 直接启动展览模式"
echo "5. 查看系统信息"
echo "6. 退出"

read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo "🎯 启动快速触摸测试..."
        echo "💡 这将测试pygame字体修复和触摸校准效果"
        if [ -f "quick_touch_test.py" ]; then
            python3 quick_touch_test.py
        else
            echo "❌ 找不到 quick_touch_test.py"
            echo "   请确保你在正确的目录中运行此脚本"
        fi
        ;;
    2)
        echo "🔧 运行完整功能验证..."
        python3 fix_verification.py
        ;;
    3)
        echo "📐 启动触摸校准和偏置诊断..."
        echo "💡 选择选项4进行触摸偏置诊断"
        python3 touch_calibration.py
        ;;
    4)
        echo "🚀 启动展览模式..."
        python3 main.py --mode exhibition --log-level DEBUG
        ;;
    5)
        echo "📊 系统信息:"
        echo "=========================================="
        cat fix_status_report.txt
        echo ""
        echo "🔍 详细诊断信息:"
        echo "系统和Python环境:"
        python3 --version
        python3 -c "import pygame; print(f'pygame版本: {pygame.version.ver}')"
        
        echo "屏幕分辨率检测:"
        python3 -c "
import pygame
pygame.init()
info = pygame.display.Info()
print(f'检测到分辨率: {info.current_w}x{info.current_h}')
pygame.quit()
"
        
        echo "输入设备:"
        ls -la /dev/input/
        
        echo "触摸设备详情:"
        cat /proc/bus/input/devices | grep -A 5 -B 5 -i "touch" || echo "未找到触摸设备信息"
        ;;
    6)
        echo "👋 退出修复脚本"
        exit 0
        ;;
    *)
        echo "❌ 无效选择，退出"
        exit 1
        ;;
esac

echo ""
echo "📚 有用的命令:"
echo "   - 触摸问题诊断: python3 quick_touch_test.py"
echo "   - 触摸校准: python3 touch_calibration.py"
echo "   - 功能验证: python3 fix_verification.py"
echo "   - 查看日志: tail -f logs/exhibition.log"
echo "   - 完整启动: python3 main.py --mode exhibition"

echo "👋 修复脚本执行完成" 