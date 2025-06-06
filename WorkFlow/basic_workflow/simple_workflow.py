#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 距离控制地图探索系统
结合编码器距离控制和Google Maps API的虚拟地理探索
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

class TelescopeMapExplorer:
    def __init__(self, api_key, bus_number=3, address=0x36):
        # I2C和编码器配置
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
            'acceleration_threshold': 3, # 加速阈值：连续旋转3次
            'acceleration_factor': 1.5,   # 加速倍数
        }
        
        # 当前状态
        self.current_distance = 1000  # 初始距离：1公里
        self.last_rotation_time = 0
        self.consecutive_rotations = 0
        
        # 地图API配置
        self.api_key = api_key
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 基础地理参数（固定值，模拟方向和时间的定量）
        self.base_location = (51.5074, -0.1278)  # 伦敦市中心作为起始点
        self.fixed_direction = 45  # 固定方向：东北方向（45度）
        self.fixed_time_period = "current"  # 固定时间：当前
        
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
            # HyperPixel 4" 默认分辨率
            self.screen_width = 480
            self.screen_height = 800
            print(f"🖥️ 使用默认分辨率: {self.screen_width}x{self.screen_height}")
    
    # ========== 编码器控制部分 ==========
    
    def connect_encoder(self):
        """连接到I2C总线"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            print(f"✅ 编码器连接成功 (I2C总线 {self.bus_number})")
            return True
        except Exception as e:
            print(f"❌ 编码器连接失败: {e}")
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
    
    def init_encoder(self):
        """初始化编码器"""
        print("⚙️ 初始化编码器...")
        
        # 软件复位
        success = self.write_register(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
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
        
        success1 = self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
        success2 = self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, pin_bytes)
        
        if success1 and success2:
            # 获取初始状态
            a_state, b_state, _, _ = self.read_gpio_state()
            if a_state is not None:
                self.last_a_state = a_state
                self.last_b_state = b_state
                print("✅ 编码器初始化完成")
                return True
        
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
        
        # 检查连续旋转
        if time_since_last < 0.4:  # 400ms内连续旋转
            self.consecutive_rotations += 1
        else:
            self.consecutive_rotations = 0
        
        # 基础步长
        step = self.distance_config['base_step']
        
        # 自适应加速
        if self.consecutive_rotations >= self.distance_config['acceleration_threshold']:
            acceleration = min(self.consecutive_rotations / 3, 3)  # 最大3倍加速
            step *= (1 + acceleration * self.distance_config['acceleration_factor'])
        
        return int(step) * direction
    
    def update_distance(self, direction):
        """更新距离值"""
        current_time = time.time()
        distance_change = self.calculate_distance_step(direction, current_time)
        
        # 更新距离
        new_distance = self.current_distance + distance_change
        self.current_distance = max(
            self.distance_config['min_distance'],
            min(self.distance_config['max_distance'], new_distance)
        )
        
        self.last_rotation_time = current_time
        return distance_change
    
    # ========== 地理计算部分 ==========
    
    def calculate_destination_coordinates(self, start_lat, start_lon, distance_meters, bearing_degrees):
        """
        根据起始坐标、距离和方向角计算目标坐标
        使用Haversine公式的逆运算
        """
        # 地球半径（米）
        R = 6371000
        
        # 转换为弧度
        lat1 = math.radians(start_lat)
        lon1 = math.radians(start_lon)
        bearing = math.radians(bearing_degrees)
        
        # 角距离
        angular_distance = distance_meters / R
        
        # 计算目标纬度
        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance) +
            math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )
        
        # 计算目标经度
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2)
        )
        
        # 转换回度数
        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)
        
        return lat2, lon2
    
    def get_exploration_target(self, distance):
        """根据距离获取探索目标坐标"""
        target_lat, target_lon = self.calculate_destination_coordinates(
            self.base_location[0],  # 起始纬度
            self.base_location[1],  # 起始经度
            distance,               # 距离（米）
            self.fixed_direction    # 方向角（度）
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
        # 根据距离计算合适的缩放级别
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
        map_height = self.screen_height - 100  # 为信息栏预留空间
        
        params = {
            'center': f"{center_lat},{center_lon}",
            'zoom': str(zoom),
            'size': f"{self.screen_width}x{map_height}",
            'maptype': 'roadmap',
            'markers': f"color:red|{center_lat},{center_lon}",  # 添加红色标记
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
    
    def display_map_on_screen(self, map_image, target_location, distance, location_info):
        """在屏幕上显示地图"""
        try:
            root = tk.Tk()
            root.title("Obscura No.7 - Virtual Telescope")
            root.configure(bg='black')
            root.attributes('-fullscreen', True)
            root.geometry(f"{self.screen_width}x{self.screen_height}")
            
            # ESC键退出
            root.bind('<Escape>', lambda e: root.quit())
            
            # 地图显示
            photo = ImageTk.PhotoImage(map_image)
            map_label = tk.Label(root, image=photo, bg='black')
            map_label.pack()
            
            # 信息显示区域
            info_frame = tk.Frame(root, bg='black', height=100)
            info_frame.pack(side='bottom', fill='x')
            
            # 距离信息
            distance_text = f"🔭 探索距离: {self.format_distance(distance)}"
            distance_label = tk.Label(
                info_frame, text=distance_text,
                fg='cyan', bg='black', font=('Arial', 12, 'bold')
            )
            distance_label.pack(pady=2)
            
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
            control_label.pack(pady=2)
            
            print("🖥️ 地图显示中，按ESC键返回...")
            root.mainloop()
            
            return True
            
        except Exception as e:
            print(f"❌ 地图显示失败: {e}")
            return False
    
    # ========== 主工作流程 ==========
    
    def run_distance_selection(self, timeout=120):
        """运行距离选择"""
        print("=" * 70)
        print("🔭 Obscura No.7 - Virtual Telescope Distance Selection")
        print("=" * 70)
        print(f"📏 距离范围: {self.format_distance(self.distance_config['min_distance'])} - "
              f"{self.format_distance(self.distance_config['max_distance'])}")
        print(f"🧭 探索方向: {self.fixed_direction}° (东北方)")
        print(f"📍 起始位置: 伦敦市中心")
        print("-" * 70)
        print("🎮 操作说明:")
        print("   🔄 旋转编码器: 调整探索距离")
        print("   🔘 按下按钮: 确认距离并开始探索")
        print("=" * 70)
        
        start_time = time.time()
        self.display_distance_selection()
        
        while time.time() - start_time < timeout:
            a_state, b_state, button_state, raw_gpio = self.read_gpio_state()
            
            if a_state is not None:
                # 处理旋转
                direction = self.process_encoder_rotation(a_state, b_state)
                if direction:
                    distance_change = self.update_distance(direction)
                    self.display_distance_selection()
                
                # 处理按钮按压
                if button_state:
                    print(f"\n🔘 距离确认: {self.format_distance(self.current_distance)}")
                    return self.current_distance
                
                # 更新状态
                self.last_a_state = a_state
                self.last_b_state = b_state
            
            time.sleep(0.02)  # 50Hz采样
        
        print(f"\n⏰ 选择超时，使用当前距离: {self.format_distance(self.current_distance)}")
        return self.current_distance
    
    def explore_location(self, distance):
        """探索指定距离的位置"""
        print("\n" + "=" * 70)
        print("🌍 Virtual Telescope Exploration")
        print("=" * 70)
        
        # 1. 计算目标坐标
        print("📐 计算目标坐标...")
        target_lat, target_lon = self.get_exploration_target(distance)
        print(f"📍 目标位置: {target_lat:.4f}, {target_lon:.4f}")
        
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
            filename = f"telescope_exploration_{distance}m_{timestamp}.png"
            save_path = os.path.join(self.script_dir, filename)
            map_image.save(save_path)
            print(f"💾 地图已保存: {filename}")
            
            # 5. 显示地图
            return self.display_map_on_screen(
                map_image, 
                (target_lat, target_lon), 
                distance, 
                location_info
            )
        else:
            print("❌ 地图生成失败")
            return False
    
    def run_telescope_session(self):
        """运行完整的望远镜会话"""
        print("🚀 启动Obscura No.7 Virtual Telescope...")
        
        try:
            # 1. 初始化编码器
            if not self.connect_encoder():
                return False
            
            if not self.init_encoder():
                return False
            
            # 2. 距离选择
            selected_distance = self.run_distance_selection()
            
            # 3. 位置探索
            success = self.explore_location(selected_distance)
            
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
    
    # 创建虚拟望远镜实例
    telescope = TelescopeMapExplorer(
        api_key=API_KEY,
        bus_number=3,
        address=0x36
    )
    
    # 运行会话
    telescope.run_telescope_session()
    
    print("🏁 Virtual Telescope 会话结束")

if __name__ == "__main__":
    main()