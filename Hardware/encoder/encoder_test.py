#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码器旋转功能调试脚本
专门用于排查旋钮转动检测问题
"""

import smbus
import time
import signal
import sys

# Seesaw寄存器定义
SEESAW_STATUS_BASE = 0x00
SEESAW_STATUS_HW_ID = 0x01
SEESAW_STATUS_VERSION = 0x02
SEESAW_STATUS_SWRST = 0x7F

SEESAW_ENCODER_BASE = 0x11
SEESAW_ENCODER_STATUS = 0x00
SEESAW_ENCODER_INTENSET = 0x02
SEESAW_ENCODER_INTENCLR = 0x03
SEESAW_ENCODER_POSITION = 0x04
SEESAW_ENCODER_DELTA = 0x05

class EncoderRotationDebugger:
    def __init__(self, bus_number=3, address=0x36):
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        
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
            time.sleep(0.005)  # 增加延迟
            
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
        print("🔄 执行软件复位...")
        success = self.write_register(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)
        if success:
            time.sleep(0.5)  # 增加复位等待时间
            print("✅ 复位完成")
        return success
    
    def check_device_info(self):
        """检查设备信息"""
        print("📋 检查设备信息...")
        
        # 检查硬件ID
        hw_id = self.read_register(SEESAW_STATUS_BASE, SEESAW_STATUS_HW_ID)
        if hw_id is not None:
            print(f"🆔 硬件ID: 0x{hw_id:02x}")
        else:
            print("❌ 无法读取硬件ID")
            return False
            
        # 检查版本
        version_data = self.read_register(SEESAW_STATUS_BASE, SEESAW_STATUS_VERSION, 4)
        if version_data and len(version_data) >= 4:
            version = (version_data[0] << 24) | (version_data[1] << 16) | (version_data[2] << 8) | version_data[3]
            print(f"📌 固件版本: 0x{version:08x}")
        else:
            print("⚠️ 无法读取版本信息")
            
        return True
    
    def init_encoder_detailed(self):
        """详细的编码器初始化"""
        print("⚙️ 详细编码器初始化...")
        
        # 1. 清除编码器中断
        print("  1. 清除编码器中断...")
        self.write_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_INTENCLR, 0xFF)
        time.sleep(0.1)
        
        # 2. 检查编码器状态
        print("  2. 检查编码器状态...")
        status = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_STATUS)
        if status is not None:
            print(f"     编码器状态: 0x{status:02x}")
        
        # 3. 启用编码器中断
        print("  3. 启用编码器中断...")
        success = self.write_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_INTENSET, 0x01)
        if success:
            print("     ✅ 编码器中断已启用")
        else:
            print("     ❌ 编码器中断启用失败")
            return False
        
        # 4. 再次检查状态
        status = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_STATUS)
        if status is not None:
            print(f"     更新后状态: 0x{status:02x}")
        
        return True
    
    def get_encoder_position_detailed(self):
        """详细的编码器位置读取"""
        try:
            # 方法1: 直接读取位置
            pos_data = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_POSITION, 4)
            if pos_data and len(pos_data) >= 4:
                position = (pos_data[0] << 24) | (pos_data[1] << 16) | (pos_data[2] << 8) | pos_data[3]
                if position > 0x7FFFFFFF:
                    position -= 0x100000000
                return position, pos_data
            else:
                return None, None
        except Exception as e:
            print(f"     读取位置异常: {e}")
            return None, None
    
    def get_encoder_delta_detailed(self):
        """详细的编码器增量读取"""
        try:
            delta_data = self.read_register(SEESAW_ENCODER_BASE, SEESAW_ENCODER_DELTA, 4)
            if delta_data and len(delta_data) >= 4:
                delta = (delta_data[0] << 24) | (delta_data[1] << 16) | (delta_data[2] << 8) | delta_data[3]
                if delta > 0x7FFFFFFF:
                    delta -= 0x100000000
                return delta, delta_data
            else:
                return None, None
        except Exception as e:
            print(f"     读取增量异常: {e}")
            return None, None
    
    def debug_encoder_rotation(self, duration=30):
        """调试编码器旋转功能"""
        print("=" * 60)
        print("🔍 编码器旋转调试模式")
        print("=" * 60)
        print("📝 请缓慢旋转编码器，观察数值变化...")
        print("⏱️ 测试时长: {}秒".format(duration))
        print("-" * 60)
        
        # 获取初始位置
        initial_pos, initial_raw = self.get_encoder_position_detailed()
        if initial_pos is not None:
            print(f"📍 初始位置: {initial_pos} (原始数据: {initial_raw})")
        else:
            print("❌ 无法读取初始位置")
            return
        
        start_time = time.time()
        last_position = initial_pos
        sample_count = 0
        change_count = 0
        
        print(f"{'时间':<8} {'位置':<12} {'变化':<8} {'增量':<12} {'原始位置':<20} {'原始增量':<20}")
        print("-" * 90)
        
        while time.time() - start_time < duration:
            sample_count += 1
            
            # 读取当前位置
            current_pos, pos_raw = self.get_encoder_position_detailed()
            
            # 读取增量
            delta, delta_raw = self.get_encoder_delta_detailed()
            
            if current_pos is not None:
                position_change = current_pos - last_position
                
                if position_change != 0 or delta != 0:
                    change_count += 1
                    elapsed = time.time() - start_time
                    print(f"{elapsed:7.1f}s {current_pos:<12} {position_change:<+8} {delta if delta else 0:<12} {str(pos_raw):<20} {str(delta_raw):<20}")
                    last_position = current_pos
                
                # 每5秒显示一次当前状态（即使没有变化）
                elif sample_count % 100 == 0:  # 约每5秒
                    elapsed = time.time() - start_time
                    print(f"{elapsed:7.1f}s {current_pos:<12} {'0':<8} {'0':<12} {'(无变化)':<20} {'(无变化)':<20}")
            
            time.sleep(0.05)  # 20Hz采样率
        
        print("-" * 90)
        print(f"📊 调试统计:")
        print(f"   总采样次数: {sample_count}")
        print(f"   检测到变化次数: {change_count}")
        print(f"   最终位置: {current_pos if current_pos else '未知'}")
        
        if change_count == 0:
            print("\n⚠️ 没有检测到任何旋转变化！")
            print("🔧 可能的问题:")
            print("   1. 编码器硬件连接问题")
            print("   2. 编码器初始化失败")
            print("   3. 旋转幅度太小")
            print("   4. 编码器需要更多的初始化步骤")
        else:
            print(f"\n✅ 检测到 {change_count} 次旋转变化")

def signal_handler(sig, frame):
    print("\n\n🛑 收到中断信号，正在退出...")
    sys.exit(0)

def main():
    print("🚀 启动编码器旋转调试...")
    signal.signal(signal.SIGINT, signal_handler)
    
    debugger = EncoderRotationDebugger(bus_number=3, address=0x36)
    
    try:
        # 连接
        if not debugger.connect():
            return
        
        # 检查设备
        if not debugger.check_device_info():
            return
        
        # 复位
        if not debugger.software_reset():
            return
        
        # 初始化
        if not debugger.init_encoder_detailed():
            return
        
        # 调试旋转
        debugger.debug_encoder_rotation(duration=30)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 调试过程中出现错误: {e}")
    
    print("🏁 调试结束")

if __name__ == "__main__":
    main()