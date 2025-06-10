#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 集成磁感器的虚拟望远镜系统
结合编码器距离控制、磁感器方向控制和Google Maps API的完整虚拟地理探索
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
from datetime import datetime

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

class CompassIntegratedTelescope:
    def __init__(self, api_key, encoder_bus=3, encoder_addr=0x36, compass_bus=4):
        # I2C配置
        self.encoder_bus_number = encoder_bus
        self.encoder_address = encoder_addr
        self.compass_bus_number = compass_bus
        self.encoder_bus = None
        self.compass_bus = None
        
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
            'acceleration_threshold': 3, # 加速阈值：连续旋转3次
            'acceleration_factor': 1.5,   # 加速倍数
        }
        
        # 磁感器配置
        self.compass_config = {
            'samples_for_calibration': 10,  # 校准时的采样次数
            'direction_deadband': 5,        # 方向死区（度）
            'smoothing_factor': 0.8,        # 角度平滑系数
        }
        
        # 当前状态
        self.current_distance = 1000  # 初始距离：1公里
        self.current_direction = 0    # 当前探索方向
        self.north_calibration = None # 北方校准基准
        self.last_rotation_time = 0
        self.consecutive_rotations = 0
        self.last_smooth_angle = 0
        
        # 地图API配置
        self.api_key = api_key
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 基础地理参数
        self.base_location = (51.5074, -0.1278)  # 伦敦市中心作为起始点
        self.fixed_time_period = "current"
        
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
        
        # 连接编码器
        try:
            self.encoder_bus = smbus.SMBus(self.encoder_bus_number)
            print(f"✅ 编码器连接成功 (I2C总线 {self.encoder_bus_number})")
        except Exception as e:
            print(f"❌ 编码器连接失败: {e}")
            success = False
        
        # 连接磁感器
        try:
            self.compass_bus = smbus.SMBus(self.compass_bus_number)
            print(f"✅ 磁感器连接成功 (I2C总线 {self.compass_bus_number})")
        except Exception as e:
            print(f"❌ 磁感器连接失败: {e}")
            success = False
        
        return success
    
    # ========== 编码器控制部分 ==========
    
    def write_encoder_register(self, reg_base, reg_addr, data):
        """写入seesaw寄存器"""
        try:
            if isinstance(data, int):
                self.encoder_bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr, data])
            else:
                self.encoder_bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            return False
    
    def read_encoder_register(self, reg_base, reg_addr, length=1):
        """读取seesaw寄存器"""
        try:
            self.encoder_bus.write_i2c_block_data(self.encoder_address, reg_base, [reg_addr])
            time.sleep(0.005)
            
            if length == 1:
                data = self.encoder_bus.read_byte(self.encoder_address)
                return data
            else:
                data = self.encoder_bus.read_i2c_block_data(self.encoder_address, 0, length)
                return data
        except Exception as e:
            return None
    
    def init_encoder(self):
        """初始化编码器"""
        print("⚙️ 初始化编码器...")
        
        # 软件复位
        success = self.write_encoder_register(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
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
        
        success1 = self.write_encoder_register(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
        success2 = self.write_encoder_register(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, pin_bytes)
        
        if success1 and success2:
            a_state, b_state, _, _ = self.read_encoder_state()
            if a_state is not None:
                self.last_a_state = a_state
                self.last_b_state = b_state
                print("✅ 编码器初始化完成")
                return True
        
        print("❌ 编码器初始化失败")
        return False
    
    def read_encoder_state(self):
        """读取编码器GPIO状态"""
        try:
            gpio_data = self.read_encoder_register(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
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
        
        if a_state != self.last_a_state:
            if a_state:  # A相上升沿
                if b_state:
                    self.encoder_position += 1
                    direction = 1  # 顺时针
                else:
                    self.encoder_position -= 1
                    direction = -1  # 逆时针
        elif b_state != self.last_b_state:
            if b_state:  # B相上升沿
                if not a_state:
                    self.encoder_position += 1
                    direction = 1  # 顺时针
                else:
                    self.encoder_position -= 1
                    direction = -1  # 逆时针
        
        return direction
    
    def calculate_distance_step(self, direction, current_time):
        """计算距离步长"""
        time_since_last = current_time - self.last_rotation_time
        
        if time_since_last < 0.4:
            self.consecutive_rotations += 1
        else:
            self.consecutive_rotations = 0
        
        step = self.distance_config['base_step']
        
        if self.consecutive_rotations >= self.distance_config['acceleration_threshold']:
            acceleration = min(self.consecutive_rotations / 3, 3)
            step *= (1 + acceleration * self.distance_config['acceleration_factor'])
        
        return int(step) * direction
    
    def update_distance(self, direction):
        """更新距离值"""
        current_time = time.time()
        distance_change = self.calculate_distance_step(direction, current_time)
        
        new_distance = self.current_distance + distance_change
        self.current_distance = max(
            self.distance_config['min_distance'],
            min(self.distance_config['max_distance'], new_distance)
        )
        
        self.last_rotation_time = current_time
        return distance_change
    
    # ========== 磁感器控制部分 ==========
    
    def init_compass(self):
        """初始化QMC5883L磁感器"""
        print("🧭 初始化磁感器...")
        
        try:
            # 软件复位
            self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG2, 0x80)
            time.sleep(0.1)
            
            # 配置寄存器：10Hz输出频率，2G量程，连续测量模式
            self.compass_bus.write_byte_data(QMC5883L_ADDR, QMC5883L_CONFIG, 0x01)
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
            # 检查数据准备状态
            status = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_STATUS)
            if not (status & 0x01):  # 数据未准备好
                return None, None, None
            
            # 读取XYZ数据（小端序）
            x_lsb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_X_LSB)
            x_msb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_X_MSB)
            y_lsb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_Y_LSB)  
            y_msb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_Y_MSB)
            z_lsb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_Z_LSB)
            z_msb = self.compass_bus.read_byte_data(QMC5883L_ADDR, QMC5883L_DATA_OUTPUT_Z_MSB)
            
            # 合成16位有符号整数
            x = self._combine_bytes(x_lsb, x_msb)
            y = self._combine_bytes(y_lsb, y_msb)
            z = self._combine_bytes(z_lsb, z_msb)
            
            return x, y, z
            
        except Exception as e:
            return None, None, None
    
    def _combine_bytes(self, lsb, msb):
        """组合LSB和MSB为有符号16位整数"""
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
    
    # ========== 地理计算部分 ==========
    
    def calculate_destination_coordinates(self, start_lat, start_lon, distance_meters, bearing_degrees):
        """根据起始坐标、距离和方向角计算目标坐标"""
        R = 6371000  # 地球半径（米）
        
        lat1 = math.radians(start_lat)
        lon1 = math.radians(start_lon)
        bearing = math.radians(bearing_degrees)
        
        angular_distance = distance_meters / R
        
        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance) +
            math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )
        
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2)
        )
        
        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)
        
        return lat2, lon2
    
    def get_exploration_target(self, distance, direction):
        """根据距离和方向获取探索目标坐标"""
        target_lat, target_lon = self.calculate_destination_coordinates(
            self.base_location[0],
            self.base_location[1],
            distance,
            direction
        )
        return target_lat, target_lon
    
    # ========== 地图API部分 ==========
    
    def get_location_info(self, lat, lon):
        """获取位置信息（逆地理编码）"""
        try:
            geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'latlng': f"{lat},{lon}",
                'key': self.api_key
            }
            
            response = requests.get(geocoding_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and data['results']:
                    return data['results'][0]['formatted_address']
        except Exception as e:
            print(f"⚠️ 获取位置信息失败: {e}")
        
        return f"位置: {lat:.4f}, {lon:.4f}"
    
    def get_static_map(self, center_lat, center_lon, distance):
        """获取静态地图图像"""
        if distance <= 500:
            zoom = 16
        elif distance <= 1000:
            zoom = 15
        elif distance <= 2000:
            zoom = 14
        elif distance <= 5000:
            zoom = 13
        else:
            zoom = 12
        
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        map_height = self.screen_height - 120
        
        params = {
            'center': f"{center_lat},{center_lon}",
            'zoom': str(zoom),
            'size': f"{self.screen_width}x{map_height}",
            'maptype': 'roadmap',
            'markers': f"color:red|{center_lat},{center_lon}",
            'key': self.api_key
        }
        
        try:
            url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
            print(f"🌐 获取地图: 缩放级别 {zoom}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    return Image.open(io.BytesIO(response.content))
            
            print(f"❌ 地图请求失败: {response.status_code}")
            return None
                
        except Exception as e:
            print(f"❌ 地图请求异常: {e}")
            return None
    
    # ========== 显示部分 ==========
    
    def format_distance(self, distance):
        """格式化距离显示"""
        if distance >= 1000:
            return f"{distance/1000:.1f}km"
        else:
            return f"{int(distance)}m"
    
    def display_distance_selection(self):
        """显示距离选择界面"""
        progress = (self.current_distance - self.distance_config['min_distance']) / \
                  (self.distance_config['max_distance'] - self.distance_config['min_distance'])
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\r🔭 探索距离: {self.format_distance(self.current_distance):<8} "
              f"[{bar}] {progress*100:5.1f}% ", end="", flush=True)
    
    def display_direction_selection(self):
        """显示方向选择界面"""
        current_dir = self.get_geographic_direction()
        if current_dir is not None:
            direction_name = self.get_direction_name(current_dir)
            
            # 创建方向指示器
            arrow_symbols = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
            arrow_index = int((current_dir + 22.5) // 45) % 8
            arrow = arrow_symbols[arrow_index]
            
            print(f"\r🧭 探索方向: {current_dir:6.1f}° {arrow} ({direction_name:<8}) ", end="", flush=True)
        else:
            print(f"\r🧭 探索方向: 读取中... ", end="", flush=True)
    
    def display_map_on_screen(self, map_image, target_location, distance, direction, location_info):
        """在屏幕上显示地图"""
        try:
            root = tk.Tk()
            root.title("Obscura No.7 - Virtual Telescope")
            root.configure(bg='black')
            root.attributes('-fullscreen', True)
            root.geometry(f"{self.screen_width}x{self.screen_height}")
            
            root.bind('<Escape>', lambda e: root.quit())
            
            # 地图显示
            photo = ImageTk.PhotoImage(map_image)
            map_label = tk.Label(root, image=photo, bg='black')
            map_label.pack()
            
            # 信息显示区域
            info_frame = tk.Frame(root, bg='black', height=120)
            info_frame.pack(side='bottom', fill='x')
            
            # 距离信息
            distance_text = f"🔭 探索距离: {self.format_distance(distance)}"
            distance_label = tk.Label(
                info_frame, text=distance_text,
                fg='cyan', bg='black', font=('Arial', 12, 'bold')
            )
            distance_label.pack(pady=1)
            
            # 方向信息
            direction_name = self.get_direction_name(direction)
            direction_text = f"🧭 探索方向: {direction:.1f}° ({direction_name})"
            direction_label = tk.Label(
                info_frame, text=direction_text,
                fg='orange', bg='black', font=('Arial', 11, 'bold')
            )
            direction_label.pack(pady=1)
            
            # 坐标信息
            coord_text = f"📍 坐标: {target_location[0]:.4f}, {target_location[1]:.4f}"
            coord_label = tk.Label(
                info_frame, text=coord_text,
                fg='white', bg='black', font=('Arial', 10)
            )
            coord_label.pack()
            
            # 位置信息
            location_label = tk.Label(
                info_frame, text=location_info,
                fg='yellow', bg='black', font=('Arial', 9)
            )
            location_label.pack()
            
            # 控制说明
            control_text = "按ESC键返回 | Obscura No.7 Virtual Telescope"
            control_label = tk.Label(
                info_frame, text=control_text,
                fg='gray', bg='black', font=('Arial', 8)
            )
            control_label.pack(pady=1)
            
            print("🖥️ 地图显示中，按ESC键返回...")
            root.mainloop()
            
            return True
            
        except Exception as e:
            print(f"❌ 地图显示失败: {e}")
            return False
    
    # ========== 主工作流程 ==========
    
    def run_distance_selection(self, timeout=60):
        """运行距离选择"""
        print("=" * 70)
        print("🔭 Obscura No.7 - 距离选择")
        print("=" * 70)
        print(f"📏 距离范围: {self.format_distance(self.distance_config['min_distance'])} - "
              f"{self.format_distance(self.distance_config['max_distance'])}")
        print("-" * 70)
        print("🎮 操作说明:")
        print("   🔄 旋转编码器: 调整探索距离")
        print("   🔘 按下按钮: 确认距离并继续")
        print("=" * 70)
        
        start_time = time.time()
        self.display_distance_selection()
        
        while time.time() - start_time < timeout:
            a_state, b_state, button_state, _ = self.read_encoder_state()
            
            if a_state is not None:
                direction = self.process_encoder_rotation(a_state, b_state)
                if direction:
                    self.update_distance(direction)
                    self.display_distance_selection()
                
                if button_state:
                    print(f"\n🔘 距离确认: {self.format_distance(self.current_distance)}")
                    return self.current_distance
                
                self.last_a_state = a_state
                self.last_b_state = b_state
            
            time.sleep(0.02)
        
        print(f"\n⏰ 选择超时，使用当前距离: {self.format_distance(self.current_distance)}")
        return self.current_distance
    
    def run_direction_selection(self, timeout=60):
        """运行方向选择"""
        print("\n" + "=" * 70)
        print("🧭 Obscura No.7 - 方向选择")
        print("=" * 70)
        print("🎮 操作说明:")
        print("   🔄 旋转设备: 选择探索方向")
        print("   🔘 按下按钮: 确认方向并开始探索")
        print("=" * 70)
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 更新方向显示
            self.display_direction_selection()
            
            # 检查按钮状态
            _, _, button_state, _ = self.read_encoder_state()
            if button_state:
                final_direction = self.get_geographic_direction()
                if final_direction is not None:
                    direction_name = self.get_direction_name(final_direction)
                    print(f"\n🔘 方向确认: {final_direction:.1f}° ({direction_name})")
                    return final_direction
                else:
                    print(f"\n❌ 无法读取方向，使用默认北方")
                    return 0
            
            time.sleep(0.1)
        
        print(f"\n⏰ 选择超时，使用当前方向")
        current_direction = self.get_geographic_direction()
        return current_direction if current_direction is not None else 0
    
    def explore_location(self, distance, direction):
        """探索指定距离和方向的位置"""
        print("\n" + "=" * 70)
        print("🌍 Virtual Telescope Exploration")
        print("=" * 70)
        
        # 1. 计算目标坐标
        print("📐 计算目标坐标...")
        target_lat, target_lon = self.get_exploration_target(distance, direction)
        print(f"📍 目标位置: {target_lat:.4f}, {target_lon:.4f}")
        print(f"🧭 探索方向: {direction:.1f}° ({self.get_direction_name(direction)})")
        
        # 2. 获取位置信息
        print("🔍 获取位置信息...")
        location_info = self.get_location_info(target_lat, target_lon)
        print(f"📝 位置描述: {location_info}")
        
        # 3. 获取地图
        print("🗺️ 生成地图...")
        map_image = self.get_static_map(target_lat, target_lon, distance)
        
        if map_image:
            print("✅ 地图生成成功!")
            
            # 4. 保存地图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            direction_name = self.get_direction_name(direction).replace("-", "_")
            filename = f"telescope_{distance}m_{direction:.0f}deg_{direction_name}_{timestamp}.png"
            save_path = os.path.join(self.script_dir, filename)
            map_image.save(save_path)
            print(f"💾 地图已保存: {filename}")
            
            # 5. 显示地图
            return self.display_map_on_screen(
                map_image, 
                (target_lat, target_lon), 
                distance,
                direction,
                location_info
            )
        else:
            print("❌ 地图生成失败")
            return False
    
    def run_telescope_session(self):
        """运行完整的望远镜会话"""
        print("🚀 启动Obscura No.7 Virtual Telescope...")
        
        try:
            # 1. 连接设备
            if not self.connect_devices():
                return False
            
            # 2. 初始化编码器
            if not self.init_encoder():
                return False
            
            # 3. 初始化磁感器
            if not self.init_compass():
                return False
            
            # 4. 校准北方基准
            if not self.calibrate_north_direction():
                return False
            
            # 5. 距离选择
            selected_distance = self.run_distance_selection()
            
            # 6. 方向选择
            selected_direction = self.run_direction_selection()
            
            # 7. 位置探索
            success = self.explore_location(selected_distance, selected_direction)
            
            if success:
                print("\n🎉 探索会话完成!")
            else:
                print("\n⚠️ 探索会话遇到问题")
            
            return success
            
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
    
    # 创建集成磁感器的虚拟望远镜实例
    telescope = CompassIntegratedTelescope(
        api_key=API_KEY,
        encoder_bus=3,      # 编码器I2C总线
        encoder_addr=0x36,  # 编码器地址
        compass_bus=4       # 磁感器I2C总线
    )
    
    # 运行会话
    telescope.run_telescope_session()
    
    print("🏁 Virtual Telescope 会话结束")

if __name__ == "__main__":
    main()