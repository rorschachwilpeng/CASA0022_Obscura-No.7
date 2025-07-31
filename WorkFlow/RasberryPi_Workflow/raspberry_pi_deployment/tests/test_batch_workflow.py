#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Workflow Test for Obscura No.7 Virtual Telescope
批量工作流测试 - 自动验证Vision Description的变化

This script automatically tests multiple parameter combinations to verify:
- Different coordinates generate different Vision Descriptions
- The parameter passing fix is working correctly
- All workflow steps complete successfully
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for importing core modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import workflow modules
from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow

class BatchWorkflowTest:
    """批量工作流测试类"""
    
    def __init__(self):
        """初始化测试"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 测试参数组合 - 覆盖不同距离、方向和时间
        self.test_cases = [
            {
                "name": "近距离北方", 
                "distance_km": 5.0, 
                "direction_degrees": 0.0, 
                "time_offset_years": 0.0,
                "expected_area": "伦敦市中心北部"
            },
            {
                "name": "中距离东方", 
                "distance_km": 20.0, 
                "direction_degrees": 90.0, 
                "time_offset_years": 5.0,
                "expected_area": "伦敦东部郊区"
            },
            {
                "name": "远距离南方", 
                "distance_km": 40.0, 
                "direction_degrees": 180.0, 
                "time_offset_years": 10.0,
                "expected_area": "英格兰南部"
            },
            {
                "name": "中距离西方", 
                "distance_km": 30.0, 
                "direction_degrees": 270.0, 
                "time_offset_years": 15.0,
                "expected_area": "伦敦西部"
            },
            {
                "name": "近距离东北", 
                "distance_km": 8.0, 
                "direction_degrees": 45.0, 
                "time_offset_years": 2.0,
                "expected_area": "伦敦东北部"
            },
            {
                "name": "远距离西南", 
                "distance_km": 35.0, 
                "direction_degrees": 225.0, 
                "time_offset_years": 20.0,
                "expected_area": "英格兰西南部"
            },
            {
                "name": "极近距离", 
                "distance_km": 2.0, 
                "direction_degrees": 315.0, 
                "time_offset_years": 0.0,
                "expected_area": "伦敦市中心"
            },
            {
                "name": "极远距离", 
                "distance_km": 50.0, 
                "direction_degrees": 135.0, 
                "time_offset_years": 25.0,
                "expected_area": "英格兰东南边界"
            }
        ]
        
        self.test_results = []
        self.vision_descriptions = []
    
    def setup_logging(self):
        """设置日志"""
        log_filename = f'batch_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_filename)
            ]
        )
        
        print(f"📄 详细日志将保存到: {log_filename}")
    
    def print_test_header(self):
        """打印测试头部信息"""
        print("\n" + "=" * 80)
        print("🔭 Obscura No.7 - 批量工作流测试")
        print("=" * 80)
        print("🎯 测试目标:")
        print("   • 验证参数传递修复是否有效")
        print("   • 确认不同参数生成不同的Vision Description")
        print("   • 检查工作流的稳定性和性能")
        print(f"   • 总共将测试 {len(self.test_cases)} 个参数组合")
        print("=" * 80)
    
    def run_single_test(self, test_case: Dict[str, Any], test_index: int) -> Dict[str, Any]:
        """运行单个测试案例"""
        
        print(f"\n🧪 测试案例 {test_index + 1}/{len(self.test_cases)}: {test_case['name']}")
        print("-" * 60)
        print(f"📏 距离: {test_case['distance_km']}km")
        print(f"🧭 方向: {test_case['direction_degrees']}°")
        print(f"⏰ 时间偏移: +{test_case['time_offset_years']}年")
        print(f"🎯 预期区域: {test_case['expected_area']}")
        
        start_time = time.time()
        
        try:
            # 准备硬件参数
            hardware_params = {
                'distance_km': test_case['distance_km'],
                'direction_degrees': test_case['direction_degrees'],
                'time_offset_years': test_case['time_offset_years']
            }
            
            # 初始化并运行工作流
            workflow = RaspberryPiTelescopeWorkflow()
            result = workflow.run_telescope_session(hardware_params=hardware_params)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 提取Vision Description
            vision_description = "未生成"
            coordinates = None
            weather_data = None
            image_path = None
            
            if (result and result.get('success') and 
                'data' in result and result['data']):
                
                data = result['data']
                
                # 提取坐标
                if 'coordinates' in data:
                    coordinates = data['coordinates']
                
                # 提取环境数据
                if 'weather_data' in data:
                    weather_data = data['weather_data']
                
                # 提取图像路径
                if 'generated_image' in data:
                    image_path = data['generated_image']
                
                # 提取Vision Description
                if ('style_prediction' in data and 
                    'description' in data['style_prediction']):
                    vision_description = data['style_prediction']['description']
            
            # 记录测试结果
            test_result = {
                'test_index': test_index + 1,
                'test_name': test_case['name'],
                'input_parameters': hardware_params,
                'expected_area': test_case['expected_area'],
                'execution_time': execution_time,
                'success': result.get('success', False) if result else False,
                'coordinates': coordinates,
                'weather_data': weather_data,
                'image_path': image_path,
                'vision_description': vision_description,
                'raw_result': result
            }
            
            # 显示简要结果
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"✅ 状态: {'成功' if test_result['success'] else '失败'}")
            
            if coordinates:
                print(f"📍 坐标: {coordinates.get('latitude', 'N/A'):.4f}, {coordinates.get('longitude', 'N/A'):.4f}")
            
            if vision_description != "未生成":
                # 显示Vision Description的前100个字符
                preview = vision_description[:100] + "..." if len(vision_description) > 100 else vision_description
                print(f"📝 描述预览: {preview}")
                
                # 记录完整描述用于比较
                self.vision_descriptions.append({
                    'test_name': test_case['name'],
                    'description': vision_description
                })
            
            return test_result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_result = {
                'test_index': test_index + 1,
                'test_name': test_case['name'],
                'input_parameters': hardware_params,
                'expected_area': test_case['expected_area'],
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'vision_description': "错误导致未生成"
            }
            
            print(f"❌ 测试失败: {str(e)}")
            self.logger.error(f"测试案例 {test_case['name']} 失败: {e}")
            
            return error_result
    
    def analyze_vision_descriptions(self):
        """分析Vision Description的差异"""
        print("\n" + "=" * 80)
        print("📊 Vision Description 差异分析")
        print("=" * 80)
        
        if len(self.vision_descriptions) < 2:
            print("❌ 没有足够的Vision Description进行比较分析")
            return
        
        # 检查描述是否相同
        all_descriptions = [desc['description'] for desc in self.vision_descriptions]
        unique_descriptions = set(all_descriptions)
        
        print(f"📈 总共生成了 {len(all_descriptions)} 个描述")
        print(f"🔍 其中唯一描述数量: {len(unique_descriptions)}")
        
        if len(unique_descriptions) == 1:
            print("⚠️ 警告: 所有测试案例生成了相同的Vision Description!")
            print("   这可能表明参数传递仍有问题")
        else:
            print("✅ 成功: 不同参数生成了不同的Vision Description")
            
            # 显示每个描述的关键词
            print("\n🔍 各测试案例的描述关键信息:")
            for desc_info in self.vision_descriptions:
                description = desc_info['description']
                # 提取地名和建筑物信息
                words = description.lower().split()
                landmarks = []
                
                # 查找可能的地标词汇
                landmark_keywords = ['hotel', 'restaurant', 'park', 'street', 'road', 'bridge', 
                                   'station', 'church', 'market', 'centre', 'center', 'building']
                
                for word in words:
                    if any(keyword in word for keyword in landmark_keywords):
                        landmarks.append(word)
                
                preview = description[:150] + "..." if len(description) > 150 else description
                print(f"\n🏷️ {desc_info['test_name']}:")
                print(f"   📝 {preview}")
                if landmarks:
                    print(f"   🏛️ 地标关键词: {', '.join(landmarks[:5])}")
    
    def generate_summary_report(self):
        """生成测试总结报告"""
        if not self.test_results:
            return
        
        # 统计信息
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - successful_tests
        avg_execution_time = sum(r['execution_time'] for r in self.test_results) / total_tests
        
        print("\n" + "=" * 80)
        print("📊 测试总结报告")
        print("=" * 80)
        print(f"📈 总测试数: {total_tests}")
        print(f"✅ 成功: {successful_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"📊 成功率: {(successful_tests/total_tests)*100:.1f}%")
        print(f"⏱️ 平均执行时间: {avg_execution_time:.2f}秒")
        
        # 保存详细报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"batch_test_report_{timestamp}.json"
        
        report = {
            'test_session': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': (successful_tests/total_tests)*100,
                'average_execution_time': avg_execution_time
            },
            'test_results': self.test_results,
            'vision_descriptions': self.vision_descriptions
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"💾 详细报告已保存到: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
    
    def run_batch_test(self):
        """运行批量测试"""
        self.print_test_header()
        
        try:
            # 运行所有测试案例
            for i, test_case in enumerate(self.test_cases):
                test_result = self.run_single_test(test_case, i)
                self.test_results.append(test_result)
                
                # 在测试之间稍作停顿，避免API限制
                if i < len(self.test_cases) - 1:
                    print("⏳ 等待3秒后继续下一个测试...")
                    time.sleep(3)
            
            # 分析结果
            self.analyze_vision_descriptions()
            
            # 生成报告
            self.generate_summary_report()
            
        except KeyboardInterrupt:
            print("\n\n👋 用户中断批量测试")
            if self.test_results:
                print("🔄 正在保存已完成的测试结果...")
                self.generate_summary_report()
        
        except Exception as e:
            self.logger.error(f"批量测试出现错误: {e}")
            print(f"❌ 批量测试失败: {e}")

def main():
    """主函数"""
    print("🚀 开始批量工作流测试...")
    
    test = BatchWorkflowTest()
    test.run_batch_test()
    
    print("\n🏁 批量测试完成!")

if __name__ == "__main__":
    main() 