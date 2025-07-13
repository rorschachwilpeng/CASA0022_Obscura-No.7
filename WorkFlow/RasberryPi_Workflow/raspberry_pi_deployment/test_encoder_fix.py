#!/usr/bin/env python3
"""
编码器高灵敏度测试脚本
用于验证Distance Encoder方向取反和高灵敏度响应
检测每一次旋转变化
"""

import time
import json
from core.raspberry_pi_hardware import RaspberryPiHardware

def test_encoder_direction_and_sensitivity():
    """测试编码器方向和灵敏度"""
    print("🔧 编码器修复测试")
    print("=" * 60)
    
    # 加载配置
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        config = {}
    
    # 初始化硬件
    hardware = RaspberryPiHardware(config)
    
    # 检查硬件状态
    status = hardware.get_hardware_status()
    print("📊 硬件状态:")
    for key, value in status.items():
        print(f"   {key}: {'✅' if value else '❌'}")
    
    if not status['encoder_available']:
        print("❌ Distance Encoder不可用，无法进行测试")
        return
    
    print("\n🧪 开始编码器测试...")
    print("🎮 操作说明:")
    print("   🔄 顺时针旋转Distance Encoder - 应该增加数值")
    print("   🔄 逆时针旋转Distance Encoder - 应该减少数值")
    print("   ⚡ 高灵敏度模式 - 检测每一次旋转变化")
    print("   ⏰ 旋转Time Encoder - 测试时间偏移调整")
    print("   🔘 按Time Encoder按钮 - 结束测试")
    print("=" * 60)
    
    # 初始化变量
    current_distance = 5000  # 5km
    current_time_offset = 5  # +5年
    
    # 获取初始状态
    distance_a, distance_b, _ = hardware._read_seesaw_gpio_state()
    time_a, time_b, _ = hardware._read_time_encoder_gpio_state()
    
    if distance_a is None:
        print("❌ 无法读取Distance Encoder状态")
        return
    
    print(f"🎛️ Distance Encoder初始状态: A={distance_a}, B={distance_b}")
    if time_a is not None:
        print(f"⏰ Time Encoder初始状态: A={time_a}, B={time_b}")
    
    last_distance_a = distance_a
    last_distance_b = distance_b
    last_time_a = time_a if time_a is not None else False
    last_time_b = time_b if time_b is not None else False
    
    # 轻量级防抖变量
    last_distance_change = 0
    last_time_change = 0
    simple_debounce = 0.05  # 50ms轻量级防抖
    
    distance_changes = 0
    time_changes = 0
    
    start_time = time.time()
    
    try:
        while True:
            # 1. 测试Distance Encoder
            distance_a, distance_b, _ = hardware._read_seesaw_gpio_state()
            
            if distance_a is not None:
                direction = hardware._process_encoder_rotation(
                    distance_a, distance_b,
                    last_distance_a, last_distance_b,
                    0,
                    invert_direction=True  # Distance Encoder取反
                )
                
                if direction != 0:
                    # 轻量级防抖：只防止极短时间内的重复触发
                    now = time.time()
                    if now - last_distance_change >= simple_debounce:
                        current_distance += 1000 * direction  # 1km步长
                        current_distance = max(1000, min(50000, current_distance))
                        distance_changes += 1
                        last_distance_change = now
                        
                        direction_text = "顺时针 ↗" if direction > 0 else "逆时针 ↙"
                        print(f"🔄 Distance Encoder: {direction_text} → {current_distance/1000:.1f}km (#{distance_changes})")
                        print(f"   状态: A={last_distance_a}→{distance_a}, B={last_distance_b}→{distance_b}")
                
                last_distance_a = distance_a
                last_distance_b = distance_b
            
            # 2. 测试Time Encoder
            time_a, time_b, _ = hardware._read_time_encoder_gpio_state()
            
            if time_a is not None:
                time_direction = hardware._process_encoder_rotation(
                    time_a, time_b,
                    last_time_a, last_time_b,
                    0,
                    invert_direction=False  # Time Encoder保持原始方向
                )
                
                if time_direction != 0:
                    # 轻量级防抖：只防止极短时间内的重复触发
                    now = time.time()
                    if now - last_time_change >= simple_debounce:
                        current_time_offset += time_direction
                        current_time_offset = max(0, min(50, current_time_offset))
                        time_changes += 1
                        last_time_change = now
                        
                        direction_text = "顺时针 ↗" if time_direction > 0 else "逆时针 ↙"
                        print(f"⏰ Time Encoder: {direction_text} → +{current_time_offset}年 (#{time_changes})")
                        print(f"   状态: A={last_time_a}→{time_a}, B={last_time_b}→{time_b}")
                
                last_time_a = time_a
                last_time_b = time_b
            
            # 3. 检查退出按钮
            button_pressed = hardware._read_time_encoder_button_state()
            if button_pressed:
                print(f"\n🔘 测试结束")
                break
            
            # 4. 显示当前状态（每2秒更新一次）
            if int(time.time() - start_time) % 2 == 0:
                elapsed = time.time() - start_time
                print(f"\r📊 测试进行中... 距离:{current_distance/1000:.1f}km, 时间:+{current_time_offset}年, "
                      f"变化次数: Distance={distance_changes}, Time={time_changes}, "
                      f"运行时间:{elapsed:.0f}s", end="", flush=True)
            
            time.sleep(0.01)  # 10ms刷新率，检测每一次旋转
            
    except KeyboardInterrupt:
        print(f"\n⏹️ 测试被用户中断")
    
    finally:
        hardware.cleanup()
    
    # 测试总结
    print(f"\n" + "=" * 60)
    print(f"📋 测试总结:")
    print(f"   🔄 Distance Encoder变化次数: {distance_changes}")
    print(f"   ⏰ Time Encoder变化次数: {time_changes}")
    print(f"   ⏱️ 总测试时间: {time.time() - start_time:.1f}秒")
    
    if distance_changes > 0:
        print(f"   ✅ Distance Encoder响应正常")
        print(f"   📝 请验证修复效果：")
        print(f"      - 顺时针旋转应该增加距离值")
        print(f"      - 逆时针旋转应该减少距离值")
        print(f"      - 高灵敏度：检测每一次旋转变化")
    else:
        print(f"   ❌ Distance Encoder无响应 - 检查硬件连接")
    
    if time_changes > 0:
        print(f"   ✅ Time Encoder响应正常")
        print(f"   📝 Time Encoder方向保持原始逻辑（未取反）")
        print(f"   ⚡ 高灵敏度：四倍频解码 + 10ms采样 + 轻量级防抖")
    else:
        print(f"   ⚠️ Time Encoder无响应或未连接")

def main():
    """主函数"""
    try:
        test_encoder_direction_and_sensitivity()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 