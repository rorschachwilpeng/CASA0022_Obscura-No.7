#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端SHAP API测试脚本
测试部署在云端(Render/其他云平台)的SHAP API功能
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

class CloudSHAPTester:
    """云端SHAP API测试器"""
    
    def __init__(self, base_url):
        # 清理URL
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30  # 云端超时设置更长
        self.results = {}
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'SHAP-API-Tester/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_basic_connectivity(self):
        """测试基础连接"""
        print("\n🔍 测试 1: 基础连接检查")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code in [200, 404]:  # 404也表示连接正常
                print("   ✅ 云端服务可访问")
                self.results['connectivity'] = True
            else:
                print(f"   ⚠️ 云端响应异常: {response.status_code}")
                self.results['connectivity'] = False
                
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            self.results['connectivity'] = False
    
    def test_shap_health(self):
        """测试SHAP健康检查"""
        print("\n🔍 测试 2: SHAP服务健康检查")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/shap/health")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   服务状态: {data.get('data', {}).get('service_status', 'unknown')}")
                print(f"   可用城市: {data.get('data', {}).get('available_cities', [])}")
                self.results['shap_health'] = True
            elif response.status_code == 404:
                print("   ⚠️ SHAP API端点不存在 - 可能需要重新部署")
                self.results['shap_health'] = False
            else:
                print(f"   ❌ SHAP健康检查失败: {response.text[:200]}")
                self.results['shap_health'] = False
                
        except Exception as e:
            print(f"   ❌ SHAP健康检查异常: {e}")
            self.results['shap_health'] = False
    
    def test_legacy_ml_api(self):
        """测试原有的ML API (作为对比)"""
        print("\n🔍 测试 3: 原有ML API检查")
        try:
            payload = {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "month": 7,
                "future_years": 0
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/ml/predict",
                json=payload
            )
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 原有ML API正常工作")
                print(f"   预测温度: {data.get('prediction', {}).get('temperature', 'N/A'):.1f}°C")
                self.results['legacy_ml'] = True
            else:
                print(f"   ❌ 原有ML API失败: {response.text[:200]}")
                self.results['legacy_ml'] = False
                
        except Exception as e:
            print(f"   ❌ 原有ML API异常: {e}")
            self.results['legacy_ml'] = False
    
    def test_shap_predict(self):
        """测试SHAP预测API"""
        print("\n🔍 测试 4: SHAP预测API")
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
                print(f"   最终分数: {prediction_data.get('final_score', 0):.3f}")
                
                # 检查SHAP分析
                if 'shap_analysis' in prediction_data:
                    shap_data = prediction_data['shap_analysis']
                    if 'error' not in shap_data:
                        print(f"   ✅ SHAP分析成功")
                    else:
                        print(f"   ⚠️ SHAP分析错误: {shap_data.get('error')}")
                
                self.results['shap_predict'] = True
            elif response.status_code == 404:
                print("   ❌ SHAP预测端点不存在")
                self.results['shap_predict'] = False
            else:
                print(f"   ❌ SHAP预测失败: {response.text[:200]}")
                self.results['shap_predict'] = False
                
        except Exception as e:
            print(f"   ❌ SHAP预测异常: {e}")
            self.results['shap_predict'] = False
    
    def test_deployment_requirements(self):
        """检查部署要求"""
        print("\n🔍 测试 5: 部署要求检查")
        
        # 检查应用启动时间
        start_check = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/v1/ml/model/info", timeout=30)
            load_time = time.time() - start_check
            
            print(f"   模型加载时间: {load_time:.2f}秒")
            
            if load_time < 30:
                print("   ✅ 冷启动时间正常")
                self.results['cold_start'] = True
            else:
                print("   ⚠️ 冷启动时间过长")
                self.results['cold_start'] = False
                
        except Exception as e:
            print(f"   ❌ 启动检查失败: {e}")
            self.results['cold_start'] = False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🔍 测试 6: 云端错误处理")
        try:
            # 测试无效数据
            payload = {
                "latitude": 95.0,  # 无效纬度
                "longitude": -0.1278
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/shap/predict",
                json=payload
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 400:
                print("   ✅ 错误处理正常")
                self.results['error_handling'] = True
            elif response.status_code == 404:
                print("   ⚠️ SHAP端点未部署")
                self.results['error_handling'] = False
            else:
                print(f"   ⚠️ 错误处理异常: 期望400，得到{response.status_code}")
                self.results['error_handling'] = False
                
        except Exception as e:
            print(f"   ❌ 错误处理测试异常: {e}")
            self.results['error_handling'] = False
    
    def generate_deployment_report(self):
        """生成部署报告"""
        print("\n" + "=" * 60)
        print("📊 云端SHAP API部署报告")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        print(f"云端URL: {self.base_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests} ✅")
        print(f"失败测试: {total_tests - passed_tests} ❌")
        
        print("\n详细结果:")
        for test_name, result in self.results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        # 部署建议
        print("\n💡 部署建议:")
        
        if not self.results.get('connectivity', False):
            print("  ❌ 基础连接失败 - 检查URL是否正确")
        
        if not self.results.get('shap_health', False):
            print("  🚀 需要部署SHAP API:")
            print("     1. 确保api/routes/shap_predict.py已提交")
            print("     2. 确保requirements.txt包含shap==0.42.1")
            print("     3. 重新部署到云端平台")
        
        if self.results.get('legacy_ml', False) and not self.results.get('shap_predict', False):
            print("  🔄 原有ML API工作正常，SHAP API需要集成")
        
        if not self.results.get('cold_start', False):
            print("  ⚡ 优化冷启动时间:")
            print("     1. 减少模型文件大小")
            print("     2. 使用lazy loading")
        
        # 保存报告
        report = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': (passed_tests/total_tests)*100 if total_tests > 0 else 0
            }
        }
        
        report_file = f"cloud_shap_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        if self.results.get('shap_predict', False):
            print("🎉 SHAP API云端部署成功！")
            return True
        else:
            print("⚠️ SHAP API需要部署到云端")
            return False
    
    def run_cloud_tests(self):
        """运行云端测试"""
        print("🌩️ 开始云端SHAP API测试")
        print(f"测试目标: {self.base_url}")
        print("=" * 60)
        
        # 执行测试
        self.test_basic_connectivity()
        self.test_shap_health()
        self.test_legacy_ml_api()
        self.test_shap_predict()
        self.test_deployment_requirements()
        self.test_error_handling()
        
        # 生成报告
        return self.generate_deployment_report()

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_cloud_shap_api.py <your-cloud-url>")
        print("示例: python test_cloud_shap_api.py https://your-app.onrender.com")
        sys.exit(1)
    
    cloud_url = sys.argv[1]
    print(f"测试云端URL: {cloud_url}")
    
    tester = CloudSHAPTester(cloud_url)
    success = tester.run_cloud_tests()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 