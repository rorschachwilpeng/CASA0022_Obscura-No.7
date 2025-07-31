#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard Input Workflow Test for Obscura No.7 Virtual Telescope
测试键盘输入工作流 - 无需硬件设备

This test script allows you to:
- Input distance, direction, and time parameters via keyboard
- Run the complete telescope workflow
- Test different parameter combinations
- Verify the Vision Description generation with different coordinates
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for importing core modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import workflow modules
from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow
from core.config_manager import ConfigManager
from core.coordinate_calculator import CoordinateCalculator

class KeyboardInputWorkflowTest:
    """测试类 - 键盘输入工作流测试"""
    
    def __init__(self):
        """初始化测试"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 预设的测试参数组合
        self.preset_combinations = [
            {"distance": 5.0, "direction": 0.0, "time": 0.0, "description": "近距离正北方向，当前时间"},
            {"distance": 15.0, "direction": 90.0, "time": 5.0, "description": "中距离正东方向，未来5年"},
            {"distance": 30.0, "direction": 180.0, "time": 10.0, "description": "远距离正南方向，未来10年"},
            {"distance": 45.0, "direction": 270.0, "time": 20.0, "description": "超远距离正西方向，未来20年"},
            {"distance": 25.0, "direction": 45.0, "time": 0.0, "description": "中距离东北方向，当前时间"},
            {"distance": 35.0, "direction": 225.0, "time": 15.0, "description": "远距离西南方向，未来15年"}
        ]
        
        self.test_results = []
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
    
    def print_banner(self):
        """打印测试横幅"""
        print("\n" + "=" * 80)
        print("🔭 Obscura No.7 Virtual Telescope - 键盘输入工作流测试")
        print("=" * 80)
        print("📝 说明：")
        print("   • 此测试允许您通过键盘输入参数来测试完整工作流")
        print("   • 无需连接硬件设备")
        print("   • 可以验证不同参数组合生成的Vision Description")
        print("   • 测试结果将保存到日志文件")
        print("=" * 80)
    
    def get_user_input(self) -> Dict[str, float]:
        """获取用户键盘输入"""
        print("\n📊 请输入测试参数:")
        print("-" * 40)
        
        try:
            while True:
                distance_input = input("📏 距离 (km, 1-50，回车默认25): ").strip()
                if distance_input == "":
                    distance = 25.0
                    break
                try:
                    distance = float(distance_input)
                    if 1 <= distance <= 50:
                        break
                    else:
                        print("   ❌ 距离必须在1-50km之间")
                except ValueError:
                    print("   ❌ 请输入有效的数字")
            
            while True:
                direction_input = input("🧭 方向 (度, 0-360，回车默认0): ").strip()
                if direction_input == "":
                    direction = 0.0
                    break
                try:
                    direction = float(direction_input)
                    if 0 <= direction <= 360:
                        break
                    else:
                        print("   ❌ 方向必须在0-360度之间")
                except ValueError:
                    print("   ❌ 请输入有效的数字")
            
            while True:
                time_input = input("⏰ 时间偏移 (年, 0-50，回车默认0): ").strip()
                if time_input == "":
                    time_offset = 0.0
                    break
                try:
                    time_offset = float(time_input)
                    if 0 <= time_offset <= 50:
                        break
                    else:
                        print("   ❌ 时间偏移必须在0-50年之间")
                except ValueError:
                    print("   ❌ 请输入有效的数字")
            
            return {
                'distance_km': distance,
                'direction_degrees': direction,
                'time_offset_years': time_offset
            }
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消输入")
            return None
    
    def show_preset_menu(self) -> Optional[Dict[str, float]]:
        """显示预设参数菜单"""
        print("\n🎯 预设参数组合:")
        print("-" * 50)
        
        for i, preset in enumerate(self.preset_combinations, 1):
            print(f"{i}. {preset['description']}")
            print(f"   距离: {preset['distance']}km, 方向: {preset['direction']}°, 时间: +{preset['time']}年")
        
        print(f"{len(self.preset_combinations) + 1}. 手动输入参数")
        print(f"{len(self.preset_combinations) + 2}. 退出测试")
        
        try:
            while True:
                choice = input(f"\n请选择 (1-{len(self.preset_combinations) + 2}): ").strip()
                
                if choice == "":
                    continue
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(self.preset_combinations):
                        preset = self.preset_combinations[choice_num - 1]
                        return {
                            'distance_km': preset['distance'],
                            'direction_degrees': preset['direction'],
                            'time_offset_years': preset['time']
                        }
                    elif choice_num == len(self.preset_combinations) + 1:
                        return self.get_user_input()
                    elif choice_num == len(self.preset_combinations) + 2:
                        return None
                    else:
                        print(f"   ❌ 请输入1-{len(self.preset_combinations) + 2}之间的数字")
                except ValueError:
                    print("   ❌ 请输入有效的数字")
                    
        except KeyboardInterrupt:
            print("\n\n👋 用户取消选择")
            return None
    
    def preview_coordinates(self, params: Dict[str, float]):
        """预览坐标计算结果"""
        print(f"\n🗺️ 坐标预览:")
        print("-" * 30)
        
        try:
            # 初始化坐标计算器
            config_manager = ConfigManager('config/config.json')
            coord_calc = CoordinateCalculator(config_manager.config)
            
            # 计算目标坐标
            base_lat = coord_calc.base_lat
            base_lon = coord_calc.base_lon
            
            result = coord_calc.calculate_target_coordinates(
                base_lat, base_lon,
                params['distance_km'] * 1000,  # 转换为米
                params['direction_degrees']
            )
            
            print(f"📍 起点: {base_lat:.4f}, {base_lon:.4f}")
            print(f"📍 目标: {result['latitude']:.4f}, {result['longitude']:.4f}")
            print(f"📏 距离: {params['distance_km']}km")
            print(f"🧭 方向: {params['direction_degrees']}°")
            
        except Exception as e:
            print(f"❌ 坐标预览失败: {e}")
    
    def run_workflow_test(self, params: Dict[str, float]) -> Dict[str, Any]:
        """运行工作流测试"""
        print(f"\n🚀 开始运行工作流测试...")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 初始化工作流
            workflow = RaspberryPiTelescopeWorkflow()
            
            # 运行工作流（传递键盘输入的参数）
            result = workflow.run_telescope_session(hardware_params=params)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 记录测试结果
            test_result = {
                'timestamp': datetime.now().isoformat(),
                'input_parameters': params,
                'workflow_result': result,
                'execution_time': execution_time,
                'success': result.get('success', False) if result else False
            }
            
            self.test_results.append(test_result)
            
            return test_result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_result = {
                'timestamp': datetime.now().isoformat(),
                'input_parameters': params,
                'error': str(e),
                'execution_time': execution_time,
                'success': False
            }
            
            self.test_results.append(error_result)
            self.logger.error(f"工作流测试失败: {e}")
            
            return error_result
    
    def display_test_results(self, test_result: Dict[str, Any]):
        """显示测试结果"""
        print("\n" + "=" * 60)
        print("📊 测试结果报告")
        print("=" * 60)
        
        params = test_result['input_parameters']
        print(f"📏 输入参数:")
        print(f"   距离: {params['distance_km']}km")
        print(f"   方向: {params['direction_degrees']}°")
        print(f"   时间偏移: +{params['time_offset_years']}年")
        
        print(f"\n⏱️ 执行时间: {test_result['execution_time']:.2f}秒")
        print(f"✅ 执行状态: {'成功' if test_result['success'] else '失败'}")
        
        if test_result['success'] and 'workflow_result' in test_result:
            workflow_result = test_result['workflow_result']
            
            if 'data' in workflow_result:
                data = workflow_result['data']
                
                # 显示坐标信息
                if 'coordinates' in data:
                    coords = data['coordinates']
                    print(f"\n🗺️ 计算得到的坐标:")
                    print(f"   纬度: {coords.get('latitude', 'N/A')}")
                    print(f"   经度: {coords.get('longitude', 'N/A')}")
                
                # 显示环境数据
                if 'weather_data' in data:
                    weather = data['weather_data']
                    print(f"\n🌤️ 环境数据:")
                    print(f"   温度: {weather.get('temperature', 'N/A')}°C")
                    print(f"   湿度: {weather.get('humidity', 'N/A')}%")
                
                # 显示生成的图像路径
                if 'generated_image' in data:
                    print(f"\n🎨 生成的图像: {data['generated_image']}")
                
                # 显示Vision Description（重点）
                if 'style_prediction' in data and 'description' in data['style_prediction']:
                    description = data['style_prediction']['description']
                    print(f"\n📝 Vision Description:")
                    print("-" * 40)
                    print(f"{description}")
                    print("-" * 40)
                
        else:
            if 'error' in test_result:
                print(f"\n❌ 错误信息: {test_result['error']}")
    
    def save_test_summary(self):
        """保存测试总结"""
        if not self.test_results:
            return
        
        summary_file = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'test_session': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r['success']),
                'failed_tests': sum(1 for r in self.test_results if not r['success'])
            },
            'test_results': self.test_results
        }
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 测试总结已保存到: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试总结失败: {e}")
    
    def run_interactive_test(self):
        """运行交互式测试"""
        self.print_banner()
        
        test_count = 0
        
        try:
            while True:
                print(f"\n🔄 测试轮次 {test_count + 1}")
                
                # 获取测试参数
                params = self.show_preset_menu()
                
                if params is None:
                    print("\n👋 退出测试")
                    break
                
                # 预览坐标
                self.preview_coordinates(params)
                
                # 确认执行
                confirm = input(f"\n确认执行测试? (y/n，回车默认y): ").strip().lower()
                if confirm in ['n', 'no']:
                    print("⏭️ 跳过此次测试")
                    continue
                
                # 运行测试
                test_result = self.run_workflow_test(params)
                
                # 显示结果
                self.display_test_results(test_result)
                
                test_count += 1
                
                # 询问是否继续
                continue_test = input(f"\n继续下一轮测试? (y/n，回车默认y): ").strip().lower()
                if continue_test in ['n', 'no']:
                    break
                    
        except KeyboardInterrupt:
            print("\n\n👋 用户中断测试")
        
        finally:
            # 保存测试总结
            if test_count > 0:
                print(f"\n📊 总共完成 {test_count} 轮测试")
                self.save_test_summary()

def main():
    """主函数"""
    test = KeyboardInputWorkflowTest()
    test.run_interactive_test()

if __name__ == "__main__":
    main() 