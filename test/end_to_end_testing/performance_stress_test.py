#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 性能和压力测试套件
测试系统在各种条件下的性能表现和稳定性
"""

import requests
import json
import time
import threading
import concurrent.futures
import random
import statistics
from datetime import datetime
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self, base_url: str = "https://casa0022-obscura-no-7.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Obscura-Performance-Test/1.0'
        })
        
        # 测试结果存储
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
        
    def create_test_payload(self, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """创建测试负载数据"""
        if lat is None:
            lat = random.uniform(-85, 85)  # 有效纬度范围
        if lon is None:
            lon = random.uniform(-180, 180)  # 有效经度范围
            
        return {
            "environmental_data": {
                "latitude": lat,
                "longitude": lon,
                "temperature": round(random.uniform(-20.0, 45.0), 1),
                "humidity": random.randint(10, 100),
                "pressure": random.randint(950, 1050),
                "wind_speed": round(random.uniform(0.0, 25.0), 1),
                "weather_description": random.choice([
                    "clear sky", "few clouds", "scattered clouds", 
                    "overcast clouds", "light rain", "moderate rain",
                    "heavy rain", "snow", "fog", "thunderstorm"
                ]),
                "location_name": f"Test Location {random.randint(1, 1000)}"
            },
            "hours_ahead": random.choice([6, 12, 24, 48, 72, 96, 120, 168])
        }
    
    def single_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行单次API请求"""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/ml/predict",
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.success_count += 1
                self.response_times.append(response_time)
                return {
                    "success": True,
                    "response_time": response_time,
                    "prediction": result.get("prediction", {}),
                    "status_code": response.status_code
                }
            else:
                self.error_count += 1
                return {
                    "success": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            self.error_count += 1
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e),
                "status_code": 0
            }
    
    def response_time_benchmark(self, num_requests: int = 20) -> Dict[str, Any]:
        """API响应时间基准测试"""
        logger.info(f"🏃 开始响应时间基准测试 - {num_requests}次请求")
        
        # 重置计数器
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        
        results = []
        start_time = time.time()
        
        for i in range(num_requests):
            payload = self.create_test_payload()
            result = self.single_api_request(payload)
            results.append(result)
            
            if (i + 1) % 5 == 0:
                logger.info(f"   完成 {i + 1}/{num_requests} 请求")
            
            # 请求间短暂间隔
            time.sleep(0.2)
        
        total_time = time.time() - start_time
        
        # 计算统计数据
        if self.response_times:
            avg_response_time = statistics.mean(self.response_times)
            median_response_time = statistics.median(self.response_times)
            min_response_time = min(self.response_times)
            max_response_time = max(self.response_times)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
        
        success_rate = (self.success_count / num_requests) * 100
        
        benchmark_result = {
            "test_type": "response_time_benchmark",
            "total_requests": num_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": f"{success_rate:.1f}%",
            "total_test_time": f"{total_time:.2f}s",
            "requests_per_second": f"{num_requests / total_time:.2f}",
            "response_time_stats": {
                "average": f"{avg_response_time:.3f}s",
                "median": f"{median_response_time:.3f}s",
                "min": f"{min_response_time:.3f}s",
                "max": f"{max_response_time:.3f}s"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ 基准测试完成 - 成功率: {success_rate:.1f}%, 平均响应: {avg_response_time:.3f}s")
        
        return benchmark_result
    
    def concurrent_load_test(self, num_concurrent: int = 5, requests_per_thread: int = 3) -> Dict[str, Any]:
        """并发负载测试"""
        logger.info(f"🔄 开始并发负载测试 - {num_concurrent}并发线程, 每线程{requests_per_thread}请求")
        
        def worker_thread(thread_id: int) -> List[Dict[str, Any]]:
            """工作线程函数"""
            thread_results = []
            for i in range(requests_per_thread):
                payload = self.create_test_payload()
                result = self.single_api_request(payload)
                result["thread_id"] = thread_id
                result["request_id"] = i
                thread_results.append(result)
                time.sleep(0.5)  # 线程内请求间隔
            return thread_results
        
        start_time = time.time()
        all_results = []
        
        # 使用线程池执行并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            future_to_thread = {executor.submit(worker_thread, i): i for i in range(num_concurrent)}
            
            for future in concurrent.futures.as_completed(future_to_thread):
                thread_id = future_to_thread[future]
                try:
                    thread_results = future.result()
                    all_results.extend(thread_results)
                    logger.info(f"   线程 {thread_id} 完成")
                except Exception as e:
                    logger.error(f"   线程 {thread_id} 异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = num_concurrent * requests_per_thread
        
        # 分析结果
        successful_results = [r for r in all_results if r["success"]]
        failed_results = [r for r in all_results if not r["success"]]
        
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        success_rate = (len(successful_results) / total_requests) * 100
        
        concurrent_result = {
            "test_type": "concurrent_load_test",
            "concurrent_threads": num_concurrent,
            "requests_per_thread": requests_per_thread,
            "total_requests": total_requests,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": f"{success_rate:.1f}%",
            "total_test_time": f"{total_time:.2f}s",
            "requests_per_second": f"{total_requests / total_time:.2f}",
            "concurrent_response_time": {
                "average": f"{avg_response_time:.3f}s",
                "min": f"{min_response_time:.3f}s",
                "max": f"{max_response_time:.3f}s"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ 并发测试完成 - 成功率: {success_rate:.1f}%, 平均响应: {avg_response_time:.3f}s")
        
        return concurrent_result
    
    def boundary_condition_test(self) -> Dict[str, Any]:
        """边界条件测试"""
        logger.info("🔍 开始边界条件测试")
        
        boundary_tests = [
            # 极端坐标
            {"name": "北极点", "lat": 89, "lon": 0},
            {"name": "南极点", "lat": -89, "lon": 0},
            {"name": "国际日期变更线", "lat": 0, "lon": 180},
            {"name": "本初子午线", "lat": 0, "lon": 0},
            {"name": "极端西经", "lat": 0, "lon": -180},
        ]
        
        results = []
        
        for test_case in boundary_tests:
            logger.info(f"   测试 {test_case['name']}: ({test_case['lat']}, {test_case['lon']})")
            
            payload = self.create_test_payload(test_case["lat"], test_case["lon"])
            result = self.single_api_request(payload)
            
            result["test_case"] = test_case["name"]
            result["coordinates"] = (test_case["lat"], test_case["lon"])
            results.append(result)
            
            time.sleep(1)  # 间隔请求
        
        successful_boundary_tests = sum(1 for r in results if r["success"])
        boundary_success_rate = (successful_boundary_tests / len(boundary_tests)) * 100
        
        boundary_result = {
            "test_type": "boundary_condition_test",
            "total_boundary_tests": len(boundary_tests),
            "successful_tests": successful_boundary_tests,
            "failed_tests": len(boundary_tests) - successful_boundary_tests,
            "boundary_success_rate": f"{boundary_success_rate:.1f}%",
            "test_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ 边界条件测试完成 - 成功率: {boundary_success_rate:.1f}%")
        
        return boundary_result
    
    def run_performance_test(self) -> Dict[str, Any]:
        """运行性能测试"""
        logger.info("🚀 开始Obscura No.7性能测试")
        suite_start_time = time.time()
        
        # 执行各项测试
        benchmark_result = self.response_time_benchmark(20)
        time.sleep(2)  # 测试间隔
        
        concurrent_result = self.concurrent_load_test(5, 3)
        time.sleep(2)  # 测试间隔
        
        boundary_result = self.boundary_condition_test()
        
        suite_total_time = time.time() - suite_start_time
        
        # 生成综合报告
        performance_report = {
            "test_suite": "Obscura No.7 Performance Test",
            "test_timestamp": datetime.now().isoformat(),
            "total_suite_time": f"{suite_total_time:.2f}s",
            "test_results": {
                "response_time_benchmark": benchmark_result,
                "concurrent_load_test": concurrent_result,
                "boundary_condition_test": boundary_result
            }
        }
        
        # 保存报告
        self.save_performance_report(performance_report)
        
        # 打印摘要
        self.print_performance_summary(performance_report)
        
        return performance_report
    
    def save_performance_report(self, report: Dict[str, Any]):
        """保存性能测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_test_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 性能测试报告已保存: {filename}")
        except Exception as e:
            logger.error(f"❌ 保存性能报告失败: {e}")
    
    def print_performance_summary(self, report: Dict[str, Any]):
        """打印性能测试摘要"""
        print("\n" + "="*80)
        print("🔭 OBSCURA NO.7 性能测试摘要")
        print("="*80)
        print(f"⏱️  总测试时间: {report['total_suite_time']}")
        print("")
        
        # 详细结果
        results = report["test_results"]
        
        print("📈 测试结果详情:")
        print(f"  响应时间基准: {results['response_time_benchmark']['success_rate']} 成功")
        print(f"    - 平均响应: {results['response_time_benchmark']['response_time_stats']['average']}")
        print(f"    - 最快响应: {results['response_time_benchmark']['response_time_stats']['min']}")
        print(f"    - 最慢响应: {results['response_time_benchmark']['response_time_stats']['max']}")
        
        print(f"  并发负载测试: {results['concurrent_load_test']['success_rate']} 成功")
        print(f"    - 并发线程: {results['concurrent_load_test']['concurrent_threads']}")
        print(f"    - 请求/秒: {results['concurrent_load_test']['requests_per_second']}")
        
        print(f"  边界条件测试: {results['boundary_condition_test']['boundary_success_rate']} 成功")
        
        print("="*80)

def main():
    """主函数"""
    print("🔭 Obscura No.7 性能和压力测试套件")
    print("测试系统性能表现和稳定性\n")
    
    # 创建性能测试套件
    performance_test = PerformanceTestSuite()
    
    # 运行性能测试
    report = performance_test.run_performance_test()
    
    print("🎉 性能测试完成！")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 