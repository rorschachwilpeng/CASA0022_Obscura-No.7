#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码器距离控制测试脚本
任务1：测试旋钮变化 → 距离值映射
"""

import smbus
import time
import signal
import sys
from datetime import datetime

# Seesaw寄存器定义（复用之前的定义）
SEESAW_STATUS_BASE = 0x00
SEESAW_STATUS_SWRST = 0x7F
SEESAW_ENCODER_BASE = 0x11
SEESAW_ENCODER_INTENSET = 0x02
SEESAW_ENCODER_POSITION = 0x04
SEESAW_ENCODER_DELTA = 0x05

class EncoderDistanceController:
    def __init__(self, bus_number=3, address=0x36):
        """
        编码器距离控制器
        
        Args:
            bus_number (int): I2C总线号 (默认3)
            address (int): I2C设备地址 (默认0x36)
        """
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        self.is_running = False
        
        # 距离控制参数
        self.min_distance = 100      # 最小距离：100米
        self.max_distance = 10000    # 最大距离：10公里
        self.distance_step = 100     # 每格距离：100米
        self.current_distance = 1000 # 初始距离：1公里
        
        # 编码器状态
        self.last_position = 0
        self.encoder_position = 0
        
    def connect(self):
        """连接到I2C总线"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            print(f"✅ 成功连接到I2C总线 {self.bus_number}")
            return True
        except Exception as e:
            print(f"❌ 连接I2C总线失败: {e}")
            return False
    
    def write_register(self, reg_base, reg_addr, data=None):
        """写入seesaw寄存器"""
        try:
            if data is None:
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr])
            elif isinstance(data, int):
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr, data])
            else:
                self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr] + list(data))
            return True
        except Exception as e:
            print(f"写寄存器失败 {reg_base:02x}:{reg_addr:02x} - {e}")
            return False
    
    def read_register(self, reg_base, reg_addr, length=1):
        """读取seesaw寄存器"""
        try:
            self.bus.write_i2c_block_data(self.address, reg_base, [reg_addr])
            time.sleep(0.001)
            
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
    
    def init_encoder(self):
        """初始化编码器"""
        print("初始化编码器...")
        
        # 软件复位
        if self.software_reset():
            time.sleep(0.1)
        
        # 启用编码器中断
        success = self.write_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_INTENSET, 0x01)
        if success:
            print("✅ 编码器初始化成功")
            
            # 获取初始位置
            self.last_position = self.get_encoder_position()
            if self.last_position is not None:
                print(f"📍 初始编码器位置: {self.last_position}")
            return True
        else:
            print("❌ 编码器初始化失败")
            return False
    
    def get_encoder_position(self):
        """获取编码器位置"""
        try:
            pos_data = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_POSITION, 4)
            if pos_data and len(pos_data) >= 4:
                position = (pos_data[0] << 24) | (pos_data[1] << 16) | (pos_data[2] << 8) | pos_data[3]
                if position > 0x7FFFFFFF:
                    position -= 0x100000000
                return position
        except Exception as e:
            print(f"读取编码器位置失败: {e}")
        return None
    
    def position_to_distance(self, position_delta):
        """将编码器位置变化转换为距离值"""
        # 每4个位置变化 = 1个距离步长
        distance_change = (position_delta // 4) * self.distance_step
        
        new_distance = self.current_distance + distance_change
        
        # 限制在有效范围内
        if new_distance < self.min_distance:
            new_distance = self.min_distance
        elif new_distance > self.max_distance:
            new_distance = self.max_distance
            
        return new_distance
    
    def format_distance(self, distance):
        """格式化距离显示"""
        if distance >= 1000:
            return f"{distance/1000:.1f}km"
        else:
            return f"{distance}m"
    
    def test_distance_control(self, duration=60):
        """测试距离控制功能"""
        print("=" * 50)
        print("🎯 编码器距离控制测试")
        print("=" * 50)
        print(f"📏 距离范围: {self.format_distance(self.min_distance)} - {self.format_distance(self.max_distance)}")
        print(f"📐 距离步长: {self.format_distance(self.distance_step)}")
        print(f"🎚️ 初始距离: {self.format_distance(self.current_distance)}")
        print(f"⏱️ 测试时长: {duration}秒")
        print("🔄 请旋转编码器来调整距离...")
        print("-" * 50)
        
        start_time = time.time()
        update_count = 0
        
        while time.time() - start_time < duration:
            # 获取当前编码器位置
            current_position = self.get_encoder_position()
            
            if current_position is not None and self.last_position is not None:
                # 计算位置变化
                position_delta = current_position - self.last_position
                
                if position_delta != 0:
                    # 更新距离
                    new_distance = self.position_to_distance(position_delta)
                    
                    if new_distance != self.current_distance:
                        self.current_distance = new_distance
                        update_count += 1
                        
                        # 显示更新信息
                        direction = "增加" if position_delta > 0 else "减少"
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        print(f"[{timestamp}] 🔄 距离{direction}: {self.format_distance(self.current_distance)} "
                              f"(编码器: {current_position}, 变化: {position_delta:+d})")
                    
                    # 更新last_position
                    self.last_position = current_position
            
            time.sleep(0.05)  # 20Hz采样率
        
        print("-" * 50)
        print(f"✅ 测试完成!")
        print(f"📊 总更新次数: {update_count}")
        print(f"🎯 最终距离: {self.format_distance(self.current_distance)}")
        
        return self.current_distance

def signal_handler(sig, frame):
    """信号处理函数"""
    print("\n\n🛑 收到中断信号，正在退出...")
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 启动编码器距离控制测试...")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建控制器实例
    controller = EncoderDistanceController(bus_number=3, address=0x36)
    
    try:
        # 连接I2C总线
        if not controller.connect():
            print("❌ 连接失败，请检查硬件连接")
            return
        
        # 初始化编码器
        if not controller.init_encoder():
            print("❌ 编码器初始化失败")
            return
        
        # 测试距离控制
        final_distance = controller.test_distance_control(duration=60)
        
        print(f"\n🎉 测试成功! 最终选择距离: {controller.format_distance(final_distance)}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    
    print("🏁 测试结束")

if __name__ == "__main__":
    main()
