#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 编码器距离控制算法
将编码器旋转转换为虚拟地理距离控制
"""

import smbus
import time
import signal
import sys
import math
from datetime import datetime

# Seesaw寄存器定义
SEESAW_STATUS_BASE = 0x00
SEESAW_STATUS_SWRST = 0x7F
SEESAW_GPIO_BASE = 0x01
SEESAW_GPIO_DIRCLR_BULK = 0x03
SEESAW_GPIO_BULK = 0x04
SEESAW_GPIO_PULLENSET = 0x0B

class DistanceController:
    def __init__(self, bus_number=3, address=0x36):
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        
        # 编码器引脚配置
        self.encoder_a_pin = 8
        self.encoder_b_pin = 14
        self.button_pin = 24
        
        # 编码器状态
        self.last_a_state = False
        self.last_b_state = False
        self.encoder_position = 0
        
        # 距离控制参数
        self.distance_config = {
            'min_distance': 100,        # 最小距离：100米
            'max_distance': 10000,      # 最大距离：10公里
            'base_step': 100,           # 基础步长：100米
            'acceleration_threshold': 5, # 加速阈值：连续旋转5次
            'acceleration_factor': 2,   # 加速倍数
            'deceleration_time': 2.0   # 减速时间：2秒
        }
        
        # 当前状态
        self.current_distance = 1000  # 初始距离：1公里
        self.target_distance = 1000
        self.last_rotation_time = 0
        self.rotation_velocity = 0    # 旋转速度（次/秒）
        self.consecutive_rotations = 0
        
        # 平滑算法参数
        self.smoothing_enabled = True
        self.smoothing_factor = 0.15  # 平滑系数
        
    def connect(self):
        """连接到I2C总线"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            print(f"✅ 成功连接到I2C总线 {self.bus_number}")
            return True
        except Exception as e:
            print(f"❌ 连接I2C总线失败: {e}")
            return False
    
    def write_register(self, reg_base, reg_addr, data):
        """写入seesaw寄存器"""
        try:
            if isinstance(data, int):
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr, data])
            else:
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            return False
    
    def read_register(self, reg_base, reg_addr, length=1):
        """读取seesaw寄存器"""
        try:
            self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr])
            time.sleep(0.005)
            
            if length == 1:
                data = self.bus.read_byte(self.address)
                return data
            else:
                data = self.bus.read_i2c_block_data(self.address, 0, length)
                return data
        except Exception as e:
            return None
    
    def software_reset(self):
        """软件复位"""
        print("🔄 执行软件复位...")
        success = self.write_register(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
        if success:
            time.sleep(0.5)
            print("✅ 复位完成")
        return success
    
    def init_encoder(self):
        """初始化编码器"""
        print("⚙️ 初始化编码器...")
        
        # 引脚掩码
        pin_mask = (1 << self.encoder_a_pin) | (1 << self.encoder_b_pin) | (1 << self.button_pin)
        pin_bytes = [
            (pin_mask >> 24) & 0xFF,
            (pin_mask >> 16) & 0xFF, 
            (pin_mask >> 8) & 0xFF,
            pin_mask & 0xFF
        ]
        
        # 设置为输入并启用上拉
        success1 = self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
        success2 = self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, pin_bytes)
        
        if success1 and success2:
            print("✅ 编码器初始化完成")
            
            # 获取初始状态
            a_state, b_state, _, _ = self.read_gpio_state()
            if a_state is not None:
                self.last_a_state = a_state
                self.last_b_state = b_state
                print(f"📍 初始编码器状态: A={a_state}, B={b_state}")
            
            return True
        else:
            print("❌ 编码器初始化失败")
            return False
    
    def read_gpio_state(self):
        """读取GPIO状态"""
        try:
            gpio_data = self.read_register(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
            if gpio_data and len(gpio_data) >= 4:
                gpio_state = (gpio_data[0] << 24) | (gpio_data[1] << 16) | (gpio_data[2] << 8) | gpio_data[3]
                
                a_state = bool((gpio_state >> self.encoder_a_pin) & 1)
                b_state = bool((gpio_state >> self.encoder_b_pin) & 1)
                button_state = not bool((gpio_state >> self.button_pin) & 1)
                
                return a_state, b_state, button_state, gpio_state
            else:
                return None, None, None, None
        except Exception as e:
            return None, None, None, None
    
    def process_encoder_rotation(self, a_state, b_state):
        """处理编码器旋转"""
        direction = None
        
        # 检查A相变化
        if a_state != self.last_a_state:
            if a_state:  # A相上升沿
                if b_state:
                    self.encoder_position += 1
                    direction = 1  # 顺时针
                else:
                    self.encoder_position -= 1
                    direction = -1  # 逆时针
        
        # 检查B相变化（提高精度）
        elif b_state != self.last_b_state:
            if b_state:  # B相上升沿
                if not a_state:
                    self.encoder_position += 1
                    direction = 1  # 顺时针
                else:
                    self.encoder_position -= 1
                    direction = -1  # 逆时针
        
        return direction
    
    def calculate_adaptive_step(self, direction, current_time):
        """计算自适应步长"""
        time_since_last = current_time - self.last_rotation_time
        
        # 计算旋转速度
        if time_since_last > 0:
            self.rotation_velocity = 1.0 / time_since_last
        
        # 检查是否连续快速旋转
        if time_since_last < 0.5:  # 500ms内连续旋转
            self.consecutive_rotations += 1
        else:
            self.consecutive_rotations = 0
        
        # 基础步长
        step = self.distance_config['base_step']
        
        # 自适应加速
        if self.consecutive_rotations >= self.distance_config['acceleration_threshold']:
            # 快速旋转时增大步长
            acceleration = min(self.consecutive_rotations / 5, 4)  # 最大4倍加速
            step *= (1 + acceleration * self.distance_config['acceleration_factor'])
        
        # 根据当前距离调整步长（远距离时步长更大）
        if self.current_distance > 5000:  # 超过5公里
            step *= 2
        elif self.current_distance > 2000:  # 超过2公里
            step *= 1.5
        
        return int(step) * direction
    
    def update_distance(self, direction):
        """更新距离值"""
        current_time = time.time()
        
        # 计算距离变化
        distance_change = self.calculate_adaptive_step(direction, current_time)
        
        # 更新目标距离
        new_target = self.target_distance + distance_change
        
        # 限制在有效范围内
        self.target_distance = max(
            self.distance_config['min_distance'],
            min(self.distance_config['max_distance'], new_target)
        )
        
        # 平滑处理
        if self.smoothing_enabled:
            # 指数平滑
            distance_diff = self.target_distance - self.current_distance
            self.current_distance += distance_diff * self.smoothing_factor
        else:
            self.current_distance = self.target_distance
        
        self.last_rotation_time = current_time
        
        return distance_change
    
    def format_distance(self, distance):
        """格式化距离显示"""
        if distance >= 1000:
            return f"{distance/1000:.1f}km"
        else:
            return f"{int(distance)}m"
    
    def get_distance_category(self, distance):
        """获取距离类别"""
        if distance <= 500:
            return "近距离", "🔍"
        elif distance <= 2000:
            return "中距离", "🚶"
        elif distance <= 5000:
            return "远距离", "🚗"
        else:
            return "超远距离", "✈️"
    
    def display_status(self, distance_change=None, direction_name=None):
        """显示当前状态"""
        category, icon = self.get_distance_category(self.current_distance)
        
        # 创建距离条
        progress = (self.current_distance - self.distance_config['min_distance']) / \
                  (self.distance_config['max_distance'] - self.distance_config['min_distance'])
        bar_length = 20
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\r{icon} 距离: {self.format_distance(self.current_distance):<8} "
              f"[{bar}] {progress*100:5.1f}% "
              f"({category}) ", end="", flush=True)
        
        if distance_change and direction_name:
            print(f"| {direction_name} {abs(distance_change):+d}m")
        else:
            print()
    
    def run_distance_control(self, duration=300):
        """运行距离控制系统"""
        print("=" * 80)
        print("🎯 Obscura No.7 - 距离控制系统")
        print("=" * 80)
        print("📏 距离范围:", 
              f"{self.format_distance(self.distance_config['min_distance'])} - "
              f"{self.format_distance(self.distance_config['max_distance'])}")
        print("📐 基础步长:", f"{self.distance_config['base_step']}m")
        print("🔄 自适应加速: 启用")
        print("🎨 平滑算法: 启用" if self.smoothing_enabled else "🎨 平滑算法: 禁用")
        print(f"⏱️ 运行时长: {duration}秒")
        print("-" * 80)
        print("🎮 操作说明:")
        print("   🔄 旋转编码器: 调整距离")
        print("   🔘 按下按钮: 确认当前距离并退出")
        print("   ⚡ 快速旋转: 自动加速调整")
        print("=" * 80)
        
        start_time = time.time()
        last_display_time = 0
        button_presses = 0
        total_rotations = 0
        
        # 显示初始状态
        self.display_status()
        
        while time.time() - start_time < duration:
            # 读取编码器状态
            a_state, b_state, button_state, raw_gpio = self.read_gpio_state()
            
            if a_state is not None:
                current_time = time.time()
                
                # 处理编码器旋转
                direction = self.process_encoder_rotation(a_state, b_state)
                if direction:
                    total_rotations += 1
                    distance_change = self.update_distance(direction)
                    direction_name = "顺时针" if direction > 0 else "逆时针"
                    
                    # 立即显示变化
                    self.display_status(distance_change, direction_name)
                
                # 处理按钮按压
                if button_state:
                    button_presses += 1
                    print(f"\n🔘 按钮按下! 确认距离: {self.format_distance(self.current_distance)}")
                    break
                
                # 定期更新显示（平滑动画）
                if current_time - last_display_time > 0.1:  # 10Hz更新
                    if self.smoothing_enabled and abs(self.target_distance - self.current_distance) > 1:
                        self.display_status()
                    last_display_time = current_time
                
                # 更新编码器状态
                self.last_a_state = a_state
                self.last_b_state = b_state
            
            time.sleep(0.02)  # 50Hz采样率
        
        print("\n" + "=" * 80)
        print("📊 距离控制会话统计:")
        print(f"   最终距离: {self.format_distance(self.current_distance)}")
        print(f"   总旋转次数: {total_rotations}")
        print(f"   按钮按压次数: {button_presses}")
        print(f"   运行时长: {time.time() - start_time:.1f}秒")
        
        category, icon = self.get_distance_category(self.current_distance)
        print(f"   距离类别: {category} {icon}")
        
        return int(self.current_distance)

def signal_handler(sig, frame):
    print("\n\n🛑 收到中断信号，正在退出...")
    sys.exit(0)

def main():
    print("🚀 启动Obscura No.7距离控制系统...")
    signal.signal(signal.SIGINT, signal_handler)
    
    controller = DistanceController(bus_number=3, address=0x36)
    
    try:
        # 初始化
        if not controller.connect():
            return
        
        if not controller.software_reset():
            return
        
        if not controller.init_encoder():
            return
        
        # 运行距离控制
        final_distance = controller.run_distance_control(duration=300)  # 5分钟
        
        print(f"\n🎉 距离控制完成!")
        print(f"📍 选定距离: {controller.format_distance(final_distance)}")
        print("📝 此距离值可用于后续的天气艺术生成...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断系统")
    except Exception as e:
        print(f"\n❌ 系统运行错误: {e}")
    
    print("🏁 距离控制系统结束")

if __name__ == "__main__":
    main()
