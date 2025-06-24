#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Hardware Interface
树莓派真实硬件接口 - 替代模拟器
"""

import time
import logging
import time
from typing import Dict, Optional, Tuple

# 尝试导入树莓派专用库
try:
    import RPi.GPIO as GPIO
    from gpiozero import RotaryEncoder, Button
    import spidev
    import smbus
    PI_HARDWARE_AVAILABLE = True
except ImportError:
    PI_HARDWARE_AVAILABLE = False
    print("⚠️ Raspberry Pi hardware libraries not available - using simulation mode")

class RaspberryPiHardware:
    """树莓派硬件接口类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.hardware_available = PI_HARDWARE_AVAILABLE
        
        # 硬件I2C配置 - 完全使用I2C通信，避免GPIO冲突
        # 使用与simple_workflow.py相同的配置
        self.encoder_i2c_bus = config.get('hardware_settings.distance_bus', 3)    # I2C总线3用于编码器 (GPIO23/24)
        self.compass_i2c_bus = config.get('hardware_settings.compass_bus', 4)     # I2C总线4用于磁感器 (GPIO20/21)
        self.time_encoder_i2c_bus = config.get('hardware_settings.time_bus', 5)  # I2C总线5用于时间编码器 (GPIO5/6)
        self.encoder_address = int(config.get('hardware_settings.encoder_addr', '0x36'), 16)
        self.compass_address = config.get('hardware.compass.i2c_address', 0x0D)
        
        # 不再使用GPIO直连，避免与HyperPixel冲突
        
        # 初始化硬件
        if self.hardware_available:
            self._init_hardware()
        else:
            self._init_simulation()
    
    def _init_hardware(self):
        """初始化真实硬件 - 使用I2C通信"""
        try:
            # 初始化I2C总线
            self.compass_i2c = smbus.SMBus(self.compass_i2c_bus)
            self.encoder_i2c = smbus.SMBus(self.encoder_i2c_bus)
            self.time_encoder_i2c = smbus.SMBus(self.time_encoder_i2c_bus)
            
            # 编码器状态变量（通过I2C Seesaw芯片控制）
            self.encoder_position = 0
            self.button_pressed = False
            
            # 初始化Seesaw编码器
            encoder_init = self._init_seesaw_encoder()
            time_encoder_init = self._init_time_encoder()
            
            if encoder_init and time_encoder_init:
                self.logger.info("🔧 Raspberry Pi I2C hardware initialized successfully")
            elif encoder_init or time_encoder_init:
                self.logger.warning("⚠️ 部分Seesaw编码器初始化失败，但其他硬件正常")
            else:
                self.logger.warning("⚠️ Seesaw编码器初始化失败，但其他硬件正常")
            
        except Exception as e:
            self.logger.error(f"❌ Hardware initialization failed: {e}")
            self.hardware_available = False
            self._init_simulation()
    
    def _init_simulation(self):
        """初始化模拟模式"""
        self.encoder_position = 0
        self.button_pressed = False
        self.logger.warning("⚠️ Running in simulation mode - no real hardware")
    
    # ========== Seesaw编码器协议实现 ==========
    
    # Seesaw寄存器定义
    SEESAW_STATUS_BASE = 0x00
    SEESAW_STATUS_HW_ID = 0x01
    SEESAW_STATUS_SWRST = 0x7F
    SEESAW_GPIO_BASE = 0x01
    SEESAW_GPIO_DIRCLR_BULK = 0x03
    SEESAW_GPIO_BULK = 0x04
    SEESAW_GPIO_PULLENSET = 0x0B
    
    def _write_seesaw_register(self, reg_base, reg_addr, data=None):
        """写入Seesaw寄存器"""
        try:
            if data is None:
                self.encoder_i2c.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr])
            elif isinstance(data, int):
                self.encoder_i2c.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr, data])
            else:
                self.encoder_i2c.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            self.logger.debug(f"Seesaw写寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return False
    
    def _read_seesaw_register(self, reg_base, reg_addr, length=1):
        """读取Seesaw寄存器"""
        try:
            self.encoder_i2c.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr])
            time.sleep(0.005)
            
            if length == 1:
                data = self.encoder_i2c.read_byte(self.encoder_address)
                return data
            else:
                data = self.encoder_i2c.read_i2c_block_data(self.encoder_address, 0, length)
                return data
        except Exception as e:
            self.logger.debug(f"Seesaw读寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return None
    
    def _test_seesaw_encoder(self):
        """测试Seesaw编码器是否可用"""
        try:
            # 尝试读取硬件ID
            hw_id = self._read_seesaw_register(self.SEESAW_STATUS_BASE, self.SEESAW_STATUS_HW_ID)
            if hw_id is not None:
                self.logger.info(f"🎯 检测到Seesaw编码器，硬件ID: 0x{hw_id:02x}")
                return True
            else:
                self.logger.debug("❌ 无法读取Seesaw硬件ID")
                return False
        except Exception as e:
            self.logger.debug(f"❌ Seesaw编码器检测失败: {e}")
            return False
    
    def _init_seesaw_encoder(self):
        """初始化Seesaw编码器"""
        try:
            # 软件复位
            success = self._write_seesaw_register(self.SEESAW_STATUS_BASE, self.SEESAW_STATUS_SWRST, 0xFF)
            if success:
                time.sleep(0.5)
            
            # 配置GPIO引脚
            encoder_a_pin = 8
            encoder_b_pin = 14  
            button_pin = 24
            
            pin_mask = (1 << encoder_a_pin) | (1 << encoder_b_pin) | (1 << button_pin)
            pin_bytes = [
                (pin_mask >> 24) & 0xFF,
                (pin_mask >> 16) & 0xFF, 
                (pin_mask >> 8) & 0xFF,
                pin_mask & 0xFF
            ]
            
            success1 = self._write_seesaw_register(self.SEESAW_GPIO_BASE, self.SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
            success2 = self._write_seesaw_register(self.SEESAW_GPIO_BASE, self.SEESAW_GPIO_PULLENSET, pin_bytes)
            
            if success1 and success2:
                self.logger.info("✅ Seesaw编码器初始化成功")
                return True
            else:
                self.logger.error("❌ Seesaw编码器GPIO配置失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Seesaw编码器初始化失败: {e}")
            return False
    
    def _read_seesaw_gpio_state(self):
        """读取Seesaw GPIO状态"""
        try:
            gpio_data = self._read_seesaw_register(self.SEESAW_GPIO_BASE, self.SEESAW_GPIO_BULK, 4)
            if gpio_data and len(gpio_data) >= 4:
                gpio_state = (gpio_data[0] << 24) | (gpio_data[1] << 16) | (gpio_data[2] << 8) | gpio_data[3]
                
                encoder_a_pin = 8
                encoder_b_pin = 14  
                button_pin = 24
                
                a_state = bool((gpio_state >> encoder_a_pin) & 1)
                b_state = bool((gpio_state >> encoder_b_pin) & 1)
                button_state = not bool((gpio_state >> button_pin) & 1)
                
                return a_state, b_state, button_state
            else:
                return None, None, None
        except Exception as e:
            self.logger.debug(f"读取Seesaw GPIO状态失败: {e}")
            return None, None, None
    
    def _init_time_encoder(self):
        """初始化Time Encoder的Seesaw协议"""
        try:
            # 软复位Time Encoder
            self.time_encoder_i2c.write_i2c_block_data(
                self.encoder_address, self.SEESAW_STATUS_BASE, [self.SEESAW_STATUS_SWRST, 0xFF]
            )
            time.sleep(0.1)
            
            # 设置编码器引脚为输入模式
            pin_mask = [0x00, 0x00, 0x41, 0x00]  # 引脚8, 14 (编码器A, B)
            self.time_encoder_i2c.write_i2c_block_data(
                self.encoder_address, self.SEESAW_GPIO_BASE, [self.SEESAW_GPIO_DIRCLR_BULK] + pin_mask
            )
            
            # 启用上拉电阻
            self.time_encoder_i2c.write_i2c_block_data(
                self.encoder_address, self.SEESAW_GPIO_BASE, [self.SEESAW_GPIO_PULLENSET] + pin_mask
            )
            time.sleep(0.05)
            
            self.logger.info("⏰ Time Encoder Seesaw协议初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Time Encoder Seesaw初始化失败: {e}")
            return False
    
    def _test_time_encoder_button(self):
        """测试Time Encoder上的按钮 (I2C总线5)"""
        try:
            # 尝试读取Time Encoder的硬件ID
            hw_id = self._read_time_encoder_register(self.SEESAW_STATUS_BASE, self.SEESAW_STATUS_HW_ID)
            if hw_id is not None:
                self.logger.info(f"🎯 检测到Time Encoder，硬件ID: 0x{hw_id:02x}")
                
                # 尝试读取按钮状态
                button_state = self._read_time_encoder_button_state()
                if button_state is not None:
                    self.logger.info("🔘 Time Encoder按钮检测成功")
                    return True
                else:
                    self.logger.debug("❌ Time Encoder按钮状态读取失败")
                    return False
            else:
                self.logger.debug("❌ 无法读取Time Encoder硬件ID")
                return False
        except Exception as e:
            self.logger.debug(f"❌ Time Encoder按钮检测失败: {e}")
            return False
    
    def _read_time_encoder_register(self, reg_base, reg_addr, length=1):
        """读取Time Encoder的Seesaw寄存器"""
        try:
            self.time_encoder_i2c.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr])
            time.sleep(0.005)
            
            if length == 1:
                data = self.time_encoder_i2c.read_byte(self.encoder_address)
                return data
            else:
                data = self.time_encoder_i2c.read_i2c_block_data(self.encoder_address, 0, length)
                return data
        except Exception as e:
            self.logger.debug(f"Time Encoder读寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return None
    
    def _read_time_encoder_gpio_state(self):
        """读取Time Encoder的GPIO状态（包括编码器A/B相和按钮）"""
        try:
            gpio_data = self._read_time_encoder_register(self.SEESAW_GPIO_BASE, self.SEESAW_GPIO_BULK, 4)
            if gpio_data and len(gpio_data) >= 4:
                gpio_state = (gpio_data[0] << 24) | (gpio_data[1] << 16) | (gpio_data[2] << 8) | gpio_data[3]
                
                encoder_a_pin = 8
                encoder_b_pin = 14  
                button_pin = 24
                
                a_state = bool((gpio_state >> encoder_a_pin) & 1)
                b_state = bool((gpio_state >> encoder_b_pin) & 1)
                button_state = not bool((gpio_state >> button_pin) & 1)
                
                return a_state, b_state, button_state
            else:
                return None, None, None
        except Exception as e:
            self.logger.debug(f"读取Time Encoder GPIO状态失败: {e}")
            return None, None, None

    def _read_time_encoder_button_state(self):
        """读取Time Encoder的按钮状态"""
        try:
            _, _, button_state = self._read_time_encoder_gpio_state()
            return button_state
        except Exception as e:
            self.logger.debug(f"读取Time Encoder按钮状态失败: {e}")
            return None
    
    def read_three_parameter_input(self, timeout: float = 60.0) -> tuple:
        """
        读取三参数输入：距离、方向、时间偏移
        通过Distance Encoder调整距离，磁感器检测方向，Time Encoder按钮确认
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            tuple: (distance_km, direction_deg, time_offset_years)
        """
        if not self.hardware_available:
            # 模拟模式 - 使用键盘输入
            try:
                distance_str = input("🎯 输入目标距离 (km): ").strip()
                direction_str = input("🧭 输入方向角度 (0-360°): ").strip()
                time_str = input("⏰ 输入时间偏移 (年): ").strip()
                return float(distance_str), float(direction_str), float(time_str)
            except ValueError:
                return 5.0, 0.0, 5.0  # 默认值
        
        # 参数配置
        distance_config = {
            'min_distance': 1000,    # 1km
            'max_distance': 50000,   # 50km
            'base_step': 1000,       # 1km步长
        }
        
        time_config = {
            'min_offset': 0,         # 当前年份
            'max_offset': 50,        # +50年
            'base_step': 1,          # 1年步长
        }
        
        # 初始状态
        current_distance = 5000  # 5km
        current_time_offset = 5  # +5年
        
        # Distance Encoder状态追踪 - 获取初始状态
        initial_a, initial_b, _ = self._read_seesaw_gpio_state()
        if initial_a is not None:
            last_distance_a_state = initial_a
            last_distance_b_state = initial_b
            distance_encoder_position = 0
            print(f"🎛️ Distance Encoder初始状态: A={initial_a}, B={initial_b}")
        else:
            print("❌ 无法读取Distance Encoder初始状态")
            last_distance_a_state = False
            last_distance_b_state = False
            distance_encoder_position = 0
        
        # Time Encoder状态追踪 - 获取初始状态
        initial_time_a, initial_time_b, _ = self._read_time_encoder_gpio_state()
        if initial_time_a is not None:
            last_time_a_state = initial_time_a
            last_time_b_state = initial_time_b
            time_encoder_position = 0
            print(f"⏰ Time Encoder初始状态: A={initial_time_a}, B={initial_time_b}")
        else:
            print("❌ 无法读取Time Encoder初始状态")
            last_time_a_state = False
            last_time_b_state = False
            time_encoder_position = 0
        
        # 初始化磁感器
        self._init_compass()
        
        print("=" * 70)
        print("🎯 Obscura No.7 - 三参数设置")
        print("=" * 70)
        print("🎮 操作说明:")
        print("   🔄 旋转Distance Encoder: 调整探索距离")
        print("   ⏰ 旋转Time Encoder: 调整时间偏移")
        print("   🧭 旋转设备: 改变探索方向")
        print("   🔘 按Time Encoder按钮: 确认所有参数")
        print("=" * 70)
        
        # 验证硬件连接
        print("🔍 验证硬件连接...")
        encoder_test = self._test_seesaw_encoder()
        compass_test = self._read_compass_direction() is not None
        time_encoder_test = self._read_time_encoder_gpio_state()[0] is not None
        button_test = self._read_time_encoder_button_state() is not None
        
        print(f"   Distance Encoder (I2C{self.encoder_i2c_bus}): {'✅' if encoder_test else '❌'}")
        print(f"   Compass (I2C{self.compass_i2c_bus}): {'✅' if compass_test else '❌'}")  
        print(f"   Time Encoder旋钮 (I2C{self.time_encoder_i2c_bus}): {'✅' if time_encoder_test else '❌'}")
        print(f"   Time Encoder按钮 (I2C{self.time_encoder_i2c_bus}): {'✅' if button_test else '❌'}")
        print()
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 1. 读取Distance Encoder状态 (I2C总线3)
            distance_a_state, distance_b_state, distance_button = self._read_seesaw_gpio_state()
            
            if distance_a_state is not None:
                # 处理距离编码器旋转
                direction = self._process_encoder_rotation(
                    distance_a_state, distance_b_state, 
                    last_distance_a_state, last_distance_b_state,
                    distance_encoder_position
                )
                
                if direction:
                    distance_change = distance_config['base_step'] * direction
                    new_distance = max(
                        distance_config['min_distance'],
                        min(distance_config['max_distance'], current_distance + distance_change)
                    )
                    if new_distance != current_distance:
                        current_distance = new_distance
                        distance_encoder_position += direction
                        print(f"\n🔄 距离调整: {direction:+d} → {current_distance/1000:.1f}km")
                
                last_distance_a_state = distance_a_state
                last_distance_b_state = distance_b_state
            else:
                # 每10次循环输出一次调试信息
                if int((time.time() - start_time) * 20) % 200 == 0:
                    print(f"\n⚠️ 编码器无响应 - 检查I2C总线{self.encoder_i2c_bus}连接")
            
            # 2. 读取Time Encoder状态 (I2C总线5)
            time_a_state, time_b_state, time_button = self._read_time_encoder_gpio_state()
            
            if time_a_state is not None:
                # 处理时间编码器旋转
                time_direction = self._process_encoder_rotation(
                    time_a_state, time_b_state, 
                    last_time_a_state, last_time_b_state,
                    time_encoder_position
                )
                
                if time_direction:
                    time_change = time_config['base_step'] * time_direction
                    new_time_offset = max(
                        time_config['min_offset'],
                        min(time_config['max_offset'], current_time_offset + time_change)
                    )
                    if new_time_offset != current_time_offset:
                        current_time_offset = new_time_offset
                        time_encoder_position += time_direction
                        print(f"\n⏰ 时间调整: {time_direction:+d} → +{current_time_offset} 年")
                
                last_time_a_state = time_a_state
                last_time_b_state = time_b_state
            else:
                # 每15次循环输出一次调试信息
                if int((time.time() - start_time) * 20) % 300 == 0:
                    print(f"\n⚠️ Time Encoder旋钮无响应 - 检查I2C总线{self.time_encoder_i2c_bus}连接")
            
            # 3. 读取磁感器方向
            current_direction = self._read_compass_direction()
            if current_direction is None:
                current_direction = 0.0  # 默认北方
            
            # 4. 检查Time Encoder按钮 (I2C总线5)
            time_button_pressed = self._read_time_encoder_button_state()
            
            if time_button_pressed:
                direction_name = self._get_direction_name(current_direction)
                print(f"\n🔘 参数确认:")
                print(f"   📏 距离: {current_distance/1000:.1f} km")
                print(f"   🧭 方向: {current_direction:.1f}° ({direction_name})")
                print(f"   ⏰ 时间偏移: +{current_time_offset} 年")
                return current_distance/1000, current_direction, current_time_offset
            elif time_button_pressed is None:
                # 每20次循环输出一次调试信息
                if int((time.time() - start_time) * 20) % 400 == 0:
                    print(f"\n⚠️ Time Encoder无响应 - 检查I2C总线{self.time_encoder_i2c_bus}连接")
            
            # 5. 显示当前状态
            self._display_three_parameter_status(current_distance, current_direction, current_time_offset)
            
            time.sleep(0.05)  # 50ms刷新率
        
        print(f"\n⏰ 选择超时，使用当前参数")
        return current_distance/1000, current_direction, current_time_offset
    
    def _process_encoder_rotation(self, a_state, b_state, last_a_state, last_b_state, position):
        """处理编码器旋转 - 根据simple_workflow.py的逻辑"""
        direction = None
        
        if a_state != last_a_state:
            if a_state:  # A相上升沿
                if b_state:
                    direction = 1  # 顺时针
                else:
                    direction = -1  # 逆时针
        elif b_state != last_b_state:
            if b_state:  # B相上升沿
                if not a_state:
                    direction = 1  # 顺时针
                else:
                    direction = -1  # 逆时针
        
        return direction
    
    def _init_compass(self):
        """初始化磁感器"""
        try:
            # QMC5883L初始化序列
            self.compass_i2c.write_byte_data(0x0D, 0x0A, 0x80)  # 软件复位
            time.sleep(0.1)
            self.compass_i2c.write_byte_data(0x0D, 0x09, 0x01)  # 连续测量模式
            time.sleep(0.1)
            self.logger.info("🧭 磁感器初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ 磁感器初始化失败: {e}")
            return False
    
    def _read_compass_direction(self):
        """读取磁感器方向"""
        try:
            # 读取QMC5883L数据
            data = self.compass_i2c.read_i2c_block_data(0x0D, 0x00, 6)
            
            # 组合XY数据
            x = self._combine_bytes(data[0], data[1])
            y = self._combine_bytes(data[2], data[3])
            
            # 计算角度
            import math
            angle = math.atan2(y, x) * 180 / math.pi
            if angle < 0:
                angle += 360
            
            return angle
        except Exception as e:
            self.logger.debug(f"磁感器读取失败: {e}")
            return None
    
    def _combine_bytes(self, lsb, msb):
        """组合LSB和MSB为有符号16位整数"""
        value = (msb << 8) | lsb
        if value > 32767:
            value -= 65536
        return value
    
    def _get_direction_name(self, angle):
        """将角度转换为方向名称"""
        directions = [
            (0, "正北"), (22.5, "北-东北"), (45, "东北"), (67.5, "东-东北"),
            (90, "正东"), (112.5, "东-东南"), (135, "东南"), (157.5, "南-东南"),
            (180, "正南"), (202.5, "南-西南"), (225, "西南"), (247.5, "西-西南"),
            (270, "正西"), (292.5, "西-西北"), (315, "西北"), (337.5, "北-西北")
        ]
        
        min_diff = 360
        closest_direction = "正北"
        
        for dir_angle, dir_name in directions:
            diff = min(abs(angle - dir_angle), 360 - abs(angle - dir_angle))
            if diff < min_diff:
                min_diff = diff
                closest_direction = dir_name
        
        return closest_direction
    
    def _display_three_parameter_status(self, distance, direction, time_offset):
        """显示三参数当前状态"""
        direction_name = self._get_direction_name(direction)
        
        # 创建距离进度条
        distance_progress = (distance - 1000) / (50000 - 1000)
        distance_bar_length = 20
        distance_filled = int(distance_bar_length * distance_progress)
        distance_bar = "█" * distance_filled + "░" * (distance_bar_length - distance_filled)
        
        # 创建方向指示器
        arrow_symbols = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        arrow_index = int((direction + 22.5) // 45) % 8
        arrow = arrow_symbols[arrow_index]
        
        print(f"\r📏 距离: {distance/1000:5.1f}km [{distance_bar}] "
              f"🧭 方向: {direction:6.1f}° {arrow} ({direction_name:<8}) "
              f"⏰ 时间: +{time_offset}年", end="", flush=True)
    
    def read_distance_input(self, timeout: float = 30.0) -> float:
        """兼容性方法 - 调用三参数输入并返回距离"""
        distance, _, _ = self.read_three_parameter_input(timeout)
        return distance
    
    def read_compass_direction(self) -> float:
        """
        读取磁感器方向数据
        
        Returns:
            direction: 方向角度（0-360度）
        """
        if not self.hardware_available:
            # 模拟模式
            import random
            direction = random.uniform(0, 360)
            print(f"🧭 模拟磁感器读数: {direction:.1f}°")
            return direction
        
        try:
            # 读取HMC5883L磁感器数据
            # 这里需要根据具体的磁感器型号调整寄存器地址
            
            # 配置寄存器
            self.compass_i2c.write_byte_data(self.compass_address, 0x00, 0x70)  # 配置寄存器A
            self.compass_i2c.write_byte_data(self.compass_address, 0x01, 0xA0)  # 配置寄存器B
            self.compass_i2c.write_byte_data(self.compass_address, 0x02, 0x00)  # 模式寄存器
            
            time.sleep(0.1)
            
            # 读取X、Y、Z轴数据
            data = self.compass_i2c.read_i2c_block_data(self.compass_address, 0x03, 6)
            
            # 转换为有符号整数
            x = self._bytes_to_int(data[0], data[1])
            y = self._bytes_to_int(data[4], data[5])
            z = self._bytes_to_int(data[2], data[3])
            
            # 计算方向角
            import math
            direction = math.atan2(y, x) * 180 / math.pi
            if direction < 0:
                direction += 360
            
            self.logger.info(f"🧭 磁感器读数: {direction:.1f}° (X:{x}, Y:{y}, Z:{z})")
            return direction
            
        except Exception as e:
            self.logger.error(f"❌ 磁感器读取失败: {e}")
            # 返回模拟值
            import random
            return random.uniform(0, 360)
    
    def _bytes_to_int(self, high_byte: int, low_byte: int) -> int:
        """将两个字节转换为有符号整数"""
        value = (high_byte << 8) + low_byte
        if value >= 32768:
            value = value - 65536
        return value
    
    def read_time_offset_input(self, timeout: float = 30.0) -> float:
        """
        读取时间偏移输入
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            time_offset: 时间偏移（年）
        """
        if not self.hardware_available:
            # 模拟模式 - 使用键盘输入
            try:
                time_str = input("⏰ 输入时间偏移 (年): ").strip()
                return float(time_str)
            except ValueError:
                return 5.0  # 默认值
        
        # 真实硬件模式 - 可以用编码器或其他方式
        print("⏰ 请设置时间偏移...")
        try:
            time_offset = float(input("输入年数: "))
            return time_offset
        except:
            return 5.0
    
    def get_hardware_status(self) -> Dict:
        """获取硬件状态"""
        status = {
            'hardware_available': self.hardware_available,
            'encoder_available': False,
            'compass_available': False,
            'button_available': False
        }
        
        if self.hardware_available:
            try:
                # 测试编码器 - 使用Seesaw协议检测
                status['encoder_available'] = self._test_seesaw_encoder()
                
                # 测试磁感器
                self.compass_i2c.read_byte(self.compass_address)
                status['compass_available'] = True
                
                # 测试按钮 - 检测Time Encoder上的按钮 (I2C总线5)
                status['button_available'] = self._test_time_encoder_button()
                
            except Exception as e:
                self.logger.warning(f"⚠️ Hardware status check failed: {e}")
        
        return status
    
    def cleanup(self):
        """清理硬件资源"""
        if self.hardware_available:
            try:
                # 关闭I2C连接
                if hasattr(self, 'compass_i2c'):
                    self.compass_i2c.close()
                if hasattr(self, 'encoder_i2c'):
                    self.encoder_i2c.close()
                if hasattr(self, 'time_encoder_i2c'):
                    self.time_encoder_i2c.close()
                
                # 不调用GPIO.cleanup()，因为我们使用I2C通信
                self.logger.info("🔧 Hardware cleanup completed (I2C only)")
            except Exception as e:
                self.logger.error(f"❌ Hardware cleanup failed: {e}")

if __name__ == "__main__":
    # 测试硬件接口
    print("🔧 Testing Raspberry Pi Hardware Interface...")
    
    config = {
        'hardware': {
            'encoder': {'pin_a': 2, 'pin_b': 3},
            'button': {'pin': 4},
            'i2c': {'bus': 1},
            'compass': {'i2c_address': 0x0D}
        }
    }
    
    hardware = RaspberryPiHardware(config)
    
    # 显示硬件状态
    status = hardware.get_hardware_status()
    print("📊 Hardware Status:")
    for key, value in status.items():
        print(f"   {key}: {'✅' if value else '❌'}")
    
    # 测试读取功能
    try:
        distance = hardware.read_distance_input(timeout=10)
        print(f"📏 Distance: {distance:.1f} km")
        
        direction = hardware.read_compass_direction()
        print(f"🧭 Direction: {direction:.1f}°")
        
        time_offset = hardware.read_time_offset_input(timeout=10)
        print(f"⏰ Time offset: {time_offset:.1f} years")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    finally:
        hardware.cleanup()
        print("�� Test completed") 