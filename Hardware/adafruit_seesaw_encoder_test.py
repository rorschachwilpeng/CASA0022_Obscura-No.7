#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Adafruit Seesaw I2C编码器测试脚本
专门针对Adafruit I2C QT Rotary Encoder (0x36)
使用seesaw协议
"""

import smbus
import time
import threading
import argparse
import signal
import sys
from datetime import datetime

# Seesaw寄存器定义
SEESAW_STATUS_BASE = 0x00
SEESAW_STATUS_HW_ID = 0x01
SEESAW_STATUS_VERSION = 0x02
SEESAW_STATUS_OPTIONS = 0x03
SEESAW_STATUS_TEMP = 0x04
SEESAW_STATUS_SWRST = 0x7F

SEESAW_GPIO_BASE = 0x01
SEESAW_GPIO_DIRSET_BULK = 0x02
SEESAW_GPIO_DIRCLR_BULK = 0x03
SEESAW_GPIO_BULK = 0x04
SEESAW_GPIO_BULK_SET = 0x05
SEESAW_GPIO_BULK_CLR = 0x06
SEESAW_GPIO_BULK_TOGGLE = 0x07
SEESAW_GPIO_INTENSET = 0x08
SEESAW_GPIO_INTENCLR = 0x09
SEESAW_GPIO_INTFLAG = 0x0A
SEESAW_GPIO_PULLENSET = 0x0B
SEESAW_GPIO_PULLENCLR = 0x0C

SEESAW_TIMER_BASE = 0x08
SEESAW_TIMER_STATUS = 0x00
SEESAW_TIMER_PWM = 0x01
SEESAW_TIMER_FREQ = 0x02

SEESAW_ENCODER_BASE = 0x11
SEESAW_ENCODER_STATUS = 0x00
SEESAW_ENCODER_INTENSET = 0x02
SEESAW_ENCODER_INTENCLR = 0x03
SEESAW_ENCODER_POSITION = 0x04
SEESAW_ENCODER_DELTA = 0x05

SEESAW_NEOPIXEL_BASE = 0x0E
SEESAW_NEOPIXEL_STATUS = 0x00
SEESAW_NEOPIXEL_PIN = 0x01
SEESAW_NEOPIXEL_SPEED = 0x02
SEESAW_NEOPIXEL_BUF_LENGTH = 0x03
SEESAW_NEOPIXEL_BUF = 0x04
SEESAW_NEOPIXEL_SHOW = 0x05

class AdafruitSeesawEncoder:
    def __init__(self, bus_number, address=0x36):
        """
        初始化Adafruit Seesaw编码器
        
        Args:
            bus_number (int): I2C总线号
            address (int): I2C设备地址 (默认0x36)
        """
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        self.is_running = False
        
        # 编码器状态
        self.encoder_position = 0
        self.last_position = 0
        self.button_pressed = False
        
        # 回调函数
        self.rotation_callback = None
        self.button_callback = None
        
    def connect(self):
        """连接到I2C总线"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            print(f"✓ 成功连接到I2C总线 {self.bus_number}")
            return True
        except Exception as e:
            print(f"✗ 连接I2C总线失败: {e}")
            return False
    
    def write_register(self, reg_base, reg_addr, data=None):
        """写入seesaw寄存器"""
        try:
            if data is None:
                # 只写寄存器地址
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr])
            elif isinstance(data, int):
                # 写单个字节
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr, data])
            else:
                # 写多个字节
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            print(f"写寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return False
    
    def read_register(self, reg_base, reg_addr, length=1):
        """读取seesaw寄存器"""
        try:
            # 先写寄存器地址
            self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr])
            time.sleep(0.001)  # 短暂延迟
            
            # 读取数据
            if length == 1:
                data = self.bus.read_byte(self.address)
                return data
            else:
                data = self.bus.read_i2c_block_data(self.address, 0, length)
                return data
        except Exception as e:
            print(f"读寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return None
    
    def software_reset(self):
        """软件复位"""
        print("执行软件复位...")
        return self.write_register(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
    
    def get_hardware_id(self):
        """获取硬件ID"""
        hw_id = self.read_register(SEESAW_STATUS_BASE, SEESAW_STATUS_HW_ID)
        if hw_id is not None:
            print(f"硬件ID: 0x{hw_id:02x}")
            return hw_id
        return None
    
    def get_version(self):
        """获取版本信息"""
        try:
            version_data = self.read_register(SEESAW_STATUS_BASE, SEESAW_STATUS_VERSION, 4)
            if version_data and len(version_data) >= 4:
                version = (version_data[0] << 24) | (version_data[1] << 16) | (version_data[2] << 8) | version_data[3]
                print(f"固件版本: 0x{version:08x}")
                return version
        except Exception as e:
            print(f"获取版本失败: {e}")
        return None
    
    def get_options(self):
        """获取选项信息"""
        try:
            options_data = self.read_register(SEESAW_STATUS_BASE, SEESAW_STATUS_OPTIONS, 4)
            if options_data and len(options_data) >= 4:
                options = (options_data[0] << 24) | (options_data[1] << 16) | (options_data[2] << 8) | options_data[3]
                print(f"设备选项: 0x{options:08x}")
                return options
        except Exception as e:
            print(f"获取选项失败: {e}")
        return None
    
    def init_encoder(self):
        """初始化编码器"""
        print("初始化编码器...")
        
        # 启用编码器中断
        success = self.write_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_INTENSET, 0x01)
        if success:
            print("✓ 编码器中断已启用")
        
        # 设置按钮引脚为输入并启用上拉
        button_pin = 24  # 按钮连接到seesaw pin 24
        pin_mask = 1 << button_pin
        
        # 设置为输入
        pin_bytes = [(pin_mask >> 24) & 0xFF, (pin_mask >> 16) & 0xFF, 
                     (pin_mask >> 8) & 0xFF, pin_mask & 0xFF]
        self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, pin_bytes)
        
        # 启用上拉
        self.write_register(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, pin_bytes)
        
        print("✓ 按钮引脚已配置")
        return True
    
    def get_encoder_position(self):
        """获取编码器位置"""
        try:
            pos_data = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_POSITION, 4)
            if pos_data and len(pos_data) >= 4:
                # 转换为32位有符号整数
                position = (pos_data[0] << 24) | (pos_data[1] << 16) | (pos_data[2] << 8) | pos_data[3]
                # 处理负数
                if position > 0x7FFFFFFF:
                    position -= 0x100000000
                return position
        except Exception as e:
            print(f"读取编码器位置失败: {e}")
        return None
    
    def get_encoder_delta(self):
        """获取编码器增量"""
        try:
            delta_data = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_DELTA, 4)
            if delta_data and len(delta_data) >= 4:
                # 转换为32位有符号整数
                delta = (delta_data[0] << 24) | (delta_data[1] << 16) | (delta_data[2] << 8) | delta_data[3]
                # 处理负数
                if delta > 0x7FFFFFFF:
                    delta -= 0x100000000
                return delta
        except Exception as e:
            print(f"读取编码器增量失败: {e}")
        return None
    
    def get_button_state(self):
        """获取按钮状态"""
        try:
            # 读取GPIO状态
            gpio_data = self.read_register(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
            if gpio_data and len(gpio_data) >= 4:
                gpio_state = (gpio_data[0] << 24) | (gpio_data[1] << 16) | (gpio_data[2] << 8) | gpio_data[3]
                button_pin = 24
                button_state = (gpio_state >> button_pin) & 1
                return button_state == 0  # 按钮是低电平有效
        except Exception as e:
            print(f"读取按钮状态失败: {e}")
        return False
    
    def set_neopixel_color(self, r, g, b):
        """设置NeoPixel颜色"""
        try:
            # 设置NeoPixel引脚
            self.write_register(SEESAW_NEOPIXEL_BASE, SEESAW_NEOPIXEL_PIN, 6)
            
            # 设置缓冲区长度
            self.write_register(SEESAW_NEOPIXEL_BASE, SEESAW_NEOPIXEL_BUF_LENGTH, [0, 3])
            
            # 设置颜色数据 (GRB格式)
            self.write_register(SEESAW_NEOPIXEL_BASE, SEESAW_NEOPIXEL_BUF, [0, 0, g, r, b])
            
            # 显示
            self.write_register(SEESAW_NEOPIXEL_BASE, SEESAW_NEOPIXEL_SHOW)
            
            return True
        except Exception as e:
            print(f"设置NeoPixel失败: {e}")
            return False
    
    def test_device_info(self):
        """测试设备信息"""
        print("\n=== 设备信息测试 ===")
        
        # 软件复位
        if self.software_reset():
            time.sleep(0.1)  # 等待复位完成
        
        # 获取硬件信息
        hw_id = self.get_hardware_id()
        version = self.get_version()
        options = self.get_options()
        
        if hw_id is not None:
            print("✓ 设备响应正常")
            return True
        else:
            print("✗ 设备无响应")
            return False
    
    def test_encoder_functionality(self, duration=30):
        """测试编码器功能"""
        print(f"\n=== 编码器功能测试 ({duration}秒) ===")
        print("请旋转编码器和按压按钮...")
        
        if not self.init_encoder():
            return False
        
        # 设置NeoPixel为蓝色表示开始测试
        self.set_neopixel_color(0, 0, 255)
        
        start_time = time.time()
        last_position = self.get_encoder_position()
        rotation_count = 0
        button_presses = 0
        last_button_state = False
        
        while time.time() - start_time < duration:
            # 检查编码器位置
            current_position = self.get_encoder_position()
            if current_position is not None and last_position is not None:
                if current_position != last_position:
                    delta = current_position - last_position
                    direction = "顺时针" if delta > 0 else "逆时针"
                    rotation_count += abs(delta)
                    print(f"编码器旋转: {direction}, 位置: {current_position}, 增量: {delta}")
                    
                    # 根据方向改变NeoPixel颜色
                    if delta > 0:
                        self.set_neopixel_color(0, 255, 0)  # 绿色 - 顺时针
                    else:
                        self.set_neopixel_color(255, 0, 0)  # 红色 - 逆时针
                    
                    last_position = current_position
            
            # 检查按钮状态
            button_state = self.get_button_state()
            if button_state != last_button_state:
                if button_state:
                    button_presses += 1
                    print(f"按钮按下 (第{button_presses}次)")
                    self.set_neopixel_color(255, 255, 0)  # 黄色 - 按钮按下
                else:
                    print("按钮释放")
                    self.set_neopixel_color(0, 0, 255)  # 蓝色 - 按钮释放
                
                last_button_state = button_state
            
            time.sleep(0.05)  # 20Hz采样率
        
        # 测试结束，关闭NeoPixel
        self.set_neopixel_color(0, 0, 0)
        
        print(f"\n测试结果:")
        print(f"  旋转次数: {rotation_count}")
        print(f"  按钮按压次数: {button_presses}")
        
        if rotation_count > 0 or button_presses > 0:
            print("✓ 编码器工作正常!")
            return True
        else:
            print("⚠ 未检测到编码器活动")
            return False

def signal_handler(sig, frame):
    """信号处理函数"""
    print("\n\n收到中断信号，正在退出...")
    sys.exit(0)

def main():
    """主函数"""
    # 使用默认值，避免命令行参数问题
    bus_number = 22
    address = 0x36
    duration = 30
    
    # 如果有命令行参数，尝试解析
    if len(sys.argv) > 1:
        try:
            parser = argparse.ArgumentParser(description="Adafruit Seesaw I2C编码器测试")
            parser.add_argument("--bus", type=int, default=22,
                               help="I2C总线号 (默认: 22)")
            parser.add_argument("--address", type=str, default="0x36",
                               help="I2C设备地址 (默认: 0x36)")
            parser.add_argument("--duration", type=int, default=30,
                               help="测试持续时间（秒，默认: 30）")
            
            args = parser.parse_args()
            
            bus_number = args.bus
            duration = args.duration
            
            # 解析地址
            if args.address.startswith('0x'):
                address = int(args.address, 16)
            else:
                address = int(args.address)
                
        except Exception as e:
            print(f"参数解析错误: {e}")
            print("使用默认参数...")
    
    print("Adafruit Seesaw I2C编码器测试程序")
    print("=" * 50)
    print(f"I2C总线: {bus_number}")
    print(f"设备地址: 0x{address:02x}")
    print(f"测试时长: {duration}秒")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建编码器实例
    encoder = AdafruitSeesawEncoder(bus_number, address)
    
    try:
        # 连接I2C总线
        if not encoder.connect():
            print("连接失败，请检查硬件连接")
            return
        
        # 测试设备信息
        if not encoder.test_device_info():
            print("设备信息测试失败，请检查设备是否为Adafruit Seesaw编码器")
            return
        
        # 测试编码器功能
        encoder.test_encoder_functionality(duration)
        
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
    
    print("测试结束")

if __name__ == "__main__":
    main() 