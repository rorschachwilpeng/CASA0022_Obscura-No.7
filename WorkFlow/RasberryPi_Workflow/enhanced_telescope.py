#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 增强版三设备集成虚拟望远镜系统
集成距离编码器、方向磁感器和时间编码器的完整虚拟地理探索系统
"""

import smbus
import time
import signal
import sys
import math
import requests
from PIL import Image, ImageTk
import tkinter as tk
import io
import os
from datetime import datetime, timedelta

# Seesaw寄存器定义
SEESAW_STATUS_BASE = 0x00
SEESAW_STATUS_SWRST = 0x7F
SEESAW_GPIO_BASE = 0x01
SEESAW_GPIO_DIRCLR_BULK = 0x03
SEESAW_GPIO_BULK = 0x04
SEESAW_GPIO_PULLENSET = 0x0B

# QMC5883L寄存器定义
QMC5883L_ADDR = 0x0D
QMC5883L_DATA_OUTPUT_X_LSB = 0x00
QMC5883L_DATA_OUTPUT_X_MSB = 0x01
QMC5883L_DATA_OUTPUT_Y_LSB = 0x02
QMC5883L_DATA_OUTPUT_Y_MSB = 0x03
QMC5883L_DATA_OUTPUT_Z_LSB = 0x04
QMC5883L_DATA_OUTPUT_Z_MSB = 0x05
QMC5883L_STATUS = 0x06
QMC5883L_TEMP_LSB = 0x07
QMC5883L_TEMP_MSB = 0x08
QMC5883L_CONFIG = 0x09
QMC5883L_CONFIG2 = 0x0A
QMC5883L_PERIOD = 0x0B
QMC5883L_CHIP_ID = 0x0D

class EnhancedTelescope:
    def __init__(self, api_key, distance_bus=3, compass_bus=4, time_bus=5, encoder_addr=0x36):
        # I2C配置
        self.distance_bus_number = distance_bus
        self.compass_bus_number = compass_bus
        self.time_bus_number = time_bus
        self.encoder_address = encoder_addr
        
        # I2C总线对象
        self.distance_bus = None
        self.compass_bus = None
        self.time_bus = None
        
        # 编码器引脚配置（所有编码器使用相同配置）
        self.encoder_a_pin = 8
        self.encoder_b_pin = 14
        self.button_pin = 24
        
        # 距离编码器状态
        self.distance_encoder_position = 0
        self.distance_last_a_state = False
        self.distance_last_b_state = False
        self.current_distance = 1000  # 初始距离：1公里
        
        # 时间编码器状态
        self.time_encoder_position = 0
        self.time_last_a_state = False
        self.time_last_b_state = False
        self.current_time_offset = 0  # 时间偏移（年份，0=当前年份）
        
        # 距离控制参数
        self.distance_config = {
            'min_distance': 1000,       # 最小距离：1公里
            'max_distance': 50000,      # 最大距离：50公里
            'base_step': 1000,          # 基础步长：1公里
            'acceleration_threshold': 3, # 加速阈值
            'acceleration_factor': 1.5,   # 加速倍数
        }
        
        # 时间控制参数（用于未来环境预测）
        self.time_config = {
            'min_offset': 0,            # 最小时间偏移：当前年份
            'max_offset': 50,           # 最大时间偏移：+50年（2075年）
            'base_step': 1,             # 基础步长：1年
            'acceleration_threshold': 3, # 加速阈值
            'acceleration_factor': 2,    # 加速倍数
        }
        
        # 磁感器配置
        self.compass_config = {
            'samples_for_calibration': 10,
            'direction_deadband': 5,
            'smoothing_factor': 0.8,
        }
        
        # 当前状态
        self.current_direction = 0
        self.north_calibration = None
        self.last_smooth_angle = 0
        
        # 显示控制（用于检测参数变化）
        self.last_displayed_distance = None
        self.last_displayed_time_offset = None
        self.last_displayed_direction = None
        
        # 旋转计时器（用于加速检测）
        self.distance_last_rotation_time = 0
        self.distance_consecutive_rotations = 0
        self.time_last_rotation_time = 0
        self.time_consecutive_rotations = 0
        
        # API配置
        self.api_key = api_key
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_location = (51.5074, -0.1278)  # 伦敦市中心
        
        # 屏幕配置
        self.detect_screen_resolution()
        
    def detect_screen_resolution(self):
        """自动检测屏幕分辨率"""
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            self.screen_width = temp_root.winfo_screenwidth()
            self.screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
            print(f"🖥️ 检测到屏幕分辨率: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            self.screen_width = 480
            self.screen_height = 800
            print(f"🖥️ 使用默认分辨率: {self.screen_width}x{self.screen_height}")
    
    # ========== I2C连接部分 ==========
    
    def connect_devices(self):
        """连接到所有I2C设备"""
        success = True
        
        # 连接距离编码器
        try:
            self.distance_bus = smbus.SMBus(self.distance_bus_number)
            print(f"✅ 距离编码器连接成功 (I2C总线 {self.distance_bus_number})")
        except Exception as e:
            print(f"❌ 距离编码器连接失败: {e}")
            success = False
        
        # 连接磁感器
        try:
            self.compass_bus = smbus.SMBus(self.compass_bus_number)
            print(f"✅ 磁感器连接成功 (I2C总线 {self.compass_bus_number})")
        except Exception as e:
            print(f"❌ 磁感器连接失败: {e}")
            success = False
        
        # 连接时间编码器
        try:
            self.time_bus = smbus.SMBus(self.time_bus_number)
            print(f"✅ 时间编码器连接成功 (I2C总线 {self.time_bus_number})")
        except Exception as e:
            print(f"❌ 时间编码器连接失败: {e}")
            success = False
        
        return success
    
    # ========== 编码器通用方法 ==========
    
    def write_encoder_register(self, bus, reg_base, reg_addr, data):
        """写入seesaw寄存器"""
        try:
            if isinstance(data, int):
                bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr, data])
            else:
                bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            return False
    
    def read_encoder_register(self, bus, reg_base, reg_addr, length=1):
        """读取seesaw寄存器"""
        try:
            bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr])
            time.sleep(0.005)
            
            if length == 1:
                data = bus.read_byte(self.encoder_address)
                return data
            else:
                data = bus.read_i2c_block_data(self.encoder_address, 0, length)
                return data
        except Exception as e:
            return None
    
    def init_encoder(self, bus, device_name):
        """初始化编码器"""
        print(f"⚙️ 初始化{device_name}...")
        
        # 软件复位
        success = self.write_encoder_register(bus, SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
        if success:
            time.sleep(0.5)
        
        # 引脚配置
        pin_mask = (1 << self.encoder_a_pin) | (1 << self.encoder_b_pin) | (1 << self.button_pin)
        pin_bytes = [
            (pin_mask >> 24) & 0xFF,
            (pin_mask >> 16) & 0xFF, 
            (pin_mask >> 8) & 0xFF,
            pin_mask & 0xFF
        ]
        
        success1 = self.write_encoder_register(bus, SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
        success2 = self.write_encoder_register(bus, SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, pin_bytes)
        
        if success1 and success2:
            a_state, b_state, _, _ = self.read_encoder_state(bus)
            if a_state is not None:
                print(f"✅ {device_name}初始化完成")
                return True, a_state, b_state
        
        print(f"❌ {device_name}初始化失败")
        return False, False, False
    
    def read_encoder_state(self, bus):
        """读取编码器GPIO状态"""
        try:
            gpio_data = self.read_encoder_register(bus, SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
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
    
    def process_encoder_rotation(self, a_state, b_state, last_a_state, last_b_state, position):
        """处理编码器旋转"""
        direction = None
        new_position = position
        
        if a_state != last_a_state:
            if a_state:  # A相上升沿
                if b_state:
                    new_position += 1
                    direction = 1  # 顺时针
                else:
                    new_position -= 1
                    direction = -1  # 逆时针
        elif b_state != last_b_state:
            if b_state:  # B相上升沿
                if not a_state:
                    new_position += 1
                    direction = 1  # 顺时针
                else:
                    new_position -= 1
                    direction = -1  # 逆时针
        
        return direction, new_position
    
    # ========== 距离编码器方法 ==========
    
    def calculate_distance_step(self, direction, current_time):
        """计算距离步长（简化版：固定1km步长）"""
        # 直接返回固定的1km步长，不使用加速算法
        return self.distance_config['base_step'] * direction
    
    def update_distance(self, direction):
        """更新距离值"""
        current_time = time.time()
        distance_change = self.calculate_distance_step(direction, current_time)
        
        new_distance = self.current_distance + distance_change
        self.current_distance = max(
            self.distance_config['min_distance'],
            min(self.distance_config['max_distance'], new_distance)
        )
        
        return distance_change
    
    # ========== 时间编码器方法 ==========
    
    def calculate_time_step(self, direction, current_time):
        """计算时间步长"""
        time_since_last = current_time - self.time_last_rotation_time
        
        if time_since_last < 0.4:
            self.time_consecutive_rotations += 1
        else:
            self.time_consecutive_rotations = 0
        
        step = self.time_config['base_step']
        
        if self.time_consecutive_rotations >= self.time_config['acceleration_threshold']:
            acceleration = min(self.time_consecutive_rotations / 3, 3)
            step *= (1 + acceleration * self.time_config['acceleration_factor'])
        
        return int(step) * direction
    
    def update_time_offset(self, direction):
        """更新时间偏移值"""
        current_time = time.time()
        time_change = self.calculate_time_step(direction, current_time)
        
        new_time_offset = self.current_time_offset + time_change
        self.current_time_offset = max(
            self.time_config['min_offset'],
            min(self.time_config['max_offset'], new_time_offset)
        )
        
        self.time_last_rotation_time = current_time
        return time_change
    
    def get_target_year(self):
        """获取目标年份"""
        current_year = datetime.now().year
        target_year = current_year + self.current_time_offset
        return target_year
    
    def format_time_offset(self):
        """格式化时间偏移显示"""
        if self.current_time_offset == 0:
            return "当前年份"
        else:
            return f"+{self.current_time_offset}年"
    
    # ========== 磁感器方法（复用原有代码）==========
    
    def init_compass(self):
        """初始化QMC5883L磁感器"""
        print("🧭 初始化磁感器...")
        
        try:
            # 软件复位
            self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG2, 0x80)
            time.sleep(0.1)
            
            # 按照qmc5883l.py的成功配置
            # 配置控制寄存器1: OSR=512, RNG=8G, ODR=200Hz, MODE=Continuous
            self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG, 0x1D)
            time.sleep(0.1)
            
            # 设置周期寄存器（与qmc5883l.py保持一致）
            self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_PERIOD, 0x01)
            time.sleep(0.1)
            
            # 验证芯片ID
            chip_id = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_CHIP_ID)
            print(f"🔍 磁感器芯片ID: 0x{chip_id:02X}")
            
            # 测试读取数据
            test_angle = self.read_compass_angle()
            if test_angle is not None:
                print(f"✅ 磁感器初始化完成，当前角度: {test_angle:.1f}°")
                return True
            else:
                print("❌ 磁感器数据读取失败")
                return False
                
        except Exception as e:
            print(f"❌ 磁感器初始化失败: {e}")
            return False
    
    def read_compass_raw(self):
        """读取磁感器原始数据"""
        try:
            # 检查数据准备状态（增加重试机制）
            max_retries = 3
            for retry in range(max_retries):
                try:
                    status = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_STATUS)
                    if status & 0x01:  # 数据准备好
                        break
                    time.sleep(0.001)  # 等待1ms
                except Exception:
                    if retry == max_retries - 1:
                        return None, None, None
                    time.sleep(0.002)  # I2C错误时等待更长时间
            else:
                return None, None, None  # 数据未准备好
            
            # 读取XYZ数据（按照qmc5883l.py的成功方式）- 增加异常处理
            try:
                # 读取6字节数据 (X_LSB, X_MSB, Y_LSB, Y_MSB, Z_LSB, Z_MSB)
                data = []
                for reg in range(QMC5883L_DATA_OUTPUT_X_LSB, QMC5883L_DATA_OUTPUT_Z_MSB + 1):
                    byte_data = self.compass_bus.read_byte_data(QMC5883L_ADDR, reg)
                    data.append(byte_data)
                
                # 按照qmc5883l.py的方式组合：MSB在前，LSB在后
                x = self._combine_bytes(data[1], data[0])  # MSB, LSB
                y = self._combine_bytes(data[3], data[2])  # MSB, LSB  
                z = self._combine_bytes(data[5], data[4])  # MSB, LSB
                
            except Exception as e:
                return None, None, None
            
            # 检查数据有效性（排除全零或异常值）
            if x == 0 and y == 0 and z == 0:
                return None, None, None
            
            # QMC5883L在连续测量模式下会自动更新数据
            # 无需手动触发，但如果发现数据停止更新，可以重新配置
            # 这里先注释掉重新配置，避免干扰正常测量
            # try:
            #     self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG, 0x1D)
            # except Exception:
            #     pass
            
            return x, y, z
            
        except Exception as e:
            return None, None, None
    
    def _combine_bytes(self, msb, lsb):
        """组合MSB和LSB为有符号16位整数（与qmc5883l.py保持一致）"""
        value = (msb << 8) | lsb
        if value > 32767:
            value -= 65536
        return value
    
    def read_compass_angle(self):
        """读取磁感器角度（0-360度）"""
        x, y, z = self.read_compass_raw()
        
        if x is None or y is None:
            return None
        
        # 计算角度（相对于磁北）
        angle = math.atan2(y, x) * 180 / math.pi
        
        # 转换为0-360度范围
        if angle < 0:
            angle += 360
        
        # 应用平滑滤波
        if hasattr(self, 'last_smooth_angle'):
            alpha = self.compass_config['smoothing_factor']
            # 处理角度跳变（例如从359度到1度）
            diff = angle - self.last_smooth_angle
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            
            angle = self.last_smooth_angle + (1 - alpha) * diff
            if angle < 0:
                angle += 360
            elif angle >= 360:
                angle -= 360
        
        self.last_smooth_angle = angle
        return angle
    
    def calibrate_north_direction(self):
        """校准北方基准方向"""
        print("\n🧭 正在校准北方基准...")
        print("📍 确保设备当前朝向正北方（展台已预设）")
        
        angles = []
        
        for i in range(self.compass_config['samples_for_calibration']):
            angle = self.read_compass_angle()
            if angle is not None:
                angles.append(angle)
                print(f"📐 校准读数 {i+1}/{self.compass_config['samples_for_calibration']}: {angle:.1f}°")
            time.sleep(0.2)
        
        if angles:
            # 计算平均角度（考虑角度的周期性）
            sin_sum = sum(math.sin(math.radians(a)) for a in angles)
            cos_sum = sum(math.cos(math.radians(a)) for a in angles)
            avg_angle = math.degrees(math.atan2(sin_sum, cos_sum))
            
            if avg_angle < 0:
                avg_angle += 360
            
            self.north_calibration = avg_angle
            print(f"✅ 北方基准已设定: {self.north_calibration:.1f}°")
            return True
        else:
            print("❌ 校准失败，无法读取磁感器数据")
            return False
    
    def get_geographic_direction(self):
        """获取相对于北方的地理方向"""
        if self.north_calibration is None:
            return None
        
        raw_angle = self.read_compass_angle()
        if raw_angle is None:
            return None
        
        # 计算相对于校准基准的角度
        geographic_angle = (raw_angle - self.north_calibration) % 360
        return geographic_angle
    
    def get_direction_name(self, angle):
        """将角度转换为方向名称"""
        directions = [
            (0, "正北"), (22.5, "北-东北"), (45, "东北"), (67.5, "东-东北"),
            (90, "正东"), (112.5, "东-东南"), (135, "东南"), (157.5, "南-东南"),
            (180, "正南"), (202.5, "南-西南"), (225, "西南"), (247.5, "西-西南"),
            (270, "正西"), (292.5, "西-西北"), (315, "西北"), (337.5, "北-西北")
        ]
        
        # 找到最接近的方向
        min_diff = 360
        closest_direction = "正北"
        
        for dir_angle, dir_name in directions:
            diff = min(abs(angle - dir_angle), 360 - abs(angle - dir_angle))
            if diff < min_diff:
                min_diff = diff
                closest_direction = dir_name
        
        return closest_direction
    
    def test_compass_communication(self):
        """测试磁感器通信状态"""
        print("\n🧭 磁感器通信测试...")
        
        # 首先验证配置
        try:
            config = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG)
            config2 = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG2)
            print(f"📋 当前配置 - CONFIG: 0x{config:02X}, CONFIG2: 0x{config2:02X}")
        except Exception as e:
            print(f"❌ 配置读取失败: {e}")
        
        successful_reads = 0
        angle_changes = 0
        last_angle = None
        
        for i in range(10):
            try:
                # 测试状态寄存器读取
                status = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_STATUS)
                data_ready = status & 0x01
                
                # 测试原始数据读取
                x, y, z = self.read_compass_raw()
                if x is not None:
                    successful_reads += 1
                    angle = self.read_compass_angle()
                    if angle is not None:
                        if last_angle is not None and abs(angle - last_angle) > 1:
                            angle_changes += 1
                        print(f"第{i+1}次 ✅ 状态:0x{status:02X} X={x:6d} Y={y:6d} Z={z:6d} 角度:{angle:6.1f}°")
                        last_angle = angle
                    else:
                        print(f"第{i+1}次 ⚠️  原始数据读取成功，但角度计算失败")
                else:
                    print(f"第{i+1}次 ❌ 状态:0x{status:02X} 原始数据读取失败")
                
            except Exception as e:
                print(f"第{i+1}次 💥 I2C错误: {e}")
            
            time.sleep(0.2)
        
        print(f"\n📊 测试总结:")
        print(f"   ✅ 成功读取: {successful_reads}/10 次")
        print(f"   🔄 角度变化: {angle_changes} 次")
        print(f"   📈 成功率: {successful_reads*10}%")
        
        if successful_reads < 8:
            print("⚠️  磁感器通信不稳定，可能存在硬件连接问题")
        elif angle_changes == 0:
            print("⚠️  磁感器数据没有变化，可能处于静止状态或配置有问题")
        else:
            print("✅ 磁感器通信正常")
        
        print("🧭 磁感器通信测试完成\n")
    
    # ========== 显示方法 ==========
    
    def format_distance(self, distance):
        """格式化距离显示"""
        if distance >= 1000:
            return f"{distance/1000:.1f}km"
        else:
            return f"{int(distance)}m"
    
    def display_selection_status(self):
        """显示当前选择状态（仅在参数变化时显示）"""
        # 获取当前参数
        current_dir = self.get_geographic_direction()
        target_year = self.get_target_year()
        
        # 调试：显示原始角度信息
        raw_angle = self.read_compass_angle()
        x, y, z = self.read_compass_raw()
        
        # 检查是否有参数变化（降低方向变化阈值）
        direction_changed = (current_dir is not None and 
                           (self.last_displayed_direction is None or 
                            abs(current_dir - self.last_displayed_direction) > 0.5))
        distance_changed = self.current_distance != self.last_displayed_distance
        time_changed = self.current_time_offset != self.last_displayed_time_offset
        
        # 调试模式：总是显示磁感器状态
        debug_display = False
        if x is not None and raw_angle is not None:
            # 每10次循环显示一次调试信息
            if not hasattr(self, '_debug_counter'):
                self._debug_counter = 0
            self._debug_counter += 1
            if self._debug_counter % 10 == 0:
                debug_display = True
        
        # 只有参数变化时才显示，或者调试模式
        if distance_changed or time_changed or direction_changed or debug_display:
            # 简化的方向显示
            if current_dir is not None:
                arrow_symbols = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
                arrow_index = int((current_dir + 22.5) // 45) % 8
                arrow = arrow_symbols[arrow_index]
                direction_display = f"{current_dir:3.0f}°{arrow}"
            else:
                direction_display = "---"
            
            # 简化的输出（适合小屏幕）
            if debug_display and x is not None:
                print(f"\r🔭{self.format_distance(self.current_distance)} 📅{target_year} 🧭{direction_display} [X:{x:4d},Y:{y:4d},原始:{raw_angle:5.1f}°]", 
                      end="", flush=True)
            else:
                print(f"\r🔭{self.format_distance(self.current_distance)} 📅{target_year} 🧭{direction_display}", 
                      end="", flush=True)
            
            # 更新最后显示的值
            self.last_displayed_distance = self.current_distance
            self.last_displayed_time_offset = self.current_time_offset
            self.last_displayed_direction = current_dir
    
    # ========== 主控制流程 ==========
    
    def run_three_parameter_selection(self, timeout=120):
        """运行三参数同时选择"""
        print("=" * 80)
        print("🔭 Obscura No.7 - 增强版三参数虚拟望远镜")
        print("=" * 80)
        print("🎮 操作说明:")
        print("   🔄 距离编码器: 旋转调整探索距离")
        print("   📅 时间编码器: 旋转选择未来预测年份")
        print("   🧭 旋转设备: 选择探索方向")
        print("   🔘 时间编码器按钮: 确认所有参数并开始探索")
        print("=" * 80)
        
        start_time = time.time()
        
        # 初始显示
        print("🔭1.0km 📅2025 🧭---", end="", flush=True)
        
        while time.time() - start_time < timeout:
            # 读取距离编码器
            distance_a, distance_b, distance_button, _ = self.read_encoder_state(self.distance_bus)
            if distance_a is not None:
                direction = self.process_encoder_rotation(
                    distance_a, distance_b, 
                    self.distance_last_a_state, self.distance_last_b_state, 
                    self.distance_encoder_position
                )[0]
                if direction:
                    self.update_distance(direction)
                
                self.distance_last_a_state = distance_a
                self.distance_last_b_state = distance_b
                
                # 距离编码器按钮被禁用（不进行任何操作）
                if distance_button:
                    pass  # 忽略距离编码器的按钮按下
            
            # 短暂延迟，避免I2C总线冲突
            time.sleep(0.005)
            
            # 读取时间编码器（旋转调整年份，按钮确认选择）
            time_a, time_b, time_button, _ = self.read_encoder_state(self.time_bus)
            if time_a is not None:
                direction = self.process_encoder_rotation(
                    time_a, time_b,
                    self.time_last_a_state, self.time_last_b_state,
                    self.time_encoder_position
                )[0]
                if direction:
                    self.update_time_offset(direction)
                
                self.time_last_a_state = time_a
                self.time_last_b_state = time_b
                
                # 时间编码器按钮按下 = 确认所有参数选择
                if time_button:
                    print(f"\n📅 时间编码器确认: 选择预测年份 {self.get_target_year()}")
                    return self.confirm_selection()
            
            # 短暂延迟，避免I2C总线冲突
            time.sleep(0.005)
            
            # 更新显示（仅在参数变化时）
            self.display_selection_status()
            
            time.sleep(0.01)  # 主循环延迟，总体保持约20ms响应速度
        
        print(f"\n⏰ 选择超时，使用当前参数")
        return self.confirm_selection()
    
    def confirm_selection(self):
        """确认当前选择的参数"""
        final_direction = self.get_geographic_direction()
        if final_direction is None:
            final_direction = 0
        
        target_year = self.get_target_year()
        direction_name = self.get_direction_name(final_direction)
        
        print(f"\n\n🔘 参数确认:")
        print(f"   🔭 探索距离: {self.format_distance(self.current_distance)}")
        print(f"   📅 预测年份: {target_year} ({self.format_time_offset()})")
        print(f"   🧭 探索方向: {final_direction:.1f}° ({direction_name})")
        
        return {
            'distance': self.current_distance,
            'direction': final_direction,
            'time_offset': self.current_time_offset,
            'target_year': target_year
        }
    
    def run_enhanced_telescope_session(self):
        """运行增强版望远镜会话"""
        print("🚀 启动Obscura No.7 增强版虚拟望远镜...")
        
        try:
            # 1. 连接设备
            if not self.connect_devices():
                return False
            
            # 2. 初始化所有编码器
            distance_success, distance_a, distance_b = self.init_encoder(self.distance_bus, "距离编码器")
            if distance_success:
                self.distance_last_a_state = distance_a
                self.distance_last_b_state = distance_b
            else:
                return False
            
            time_success, time_a, time_b = self.init_encoder(self.time_bus, "时间编码器")
            if time_success:
                self.time_last_a_state = time_a
                self.time_last_b_state = time_b
            else:
                return False
            
            # 3. 初始化磁感器
            if not self.init_compass():
                return False
            
            # 4. 测试磁感器通信
            self.test_compass_communication()
            
            # 5. 校准北方基准
            if not self.calibrate_north_direction():
                return False
            
            # 6. 磁感器预热（确保连续测量模式稳定）
            print("\n🔥 磁感器预热中...")
            for i in range(20):
                angle = self.read_compass_angle()
                if angle is not None:
                    print(f"\r🔥 预热进度: {i+1}/20 - 当前角度: {angle:.1f}°", end="", flush=True)
                time.sleep(0.05)
            print("\n✅ 磁感器预热完成")
            
            # 7. 三参数同时选择
            selection_result = self.run_three_parameter_selection()
            
            print(f"\n🎉 参数选择完成!")
            print(f"📊 准备探索: 距离={self.format_distance(selection_result['distance'])}, "
                  f"方向={selection_result['direction']:.1f}°, "
                  f"预测年份={selection_result['target_year']}")
            
            # 这里可以继续添加探索和地图显示功能
            # （为了测试，先暂停在这里）
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断会话")
            return False
        except Exception as e:
            print(f"\n❌ 会话错误: {e}")
            return False

def signal_handler(sig, frame):
    print("\n\n🛑 收到中断信号，正在退出...")
    sys.exit(0)

def main():
    # Google Maps API密钥
    API_KEY = "AIzaSyClOdMUhS3lWQqycXGkU2cT9FNdnRuyjro"
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建增强版虚拟望远镜实例
    telescope = EnhancedTelescope(
        api_key=API_KEY,
        distance_bus=3,    # 距离编码器I2C总线
        compass_bus=4,     # 磁感器I2C总线
        time_bus=5,        # 时间编码器I2C总线
        encoder_addr=0x36  # 编码器地址
    )
    
    # 运行会话
    telescope.run_enhanced_telescope_session()
    
    print("🏁 增强版 Virtual Telescope 会话结束")

if __name__ == "__main__":
    main() 