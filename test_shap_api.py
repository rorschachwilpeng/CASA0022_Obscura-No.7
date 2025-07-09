#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHAP API集成测试
测试SHAP环境预测API的完整功能
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# 测试配置
BASE_URL = "http://localhost:5000"  # 本地测试
# BASE_URL = "https://your-app.onrender.com"  # 云端测试

class SHAPAPITester:
    """SHAP API测试器"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def test_health_check(self):
        """测试健康检查"""
        print("\n🔍 测试 1: SHAP服务健康检查")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/shap/health")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   服务状态: {data.get('data', {}).get('service_status', 'unknown')}")
                print(f"   可用城市: {data.get('data', {}).get('available_cities', [])}")
                self.results['health_check'] = True
            else:
                print(f"   ❌ 健康检查失败: {response.text}")
                self.results['health_check'] = False
                
        except Exception as e:
            print(f"   ❌ 健康检查异常: {e}")
            self.results['health_check'] = False
    
    def test_model_status(self):
        """测试模型状态"""
        print("\n🔍 测试 2: SHAP模型状态")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/shap/model/status")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                status_data = data.get('data', {})
                print(f"   清单加载: {'✅' if status_data.get('manifest_loaded') else '❌'}")
                print(f"   已加载城市: {status_data.get('loaded_cities', [])}")
                print(f"   部署版本: {status_data.get('deployment_version', 'unknown')}")
                self.results['model_status'] = True
            else:
                print(f"   ❌ 模型状态获取失败: {response.text}")
                self.results['model_status'] = False
                
        except Exception as e:
            print(f"   ❌ 模型状态异常: {e}")
            self.results['model_status'] = False
    
    def test_predict_london(self):
        """测试伦敦预测"""
        print("\n🔍 测试 3: 伦敦SHAP预测")
        try:
            payload = {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "month": 7,
                "analyze_shap": True
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/predict",
                json=payload
            )
            response_time = time.time() - start_time
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {response_time:.2f}秒")
            
            if response.status_code == 200:
                data = response.json()
                prediction_data = data.get('data', {})
                
                print(f"   城市: {prediction_data.get('city', 'Unknown')}")
                print(f"   气候分数: {prediction_data.get('climate_score', 0):.3f}")
                print(f"   地理分数: {prediction_data.get('geographic_score', 0):.3f}")
                print(f"   经济分数: {prediction_data.get('economic_score', 0):.3f}")
                print(f"   最终分数: {prediction_data.get('final_score', 0):.3f}")
                print(f"   置信度: {prediction_data.get('overall_confidence', 0):.3f}")
                
                # SHAP分析
                if 'shap_analysis' in prediction_data:
                    shap_data = prediction_data['shap_analysis']
                    if 'error' not in shap_data:
                        print(f"   ✅ SHAP分析成功")
                        print(f"   基准值: {shap_data.get('base_value', 0):.3f}")
                        print(f"   预测值: {shap_data.get('prediction_value', 0):.3f}")
                    else:
                        print(f"   ⚠️ SHAP分析错误: {shap_data.get('error')}")
                
                self.results['predict_london'] = True
            else:
                print(f"   ❌ 伦敦预测失败: {response.text}")
                self.results['predict_london'] = False
                
        except Exception as e:
            print(f"   ❌ 伦敦预测异常: {e}")
            self.results['predict_london'] = False
    
    def test_predict_manchester(self):
        """测试曼彻斯特预测"""
        print("\n🔍 测试 4: 曼彻斯特SHAP预测")
        try:
            payload = {
                "latitude": 53.4808,
                "longitude": -2.2426,
                "month": 8,
                "analyze_shap": False  # 测试不进行SHAP分析
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/predict",
                json=payload
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                prediction_data = data.get('data', {})
                
                print(f"   城市: {prediction_data.get('city', 'Unknown')}")
                print(f"   最终分数: {prediction_data.get('final_score', 0):.3f}")
                print(f"   ✅ 无SHAP分析模式正常")
                
                self.results['predict_manchester'] = True
            else:
                print(f"   ❌ 曼彻斯特预测失败: {response.text}")
                self.results['predict_manchester'] = False
                
        except Exception as e:
            print(f"   ❌ 曼彻斯特预测异常: {e}")
            self.results['predict_manchester'] = False
    
    def test_batch_compare(self):
        """测试批量对比"""
        print("\n🔍 测试 5: 多城市对比")
        try:
            payload = {
                "locations": [
                    {"latitude": 51.5074, "longitude": -0.1278, "name": "London"},
                    {"latitude": 53.4808, "longitude": -2.2426, "name": "Manchester"},
                    {"latitude": 55.9533, "longitude": -3.1883, "name": "Edinburgh"}
                ],
                "month": 6,
                "comparison_type": "scores"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/compare",
                json=payload
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                compare_data = data.get('data', {})
                
                print(f"   对比位置数: {compare_data.get('locations_count', 0)}")
                
                summary = compare_data.get('comparison_summary', {})
                if summary:
                    stats = summary.get('score_statistics', {}).get('final_score', {})
                    print(f"   分数范围: {stats.get('min', 0):.3f} - {stats.get('max', 0):.3f}")
                    print(f"   平均分数: {stats.get('mean', 0):.3f}")
                
                self.results['batch_compare'] = True
            else:
                print(f"   ❌ 批量对比失败: {response.text}")
                self.results['batch_compare'] = False
                
        except Exception as e:
            print(f"   ❌ 批量对比异常: {e}")
            self.results['batch_compare'] = False
    
    def test_visualization_data(self):
        """测试可视化数据"""
        print("\n🔍 测试 6: 可视化数据生成")
        try:
            payload = {
                "latitude": 55.9533,
                "longitude": -3.1883,
                "month": 5,
                "visualization_type": "bubble"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/visualize",
                json=payload
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                viz_data = data.get('data', {})
                
                print(f"   可视化类型: {viz_data.get('type', 'unknown')}")
                
                if viz_data.get('type') == 'bubble':
                    bubble_data = viz_data.get('data', {})
                    scores = bubble_data.get('scores', [])
                    print(f"   分数数据点: {len(scores)}个")
                    print(f"   城市: {bubble_data.get('city', 'Unknown')}")
                
                self.results['visualization_data'] = True
            else:
                print(f"   ❌ 可视化数据生成失败: {response.text}")
                self.results['visualization_data'] = False
                
        except Exception as e:
            print(f"   ❌ 可视化数据异常: {e}")
            self.results['visualization_data'] = False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🔍 测试 7: 错误处理")
        try:
            # 测试无效坐标
            payload = {
                "latitude": 95.0,  # 无效纬度
                "longitude": -0.1278,
                "month": 7
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/predict",
                json=payload
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 400:
                print("   ✅ 无效坐标正确拒绝")
                self.results['error_handling'] = True
            else:
                print(f"   ❌ 错误处理异常: 期望400，得到{response.status_code}")
                self.results['error_handling'] = False
                
        except Exception as e:
            print(f"   ❌ 错误处理测试异常: {e}")
            self.results['error_handling'] = False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始SHAP API集成测试")
        print(f"测试目标: {self.base_url}")
        print("=" * 50)
        
        # 执行所有测试
        self.test_health_check()
        self.test_model_status()
        self.test_predict_london()
        self.test_predict_manchester()
        self.test_batch_compare()
        self.test_visualization_data()
        self.test_error_handling()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 SHAP API测试报告")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests} ✅")
        print(f"失败测试: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        # 保存报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'detailed_results': self.results
        }
        
        report_file = f"shap_api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        if failed_tests == 0:
            print("🎉 所有测试通过！SHAP API集成成功！")
            return True
        else:
            print("⚠️ 部分测试失败，请检查错误信息")
            return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        print(f"使用自定义URL: {base_url}")
    else:
        base_url = BASE_URL
        print(f"使用默认URL: {base_url}")
    
    tester = SHAPAPITester(base_url)
    success = tester.run_all_tests()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 