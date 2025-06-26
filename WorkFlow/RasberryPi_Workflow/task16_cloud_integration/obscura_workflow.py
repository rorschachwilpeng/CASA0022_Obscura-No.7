#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 完整工作流 - 笔记本版本
结合TASK1.5的经验，使用真实API进行完整的端到端流程
"""

import json
import time
import random
import math
from datetime import datetime, timedelta
from coordinate_calculator import CoordinateCalculator
from weather_client import WeatherClient
from cloud_api_client import CloudAPIClient
from progress_display import ProgressDisplay
from config_manager import ConfigManager

class ObscuraWorkflow:
    def __init__(self, config_path='config.json'):
        """初始化Obscura工作流"""
        print("🔭 初始化 Obscura No.7 虚拟望远镜...")
        
        # 加载配置
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # 初始化核心组件
        base_location = self.config.get('telescope_settings', {}).get('base_location', {})
        base_lat = base_location.get('latitude', 51.5074)
        base_lon = base_location.get('longitude', -0.1278)
        
        self.coordinate_calc = CoordinateCalculator((base_lat, base_lon))
        
        # 检查API密钥
        openweather_key = self.config.get('api_keys', {}).get('openweather_api_key')
        if not openweather_key or openweather_key == "YOUR_OPENWEATHER_API_KEY_HERE":
            print("⚠️ 警告：未配置OpenWeather API密钥，将使用模拟天气数据")
            self.weather_client = None
        else:
            self.weather_client = WeatherClient(openweather_key)
        
        self.cloud_client = CloudAPIClient(self.config)
        self.progress = ProgressDisplay()
        
        # 工作流状态
        self.last_result = None
        self.session_data = {
            'start_time': datetime.now(),
            'workflow_id': f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'results': []
        }
    
    def simulate_hardware_input(self) -> dict:
        """模拟硬件输入（笔记本版本）"""
        print("\n🎮 模拟硬件输入...")
        print("=" * 50)
        
        # 基于TASK1.5的模拟器逻辑
        distance_range = self.config.get('telescope_settings', {}).get('distance_range', {})
        min_km = distance_range.get('min_km', 1)
        max_km = distance_range.get('max_km', 50)
        
        # 随机生成或者允许用户输入
        use_random = input("使用随机参数? (y/n，默认y): ").strip().lower()
        
        if use_random != 'n':
            # 随机生成参数
            distance_km = random.uniform(min_km, max_km)
            direction_deg = random.uniform(0, 360)
            time_offset_years = random.uniform(0, 10)
            print(f"🎲 随机生成参数:")
        else:
            # 用户输入参数
            try:
                distance_km = float(input(f"距离 (km, {min_km}-{max_km}): ").strip())
                direction_deg = float(input("方向 (度, 0-360): ").strip())
                time_offset_years = float(input("时间偏移 (年, 0-50): ").strip())
                print(f"👤 用户输入参数:")
            except ValueError:
                print("❌ 输入无效，使用默认值")
                distance_km = 10.0
                direction_deg = 90.0
                time_offset_years = 5.0
        
        # 验证和限制参数
        distance_km = max(min_km, min(max_km, distance_km))
        direction_deg = direction_deg % 360
        time_offset_years = max(0, min(50, time_offset_years))
        
        hardware_data = {
            'distance_km': distance_km,
            'direction_degrees': direction_deg,
            'time_offset_years': time_offset_years,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"   📏 距离: {distance_km:.2f} km")
        print(f"   🧭 方向: {direction_deg:.1f}°")
        print(f"   ⏰ 时间偏移: {time_offset_years:.1f} 年")
        
        return hardware_data
    
    def run_complete_workflow(self) -> dict:
        """运行完整工作流"""
        workflow_steps = [
            "硬件数据采集",
            "坐标计算", 
            "环境数据获取",
            "AI艺术预测",
            "图像生成",
            "结果保存"
        ]
        
        self.progress.setup_workflow(workflow_steps)
        workflow_result = {}
        
        try:
            # 步骤1: 硬件数据采集
            with self.progress.start_step("硬件数据采集", "模拟从编码器和磁感器读取数据") as step:
                step.update("初始化硬件模拟器...")
                hardware_data = self.simulate_hardware_input()
                step.update(f"读取距离: {hardware_data['distance_km']:.2f}km")
                step.update(f"读取方向: {hardware_data['direction_degrees']:.1f}°")
                step.update(f"时间偏移: {hardware_data['time_offset_years']:.1f}年")
                step.success("硬件数据采集完成")
                workflow_result['hardware_input'] = hardware_data
            
            # 步骤2: 坐标计算
            with self.progress.start_step("坐标计算", "基于距离和方向计算目标坐标") as step:
                step.update("应用球面几何算法...")
                target_lat, target_lon = self.coordinate_calc.calculate_target_coordinates(
                    hardware_data['distance_km'] * 1000,  # 转换为米
                    hardware_data['direction_degrees']
                )
                
                coordinate_info = self.coordinate_calc.get_coordinate_info(target_lat, target_lon)
                
                self.progress.show_coordinates(
                    target_lat, target_lon, 
                    hardware_data['distance_km'] * 1000, 
                    hardware_data['direction_degrees']
                )
                step.success("坐标计算完成")
                workflow_result['coordinates'] = {
                    'latitude': target_lat,
                    'longitude': target_lon,
                    'info': coordinate_info
                }
            
            # 步骤3: 环境数据获取
            with self.progress.start_step("环境数据获取", "调用OpenWeather API获取真实环境数据") as step:
                if self.weather_client:
                    step.update("连接OpenWeather API...")
                    weather_data = self.weather_client.get_comprehensive_data(target_lat, target_lon)
                    
                    if weather_data:
                        self.progress.show_weather_summary(weather_data)
                        step.success("真实环境数据获取完成")
                    else:
                        step.warning("API获取失败，使用备用天气数据")
                        weather_data = self._create_fallback_weather_data(target_lat, target_lon)
                else:
                    step.update("使用模拟天气数据...")
                    weather_data = self._create_fallback_weather_data(target_lat, target_lon)
                    step.warning("使用模拟环境数据（未配置API密钥）")
                
                workflow_result['weather_data'] = weather_data
            
            # 步骤4: AI艺术预测
            with self.progress.start_step("AI艺术预测", "使用机器学习模型预测艺术风格") as step:
                step.update("准备环境特征数据...")
                
                # 格式化ML输入特征
                if weather_data and self.weather_client:
                    ml_features = self.weather_client.format_for_ml_model(weather_data)
                else:
                    ml_features = self._create_mock_ml_features(workflow_result)
                
                step.update("调用AI预测API...")
                style_prediction = self.cloud_client.predict_art_style(
                    ml_features, 
                    coordinate_info
                )
                
                self.progress.show_ml_prediction(style_prediction)
                step.success("AI艺术预测完成")
                workflow_result['style_prediction'] = style_prediction
            
            # 步骤5: 图像生成  
            with self.progress.start_step("图像生成", "使用AI生成艺术作品") as step:
                step.update("构建艺术提示词...")
                step.update("调用图像生成API...")
                
                # 显示进度条模拟
                for i in range(11):
                    self.progress.show_progress_bar(i, 10, "生成进度")
                    time.sleep(0.2)
                
                image_path = self.cloud_client.generate_artwork(
                    style_prediction,
                    weather_data,
                    coordinate_info
                )
                
                if image_path:
                    step.success(f"图像生成完成: {image_path}")
                    workflow_result['generated_image'] = image_path
                else:
                    step.error("图像生成失败")
                    workflow_result['generated_image'] = None
            
            # 步骤6: 结果保存
            with self.progress.start_step("结果保存", "保存工作流结果和元数据") as step:
                step.update("准备元数据...")
                
                # 保存完整结果
                final_result = {
                    'workflow_id': self.session_data['workflow_id'],
                    'timestamp': datetime.now().isoformat(),
                    'execution_time': (datetime.now() - self.session_data['start_time']).total_seconds(),
                    'success': True,
                    'data': workflow_result
                }
                
                # 保存到文件
                result_file = f"./workflow_outputs/workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import os
                os.makedirs('./workflow_outputs', exist_ok=True)
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(final_result, f, indent=2, ensure_ascii=False, default=str)
                
                step.update(f"结果已保存到: {result_file}")
                
                # 尝试上传到网站（如果配置了）
                if workflow_result.get('generated_image'):
                    step.update("尝试上传到展示网站...")
                    
                    # 构建适合API的上传元数据
                    upload_metadata = {
                        'coordinates': workflow_result.get('coordinates', {}),
                        'weather': workflow_result.get('weather_data', {}),
                        'style': workflow_result.get('style_prediction', {}),
                        'timestamp': workflow_result.get('timestamp'),
                        'workflow_id': final_result.get('workflow_id'),
                        'source': 'obscura_telescope_workflow'
                    }
                    
                    upload_result = self.cloud_client.upload_to_website(
                        workflow_result['generated_image'],
                        upload_metadata
                    )
                    if upload_result and upload_result.get('success'):
                        final_result['upload_result'] = upload_result
                        step.update("网站上传成功")
                    else:
                        step.warning("网站上传失败（这是正常的，如果本地没有运行网站）")
                
                step.success("工作流结果保存完成")
                self.last_result = final_result
            
            # 完成工作流
            self.progress.complete_workflow(success=True)
            return final_result
            
        except Exception as e:
            self.progress.show_error("工作流执行失败", str(e))
            self.progress.complete_workflow(success=False)
            
            error_result = {
                'workflow_id': self.session_data['workflow_id'],
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'partial_data': workflow_result
            }
            return error_result
    
    def run_batch_workflow(self, num_iterations=3):
        """运行批量工作流测试"""
        print(f"\n🚀 开始批量工作流测试 ({num_iterations} 次迭代)")
        print("=" * 60)
        
        batch_results = []
        
        for i in range(num_iterations):
            print(f"\n🔄 第 {i+1}/{num_iterations} 次迭代")
            print("-" * 40)
            
            result = self.run_complete_workflow()
            batch_results.append(result)
            
            if i < num_iterations - 1:
                print("\n⏱️ 等待3秒后开始下一次迭代...")
                time.sleep(3)
        
        # 批量结果统计
        successful = sum(1 for r in batch_results if r.get('success', False))
        print(f"\n📊 批量测试完成: {successful}/{num_iterations} 成功")
        
        return batch_results
    
    def _create_fallback_weather_data(self, lat, lon):
        """创建备用天气数据"""
        return {
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now().isoformat(),
            'current_weather': {
                'temperature': 15.0 + random.uniform(-5, 15),
                'humidity': random.randint(40, 80),
                'pressure': random.randint(990, 1030),
                'wind_speed': random.uniform(0, 10),
                'weather_main': random.choice(['Clear', 'Clouds', 'Rain']),
                'weather_description': random.choice(['晴朗', '多云', '小雨']),
                'visibility': 10
            },
            'air_quality': {
                'aqi': random.randint(1, 3),
                'aqi_description': random.choice(['优秀', '良好', '中等'])
            },
            'data_quality': {
                'score': 60,
                'level': 'simulated',
                'issues': ['使用模拟数据']
            }
        }
    
    def _create_mock_ml_features(self, workflow_data):
        """创建模拟ML特征"""
        coords = workflow_data.get('coordinates', {})
        weather = workflow_data.get('weather_data', {}).get('current_weather', {})
        
        return {
            'temperature': weather.get('temperature', 15),
            'humidity': weather.get('humidity', 60),
            'pressure': weather.get('pressure', 1013),
            'wind_speed': weather.get('wind_speed', 5),
            'latitude': coords.get('latitude', 51.5),
            'longitude': coords.get('longitude', -0.1),
            'weather_main': weather.get('weather_main', 'Clear'),
            'season': 'spring',
            'hour_of_day': datetime.now().hour
        }
    
    def show_session_summary(self):
        """显示会话总结"""
        if self.last_result:
            print("\n🎯 会话总结")
            print("=" * 50)
            print(f"🕐 开始时间: {self.session_data['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⚡ 执行时间: {self.last_result.get('execution_time', 0):.2f} 秒")
            print(f"✅ 成功状态: {'是' if self.last_result.get('success') else '否'}")
            
            if self.last_result.get('data', {}).get('generated_image'):
                print(f"🎨 生成图像: {self.last_result['data']['generated_image']}")
            
            if self.last_result.get('upload_result'):
                print(f"☁️ 网站上传: 成功")
        else:
            print("📝 当前会话无完成的工作流")

def main():
    """主函数 - 交互式菜单"""
    print("🔭 Obscura No.7 虚拟望远镜 - 笔记本版本")
    print("=" * 60)
    print("基于TASK1.5架构，集成真实API调用")
    print()
    
    # 初始化工作流
    try:
        workflow = ObscuraWorkflow()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    while True:
        print("\n🔧 选择操作:")
        print("1. 运行单次完整工作流")
        print("2. 运行批量测试工作流")
        print("3. 查看会话总结")
        print("4. 测试各个模块")
        print("5. 退出")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == '1':
            print("\n🚀 开始单次工作流...")
            result = workflow.run_complete_workflow()
            
        elif choice == '2':
            try:
                num = int(input("输入迭代次数 (默认3): ").strip() or "3")
                workflow.run_batch_workflow(num)
            except ValueError:
                print("❌ 无效输入，使用默认值")
                workflow.run_batch_workflow(3)
                
        elif choice == '3':
            workflow.show_session_summary()
            
        elif choice == '4':
            print("\n🧪 模块测试菜单:")
            print("1. 测试坐标计算")
            print("2. 测试天气API")
            print("3. 测试AI预测")
            print("4. 测试图像生成")
            
            test_choice = input("选择测试 (1-4): ").strip()
            
            if test_choice == '1':
                print("🧮 运行坐标计算测试...")
                import subprocess
                subprocess.run(['python', 'coordinate_calculator.py'])
            elif test_choice == '2':
                print("🌤️ 运行天气客户端测试...")
                import subprocess
                subprocess.run(['python', 'weather_client.py'])
            elif test_choice == '3':
                print("🤖 运行云端API测试...")
                import subprocess
                subprocess.run(['python', 'cloud_api_client.py'])
            elif test_choice == '4':
                print("🎨 运行进度显示测试...")
                import subprocess
                subprocess.run(['python', 'progress_display.py'])
                
        elif choice == '5':
            print("\n👋 感谢使用 Obscura No.7!")
            workflow.show_session_summary()
            break
            
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()
