#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 端到端测试套件
模拟完整的树莓派工作流程：用户交互 → 坐标计算 → API调用 → 网站验证
"""

import requests
import json
import time
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('e2e_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RaspberryPiSimulator:
    """树莓派用户交互模拟器"""
    
    def __init__(self):
        # 模拟硬件初始状态
        self.encoder_position = 0  # 编码器位置 (距离)
        self.magnetometer_heading = 0  # 磁感器方向 (角度)
        self.base_latitude = 51.5074  # 伦敦基准位置
        self.base_longitude = -0.1278
        
    def simulate_user_interaction(self) -> Dict[str, float]:
        """模拟用户与硬件的交互"""
        # 模拟编码器旋转 (距离调整)
        distance_change = random.uniform(-5.0, 5.0)  # km
        self.encoder_position += distance_change
        
        # 模拟磁感器方向调整
        heading_change = random.uniform(-30.0, 30.0)  # 度
        self.magnetometer_heading = (self.magnetometer_heading + heading_change) % 360
        
        # 限制距离范围 (0-50km)
        distance = max(0.1, min(50.0, abs(self.encoder_position)))
        
        logger.info(f"🎮 用户交互模拟 - 距离: {distance:.2f}km, 方向: {self.magnetometer_heading:.1f}°")
        
        return {
            "distance_km": distance,
            "heading_degrees": self.magnetometer_heading,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_target_coordinates(self, user_input: Dict[str, float]) -> Tuple[float, float]:
        """根据用户输入计算目标坐标"""
        distance_km = user_input["distance_km"]
        heading_deg = user_input["heading_degrees"]
        
        # 将方向角转换为弧度
        heading_rad = math.radians(heading_deg)
        
        # 地球半径 (km)
        earth_radius = 6371.0
        
        # 基准位置转换为弧度
        base_lat_rad = math.radians(self.base_latitude)
        base_lon_rad = math.radians(self.base_longitude)
        
        # 计算目标坐标
        # 纬度变化
        delta_lat = distance_km * math.cos(heading_rad) / earth_radius
        target_lat = base_lat_rad + delta_lat
        
        # 经度变化 (考虑纬度的余弦值)
        delta_lon = distance_km * math.sin(heading_rad) / (earth_radius * math.cos(base_lat_rad))
        target_lon = base_lon_rad + delta_lon
        
        # 转换回度数
        target_latitude = math.degrees(target_lat)
        target_longitude = math.degrees(target_lon)
        
        logger.info(f"📍 坐标计算 - 目标位置: ({target_latitude:.4f}, {target_longitude:.4f})")
        
        return target_latitude, target_longitude

class APITestClient:
    """API测试客户端"""
    
    def __init__(self, base_url: str = "https://casa0022-obscura-no-7.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Obscura-E2E-Test/1.0'
        })
    
    def test_ml_prediction(self, latitude: float, longitude: float, location_name: str = "Test Location") -> Dict[str, Any]:
        """测试ML预测API"""
        url = f"{self.base_url}/api/v1/ml/predict"
        
        # 模拟环境数据
        payload = {
            "environmental_data": {
                "latitude": latitude,
                "longitude": longitude,
                "temperature": round(random.uniform(10.0, 30.0), 1),
                "humidity": random.randint(30, 90),
                "pressure": random.randint(980, 1030),
                "wind_speed": round(random.uniform(0.0, 15.0), 1),
                "weather_description": random.choice([
                    "clear sky", "few clouds", "scattered clouds", 
                    "overcast clouds", "light rain", "moderate rain"
                ]),
                "location_name": location_name
            },
            "hours_ahead": random.choice([24, 48, 72])
        }
        
        try:
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                result['_meta'] = {
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'request_payload': payload
                }
                logger.info(f"✅ ML预测成功 - {location_name}, 响应时间: {response_time:.3f}s")
                return result
            else:
                logger.error(f"❌ ML预测失败 - 状态码: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ ML预测异常: {e}")
            return {"success": False, "error": str(e)}
    
    def test_image_list(self) -> Dict[str, Any]:
        """测试图片列表API"""
        url = f"{self.base_url}/api/v1/images"
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 图片列表获取成功 - 共{result.get('count', 0)}张图片")
                return result
            else:
                logger.error(f"❌ 图片列表获取失败 - 状态码: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ 图片列表异常: {e}")
            return {"success": False, "error": str(e)}
    
    def test_gallery_page(self) -> bool:
        """测试Gallery页面可访问性"""
        url = f"{self.base_url}/gallery"
        
        try:
            response = self.session.get(url, timeout=15)
            success = response.status_code == 200
            if success:
                logger.info("✅ Gallery页面访问成功")
            else:
                logger.error(f"❌ Gallery页面访问失败 - 状态码: {response.status_code}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Gallery页面异常: {e}")
            return False

class EndToEndTestSuite:
    """端到端测试套件"""
    
    def __init__(self):
        self.raspberry_pi = RaspberryPiSimulator()
        self.api_client = APITestClient()
        self.test_results = []
        
        # 测试地点配置
        self.test_locations = [
            {"name": "伦敦市中心", "base_lat": 51.5074, "base_lon": -0.1278},
            {"name": "北京天安门", "base_lat": 39.9042, "base_lon": 116.4074},
            {"name": "纽约时代广场", "base_lat": 40.7589, "base_lon": -73.9851},
            {"name": "巴黎埃菲尔铁塔", "base_lat": 48.8584, "base_lon": 2.2945},
            {"name": "东京银座", "base_lat": 35.6762, "base_lon": 139.7653}
        ]
    
    def run_single_workflow_test(self, location_config: Dict[str, Any]) -> Dict[str, Any]:
        """运行单次完整工作流测试"""
        test_start_time = time.time()
        location_name = location_config["name"]
        
        logger.info(f"🚀 开始测试: {location_name}")
        
        # 更新基准位置
        self.raspberry_pi.base_latitude = location_config["base_lat"]
        self.raspberry_pi.base_longitude = location_config["base_lon"]
        
        # 步骤1: 模拟用户交互
        user_input = self.raspberry_pi.simulate_user_interaction()
        
        # 步骤2: 计算目标坐标
        target_lat, target_lon = self.raspberry_pi.calculate_target_coordinates(user_input)
        
        # 步骤3: ML预测API调用
        prediction_result = self.api_client.test_ml_prediction(
            target_lat, target_lon, location_name
        )
        
        # 步骤4: 验证网站功能
        gallery_accessible = self.api_client.test_gallery_page()
        image_list = self.api_client.test_image_list()
        
        # 计算总耗时
        total_time = time.time() - test_start_time
        
        # 构建测试结果
        test_result = {
            "location": location_name,
            "user_input": user_input,
            "target_coordinates": {
                "latitude": target_lat,
                "longitude": target_lon
            },
            "prediction_result": prediction_result,
            "gallery_accessible": gallery_accessible,
            "image_count": image_list.get("count", 0) if image_list.get("success") else 0,
            "total_time": total_time,
            "timestamp": datetime.now().isoformat(),
            "success": all([
                prediction_result.get("success", False),
                gallery_accessible,
                image_list.get("success", False)
            ])
        }
        
        self.test_results.append(test_result)
        
        if test_result["success"]:
            logger.info(f"✅ {location_name} 测试完成 - 耗时: {total_time:.2f}s")
        else:
            logger.error(f"❌ {location_name} 测试失败")
        
        return test_result
    
    def run_comprehensive_test(self, num_tests_per_location: int = 2) -> Dict[str, Any]:
        """运行综合测试"""
        logger.info("🔭 开始Obscura No.7端到端综合测试")
        suite_start_time = time.time()
        
        all_results = []
        
        for location in self.test_locations:
            logger.info(f"📍 测试地点: {location['name']}")
            
            for test_round in range(num_tests_per_location):
                logger.info(f"   第 {test_round + 1}/{num_tests_per_location} 轮测试")
                result = self.run_single_workflow_test(location)
                all_results.append(result)
                
                # 测试间隔
                if test_round < num_tests_per_location - 1:
                    time.sleep(2)
            
            # 地点间隔
            time.sleep(1)
        
        # 计算统计数据
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        avg_response_time = sum(
            r["prediction_result"].get("_meta", {}).get("response_time", 0) 
            for r in all_results if r["prediction_result"].get("_meta")
        ) / len([r for r in all_results if r["prediction_result"].get("_meta")])
        
        suite_total_time = time.time() - suite_start_time
        
        # 生成测试报告
        test_report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": f"{success_rate:.1f}%",
                "average_api_response_time": f"{avg_response_time:.3f}s",
                "total_suite_time": f"{suite_total_time:.2f}s"
            },
            "test_results": all_results,
            "locations_tested": [loc["name"] for loc in self.test_locations],
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存测试报告
        self.save_test_report(test_report)
        
        # 打印摘要
        self.print_test_summary(test_report)
        
        return test_report
    
    def save_test_report(self, report: Dict[str, Any]):
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"e2e_test_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 测试报告已保存: {filename}")
        except Exception as e:
            logger.error(f"❌ 保存测试报告失败: {e}")
    
    def print_test_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        summary = report["test_summary"]
        
        print("\n" + "="*80)
        print("🔭 OBSCURA NO.7 端到端测试摘要")
        print("="*80)
        print(f"📊 测试统计:")
        print(f"   总测试数: {summary['total_tests']}")
        print(f"   成功测试: {summary['successful_tests']}")
        print(f"   失败测试: {summary['failed_tests']}")
        print(f"   成功率: {summary['success_rate']}")
        print(f"")
        print(f"⚡ 性能数据:")
        print(f"   平均API响应时间: {summary['average_api_response_time']}")
        print(f"   总测试时间: {summary['total_suite_time']}")
        print(f"")
        print(f"🌍 测试地点: {', '.join(report['locations_tested'])}")
        print("="*80)

def main():
    """主函数"""
    print("🔭 Obscura No.7 端到端测试套件")
    print("模拟完整的树莓派工作流程\n")
    
    # 创建测试套件
    test_suite = EndToEndTestSuite()
    
    # 运行综合测试
    report = test_suite.run_comprehensive_test(num_tests_per_location=3)
    
    # 检查测试结果
    if report["test_summary"]["success_rate"] == "100.0%":
        print("🎉 所有测试通过！系统准备就绪。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查日志和报告。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 