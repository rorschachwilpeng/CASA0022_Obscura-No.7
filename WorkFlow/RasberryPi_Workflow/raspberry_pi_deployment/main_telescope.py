#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 Virtual Telescope - Main Entry Point for Raspberry Pi
树莓派虚拟望远镜主程序
"""

import sys
import os
import time
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# 导入核心组件
try:
    from telescope_workflow import RaspberryPiTelescopeWorkflow
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from telescope_workflow import RaspberryPiTelescopeWorkflow

def show_banner():
    """显示启动横幅"""
    print("\n" + "=" * 60)
    print("🔭 OBSCURA NO.7 VIRTUAL TELESCOPE 🔭")
    print("=" * 60)
    print("🍓 Running on Raspberry Pi")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌟 Virtual Environmental Art Generation System")
    print("=" * 60)

def show_menu():
    """显示主菜单"""
    print("\n📋 请选择操作:")
    print("1. 🔭 启动虚拟望远镜会话")
    print("2. 🔧 硬件状态检查")
    print("3. ⚙️ 配置检查")
    print("4. 📜 查看最近的结果")
    print("5. 🧪 运行硬件测试")
    print("0. ❌ 退出程序")

def test_hardware():
    """测试硬件连接"""
    print("\n🔧 正在检查硬件状态...")
    
    try:
        try:
            from core.raspberry_pi_hardware import RaspberryPiHardware
            from core.config_manager import ConfigManager
        except ImportError:
            from raspberry_pi_hardware import RaspberryPiHardware
            from config_manager import ConfigManager
        
        # 加载配置
        config_manager = ConfigManager()
        
        # 初始化硬件
        hardware = RaspberryPiHardware(config_manager.config)
        
        # 获取硬件状态
        status = hardware.get_hardware_status()
        
        print("\n📊 硬件状态报告:")
        print(f"   树莓派GPIO库: {'✅ 可用' if status['hardware_available'] else '❌ 不可用'}")
        print(f"   编码器:       {'✅ 已连接' if status['encoder_available'] else '❌ 未连接'}")
        print(f"   磁感器:       {'✅ 已连接' if status['compass_available'] else '❌ 未连接'}")
        print(f"   按钮:         {'✅ 已连接' if status['button_available'] else '❌ 未连接'}")
        
        if not status['hardware_available']:
            print("\n⚠️ 注意: 运行在模拟模式")
            print("   在真实树莓派上运行时会启用硬件功能")
        
        # 清理资源
        hardware.cleanup()
        
    except Exception as e:
        print(f"\n❌ 硬件检查失败: {e}")

def check_config():
    """检查配置状态"""
    print("\n⚙️ 正在检查配置...")
    
    try:
        try:
            from core.config_manager import ConfigManager
        except ImportError:
            from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        print("\n📋 配置状态:")
        
        # API配置检查
        api_keys = config.get('api_keys', {})
        print(f"   OpenWeather API: {'✅ 已配置' if api_keys.get('openweather_api_key') else '❌ 未配置'}")
        print(f"   OpenAI API:      {'✅ 已配置' if api_keys.get('openai_api_key') else '❌ 未配置'}")
        print(f"   Cloudinary:      {'✅ 已配置' if api_keys.get('cloudinary_url') else '❌ 未配置'}")
        
        # 硬件配置检查
        hardware_config = config.get('hardware', {})
        print(f"   硬件配置:        {'✅ 已加载' if hardware_config else '❌ 缺失'}")
        
        # API端点检查
        api_endpoints = config.get('api_endpoints', {})
        print(f"   API端点:         {'✅ 已配置' if api_endpoints else '❌ 缺失'}")
        
    except Exception as e:
        print(f"\n❌ 配置检查失败: {e}")

def show_recent_results():
    """显示最近的结果"""
    print("\n📜 查看最近的工作流结果...")
    
    results_dir = 'outputs/workflow_results'
    
    if not os.path.exists(results_dir):
        print("❌ 还没有任何工作流结果")
        return
    
    try:
        # 获取最近的结果文件
        result_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        
        if not result_files:
            print("❌ 还没有任何工作流结果")
            return
        
        # 按修改时间排序
        result_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
        
        print(f"\n📊 找到 {len(result_files)} 个结果文件:")
        
        for i, filename in enumerate(result_files[:5]):  # 只显示最近5个
            filepath = os.path.join(results_dir, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            print(f"   {i+1}. {filename} - {mtime.strftime('%Y-%m-%d %H:%M')}")
        
        if len(result_files) > 5:
            print(f"   ... 和其他 {len(result_files) - 5} 个文件")
            
    except Exception as e:
        print(f"❌ 读取结果失败: {e}")

def main():
    """主函数"""
    show_banner()
    
    while True:
        try:
            show_menu()
            choice = input("\n🎯 请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("\n👋 感谢使用 Obscura No.7 虚拟望远镜!")
                print("🌟 愿您的探索之旅充满惊喜!")
                break
                
            elif choice == '1':
                print("\n🚀 启动虚拟望远镜会话...")
                try:
                    workflow = RaspberryPiTelescopeWorkflow()
                    result = workflow.run_telescope_session()
                    
                    if result.get('success'):
                        print("\n🎉 会话成功完成!")
                    else:
                        print(f"\n😞 会话失败: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"\n💥 会话异常: {e}")
                
                input("\n按 Enter 继续...")
                
            elif choice == '2':
                test_hardware()
                input("\n按 Enter 继续...")
                
            elif choice == '3':
                check_config()
                input("\n按 Enter 继续...")
                
            elif choice == '4':
                show_recent_results()
                input("\n按 Enter 继续...")
                
            elif choice == '5':
                print("\n🧪 运行硬件交互测试...")
                try:
                    try:
                        from core.raspberry_pi_hardware import RaspberryPiHardware
                        from core.config_manager import ConfigManager
                    except ImportError:
                        from raspberry_pi_hardware import RaspberryPiHardware
                        from config_manager import ConfigManager
                    
                    config_manager = ConfigManager()
                    hardware = RaspberryPiHardware(config_manager.config)
                    
                    print("📏 测试距离输入 (10秒超时)...")
                    distance = hardware.read_distance_input(timeout=10)
                    print(f"✅ 距离: {distance:.1f} km")
                    
                    print("🧭 测试方向读取...")
                    direction = hardware.read_compass_direction()
                    print(f"✅ 方向: {direction:.1f}°")
                    
                    hardware.cleanup()
                    
                except Exception as e:
                    print(f"❌ 硬件测试失败: {e}")
                
                input("\n按 Enter 继续...")
                
            else:
                print("❌ 无效选择，请重新输入")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ 用户中断程序")
            break
        except Exception as e:
            print(f"\n💥 程序异常: {e}")
            input("按 Enter 继续...")

if __name__ == "__main__":
    main() 