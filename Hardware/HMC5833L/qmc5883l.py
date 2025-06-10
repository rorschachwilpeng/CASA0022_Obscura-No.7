#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMC5883L磁力计测试脚本 - 树莓派版本
"""

import smbus
import time
import math

class QMC5883L:
    def __init__(self, bus_number=4, address=0x0D):
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        
        # QMC5883L寄存器地址
        self.REG_X_LSB = 0x00
        self.REG_X_MSB = 0x01
        self.REG_Y_LSB = 0x02
        self.REG_Y_MSB = 0x03
        self.REG_Z_LSB = 0x04
        self.REG_Z_MSB = 0x05
        self.REG_STATUS = 0x06
        self.REG_TEMP_LSB = 0x07
        self.REG_TEMP_MSB = 0x08
        self.REG_CONTROL1 = 0x09
        self.REG_CONTROL2 = 0x0A
        self.REG_PERIOD = 0x0B
        self.REG_CHIP_ID = 0x0D
        
    def connect(self):
        """连接到I2C总线"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            print(f"✅ 成功连接到I2C总线 {self.bus_number}")
            return True
        except Exception as e:
            print(f"❌ 连接I2C总线失败: {e}")
            return False
    
    def write_register(self, reg, value):
        """写入寄存器"""
        try:
            self.bus.write_byte_data(self.address, reg, value)
            return True
        except Exception as e:
            print(f"写寄存器失败: {e}")
            return False
    
    def read_register(self, reg):
        """读取寄存器"""
        try:
            return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            print(f"读寄存器失败: {e}")
            return None
    
    def detect_device(self):
        """检测设备"""
        print("🔍 检测QMC5883L设备...")
        
        try:
            self.bus.write_byte(self.address, 0)
            print(f"✅ 在地址 0x{self.address:02X} 发现设备")
            return True
        except Exception as e:
            print(f"❌ 地址 0x{self.address:02X} 无设备响应: {e}")
            return False
    
    def init(self):
        """初始化QMC5883L"""
        print("⚙️ 初始化QMC5883L...")
        
        # 软复位
        if not self.write_register(self.REG_CONTROL2, 0x80):
            return False
        time.sleep(0.1)
        
        # 配置控制寄存器1
        # OSR=512, RNG=8G, ODR=200Hz, MODE=Continuous
        if not self.write_register(self.REG_CONTROL1, 0x1D):
            return False
        
        # 设置周期寄存器
        if not self.write_register(self.REG_PERIOD, 0x01):
            return False
        
        print("✅ QMC5883L初始化完成")
        return True
    
    def read_raw_data(self):
        """读取原始磁场数据"""
        try:
            # 等待数据准备就绪
            status = self.read_register(self.REG_STATUS)
            if status is None or not (status & 0x01):
                return None, None, None
            
            # 读取6字节数据
            data = []
            for reg in range(self.REG_X_LSB, self.REG_Z_MSB + 1):
                byte_data = self.read_register(reg)
                if byte_data is None:
                    return None, None, None
                data.append(byte_data)
            
            # 组合成16位有符号整数
            x = self._combine_bytes(data[1], data[0])  # MSB, LSB
            y = self._combine_bytes(data[3], data[2])
            z = self._combine_bytes(data[5], data[4])
            
            return x, y, z
            
        except Exception as e:
            print(f"读取数据失败: {e}")
            return None, None, None
    
    def _combine_bytes(self, msb, lsb):
        """组合字节为有符号16位整数"""
        value = (msb << 8) | lsb
        if value > 32767:
            value -= 65536
        return value
    
    def calculate_heading(self, x, y):
        """计算方位角（度）"""
        heading = math.atan2(y, x)
        heading = math.degrees(heading)
        
        # 转换为0-360度范围
        if heading < 0:
            heading += 360
            
        return heading
    
    def get_direction_name(self, heading):
        """根据方位角获取方向名称"""
        directions = [
            "北", "东北偏北", "东北", "东北偏东",
            "东", "东南偏东", "东南", "东南偏南", 
            "南", "西南偏南", "西南", "西南偏西",
            "西", "西北偏西", "西北", "西北偏北"
        ]
        
        index = int((heading + 11.25) / 22.5) % 16
        return directions[index]
    
    def scan_i2c_bus(self):
        """扫描I2C总线"""
        print(f"🔍 扫描I2C总线 {self.bus_number}...")
        devices = []
        
        for addr in range(0x08, 0x78):
            try:
                self.bus.write_byte(addr, 0)
                devices.append(addr)
                print(f"   发现设备: 0x{addr:02X}")
            except:
                pass
        
        if not devices:
            print("   未发现任何设备")
        
        return devices

def main():
    print("🚀 QMC5883L磁力计测试程序")
    print("=" * 40)
    print(f"🧭 设备: QMC5883L磁力计")
    print(f"📡 I2C总线: 4")
    print(f"📍 地址: 0x0D")
    print(f"🔌 连接: GPIO20(SDA), GPIO21(SCL)")
    print("=" * 40)
    
    # 创建QMC5883L实例
    compass = QMC5883L(bus_number=4, address=0x0D)
    
    try:
        # 连接总线
        if not compass.connect():
            return
        
        # 扫描总线
        devices = compass.scan_i2c_bus()
        
        # 检测设备
        if not compass.detect_device():
            print("请检查连接:")
            print("  VCC → Pin 17 (3.3V)")
            print("  GND → Pin 20 (GND)")
            print("  SDA → Pin 38 (GPIO20)")
            print("  SCL → Pin 40 (GPIO21)")
            return
        
        # 初始化设备
        if not compass.init():
            return
        
        print("\n📊 开始方位测量...")
        print("时间    X轴      Y轴      Z轴      方位角   方向")
        print("-" * 55)
        
        while True:
            # 读取磁场数据
            x, y, z = compass.read_raw_data()
            
            if x is not None:
                # 计算方位角
                heading = compass.calculate_heading(x, y)
                direction = compass.get_direction_name(heading)
                
                # 输出结果
                print(f"{time.time()%1000:6.1f}  {x:6d}   {y:6d}   {z:6d}   {heading:6.1f}°  {direction}")
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
    
    print("🏁 测试结束")

if __name__ == "__main__":
    main()