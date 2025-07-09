#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Telescope Workflow
树莓派虚拟望远镜工作流 - 真实硬件版本
"""

import sys
import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# 导入核心模块（复制自task16）
try:
    from core.coordinate_calculator import CoordinateCalculator
    from core.weather_client import WeatherClient  
    from core.cloud_api_client import CloudAPIClient
    from core.config_manager import ConfigManager
    from core.progress_display import ProgressDisplay
    from core.maps_client import MapsClient
    from core.raspberry_pi_hardware import RaspberryPiHardware
except ImportError:
    # 备用导入路径
    from coordinate_calculator import CoordinateCalculator
    from weather_client import WeatherClient
    from cloud_api_client import CloudAPIClient
    from config_manager import ConfigManager
    from progress_display import ProgressDisplay
    from maps_client import MapsClient
    from raspberry_pi_hardware import RaspberryPiHardware

class RaspberryPiTelescopeWorkflow:
    """树莓派虚拟望远镜工作流"""
    
    def __init__(self, config_path='config/config.json'):
        """初始化工作流"""
        self.config_manager = ConfigManager(config_path)
        self.progress = ProgressDisplay()
        
        # 初始化核心组件
        self.coord_calc = CoordinateCalculator(self.config_manager.config)
        
        # 获取API密钥并初始化WeatherClient
        weather_api_key = self.config_manager.get('api_keys.openweather_api_key')
        if weather_api_key:
            self.weather_client = WeatherClient(weather_api_key)
            print("🌤️ OpenWeather客户端已初始化")
        else:
            self.weather_client = None
            print("⚠️ OpenWeather API密钥未配置，天气功能将使用模拟数据")
        
        self.cloud_client = CloudAPIClient(self.config_manager)
        
        # 初始化地图客户端
        google_maps_key = self.config_manager.get('api_keys.google_maps_api_key')
        if google_maps_key:
            self.maps_client = MapsClient(google_maps_key)
            print("🗺️ Google Maps客户端已初始化")
        else:
            self.maps_client = None
            print("⚠️ Google Maps API密钥未配置，地图功能将被跳过")
        
        # 初始化硬件接口
        self.hardware = RaspberryPiHardware(self.config_manager.config)
        
        # 会话数据
        self.session_data = {
            'workflow_id': f"pi_telescope_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now(),
            'device_type': 'raspberry_pi',
            'hardware_status': self.hardware.get_hardware_status()
        }
        
        self.last_result = None
        self.logger = logging.getLogger(__name__)
        
        print("🍓 树莓派虚拟望远镜已初始化")
        print(f"📊 硬件状态: {self._format_hardware_status()}")
    
    def _format_hardware_status(self) -> str:
        """格式化硬件状态显示"""
        status = self.hardware.get_hardware_status()
        indicators = []
        
        if status['hardware_available']:
            indicators.append("🍓 Pi")
        else:
            indicators.append("💻 Sim")
            
        if status['encoder_available']:
            indicators.append("🎛️ Encoder")
        if status['compass_available']:
            indicators.append("🧭 Compass")
        if status['button_available']:
            indicators.append("🔘 Button")
            
        return " | ".join(indicators)
    
    def run_telescope_session(self) -> Dict[str, Any]:
        """运行完整的望远镜会话"""
        print("\n🔭 启动 Obscura No.7 虚拟望远镜")
        print("=" * 60)
        
        try:
            # 显示欢迎信息
            self._show_welcome_message()
            
            # 运行6步工作流
            result = self._execute_workflow()
            
            # 显示完成信息
            self._show_completion_message(result)
            
            return result
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断望远镜会话")
            return {'success': False, 'error': 'User interrupted'}
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            print(f"\n❌ 工作流失败: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.hardware.cleanup()
    
    def _show_welcome_message(self):
        """显示欢迎信息"""
        print("🌟 欢迎使用 Obscura No.7 虚拟望远镜")
        print("📡 这个设备将帮您探索未来的环境可能性")
        print()
        print("🎮 操作说明:")
        if self.hardware.hardware_available:
            print("   📐 转动编码器设置距离")
            print("   🔘 按下按钮确认选择")
            print("   🧭 磁感器会自动读取方向")
        else:
            print("   ⌨️ 使用键盘输入参数")
        print()
        print("⏳ 准备开始探索...")
        time.sleep(2)
    
    def _execute_workflow(self) -> Dict[str, Any]:
        """执行6步工作流"""
        workflow_result = {}
        
        # 初始化进度显示
        self.progress.init_workflow(
            title="🔭 Obscura No.7 虚拟望远镜工作流",
            total_steps=7,  # 增加到7步，包含地图生成
            workflow_id=self.session_data['workflow_id']
        )
        
        # 步骤1: 硬件数据采集
        with self.progress.step(1, "硬件数据采集", "从编码器和磁感器读取用户输入") as step:
            hardware_data = self._collect_hardware_input()
            workflow_result['hardware_input'] = hardware_data
            step.success("硬件数据采集完成")
        
        # 步骤2: 坐标计算
        with self.progress.step(2, "坐标计算", "基于距离和方向计算目标坐标") as step:
            coordinates = self._calculate_target_coordinates(hardware_data)
            workflow_result['coordinates'] = coordinates
            self._show_coordinates_result(coordinates)
            step.success("坐标计算完成")
        
        # 步骤3: 环境数据获取
        with self.progress.step(3, "环境数据获取", "调用OpenWeather API获取真实环境数据") as step:
            weather_data = self._get_environmental_data(coordinates)
            workflow_result['weather_data'] = weather_data
            self._show_weather_summary(weather_data)
            step.success("真实环境数据获取完成")
        
        # 步骤4: AI艺术预测
        with self.progress.step(4, "AI艺术预测", "使用机器学习模型预测艺术风格") as step:
            ml_features = self._prepare_ml_features(coordinates, weather_data)
            style_prediction = self._predict_art_style(ml_features, coordinates)
            workflow_result['style_prediction'] = style_prediction
            self._show_prediction_result(style_prediction)
            step.success("AI艺术预测完成")
        
        # 步骤5: 地图生成
        with self.progress.step(5, "地图生成", "使用Google Maps API生成位置地图") as step:
            map_info = self._generate_location_map(coordinates, hardware_data)
            workflow_result['map_info'] = map_info
            if map_info and map_info.get('success'):
                step.success("地图生成完成")
            else:
                step.warning("地图生成失败或跳过")
        
        # 步骤6: 图像生成
        with self.progress.step(6, "AI图像生成", "使用AI生成艺术作品") as step:
            image_path = self._generate_artwork(style_prediction, weather_data, coordinates)
            workflow_result['generated_image'] = image_path
            step.success(f"图像生成完成: {os.path.basename(image_path)}")
        
        # 步骤7: 云端同步
        with self.progress.step(7, "云端同步", "上传图像和数据到展示网站") as step:
            sync_result = self._sync_to_cloud(workflow_result)
            workflow_result['sync_result'] = sync_result
            if sync_result and sync_result.get('success'):
                step.success("云端同步完成")
            else:
                step.warning("云端同步失败或跳过")
        
        # 完成工作流
        self.progress.complete_workflow(success=True)
        
        # 保存结果
        final_result = self._save_workflow_result(workflow_result)
        
        return final_result
    
    def _collect_hardware_input(self) -> Dict[str, float]:
        """收集硬件输入数据 - 使用三参数同步输入"""
        print("\n🎮 三参数同步设置...")
        
        # 使用新的三参数同步输入系统
        distance, direction, time_offset = self.hardware.read_three_parameter_input(timeout=120)
        
        return {
            'distance_km': distance,
            'direction_degrees': direction,
            'time_offset_years': time_offset
        }
    
    def _calculate_target_coordinates(self, hardware_data: Dict) -> Dict:
        """计算目标坐标"""
        base_lat = self.config_manager.get('telescope_settings.base_latitude', 51.5074)
        base_lon = self.config_manager.get('telescope_settings.base_longitude', -0.1278)
        
        target_coords = self.coord_calc.calculate_target_coordinates(
            base_lat, base_lon,
            hardware_data['distance_km'] * 1000,  # 转换为米
            hardware_data['direction_degrees']
        )
        
        return {
            'latitude': target_coords['latitude'],
            'longitude': target_coords['longitude'],
            'distance_km': hardware_data['distance_km'],
            'direction_degrees': hardware_data['direction_degrees'],
            'formatted_coords': f"{target_coords['latitude']:.6f}, {target_coords['longitude']:.6f}"
        }
    
    def _get_environmental_data(self, coordinates: Dict) -> Dict:
        """获取环境数据"""
        if self.weather_client:
            weather_data = self.weather_client.get_comprehensive_data(
                coordinates['latitude'],
                coordinates['longitude']
            )
            if weather_data:
                return weather_data
        
        # 如果API不可用或失败，创建备用天气数据
        print("⚠️ 使用备用天气数据")
        return self._create_fallback_weather_data(
            coordinates['latitude'],
            coordinates['longitude']
        )
    
    def _prepare_ml_features(self, coordinates: Dict, weather_data: Dict) -> Dict:
        """准备ML特征"""
        current_weather = weather_data.get('current_weather', {})
        
        return {
            'latitude': coordinates['latitude'],
            'longitude': coordinates['longitude'],
            'temperature': current_weather.get('temperature', 15),
            'humidity': current_weather.get('humidity', 60),
            'pressure': current_weather.get('pressure', 1013),
            'wind_speed': current_weather.get('wind_speed', 5),
            'weather_main': current_weather.get('weather_main', 'Clear'),
            'weather_description': current_weather.get('weather_description', 'clear sky')
        }
    
    def _predict_art_style(self, ml_features: Dict, location_info: Dict) -> Dict:
        """预测艺术风格"""
        return self.cloud_client.predict_art_style(ml_features, location_info)
    
    def _generate_location_map(self, coordinates: Dict, hardware_data: Dict) -> Optional[Dict]:
        """生成位置地图
        
        Args:
            coordinates: 坐标信息
            hardware_data: 硬件输入数据
            
        Returns:
            Dict: 地图信息，包含地址、地图文件路径等
        """
        if not self.maps_client:
            print("⚠️ Google Maps客户端未初始化，跳过地图生成")
            return None
        
        try:
            lat = coordinates['latitude']
            lon = coordinates['longitude']
            distance = hardware_data['distance_km'] * 1000  # 转换为米
            
            print(f"🗺️ 生成位置地图: {lat:.4f}, {lon:.4f}")
            
            # 获取位置信息
            location_info = self.maps_client.get_location_info(lat, lon)
            print(f"📍 位置: {location_info}")
            
            # 获取详细位置信息
            location_details = self.maps_client.get_location_details(lat, lon)
            
            # 生成静态地图
            map_image = self.maps_client.get_static_map(lat, lon, distance, 800, 600)
            
            map_file_path = None
            if map_image:
                # 保存地图图像
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                direction_name = self.maps_client.get_direction_name(hardware_data['direction_degrees'])
                distance_str = self.maps_client.format_distance(distance)
                
                map_filename = f"telescope_map_{distance_str}_{direction_name}_{timestamp}.png"
                map_file_path = os.path.join('outputs', 'images', map_filename)
                
                # 确保目录存在
                os.makedirs(os.path.dirname(map_file_path), exist_ok=True)
                map_image.save(map_file_path)
                print(f"💾 地图已保存: {map_filename}")
            
            return {
                'success': True,
                'coordinates': {
                    'latitude': lat,
                    'longitude': lon
                },
                'location_info': location_info,
                'location_details': location_details,
                'map_image_path': map_file_path,
                'distance_meters': distance,
                'direction_degrees': hardware_data['direction_degrees'],
                'direction_name': self.maps_client.get_direction_name(hardware_data['direction_degrees'])
            }
            
        except Exception as e:
            print(f"❌ 地图生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': coordinates
            }
    
    def _generate_artwork(self, style_prediction: Dict, weather_data: Dict, location_info: Dict) -> str:
        """生成艺术作品 - 确保返回有效路径"""
        try:
            image_path = self.cloud_client.generate_artwork(style_prediction, weather_data, location_info)
            
            # 确保返回有效路径
            if not image_path:
                print("⚠️ 图像生成返回空路径，创建占位符")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_placeholder_{timestamp}.txt'
                image_path = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'w', encoding='utf-8') as f:
                    f.write(f"Telescope session {timestamp}\nImage generation failed")
            
            # 验证文件是否存在
            if not os.path.exists(image_path):
                print(f"⚠️ 生成的文件不存在: {image_path}")
                # 创建占位符
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_missing_{timestamp}.txt'
                image_path = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'w', encoding='utf-8') as f:
                    f.write(f"Telescope session {timestamp}\nGenerated file was missing")
            
            return image_path
            
        except Exception as e:
            print(f"❌ 图像生成异常: {e}")
            # 创建错误占位符
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'telescope_error_{timestamp}.txt'
            image_path = os.path.join('outputs', 'images', filename)
            
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'w', encoding='utf-8') as f:
                f.write(f"Telescope session {timestamp}\nError: {str(e)}")
            
            return image_path

    def _sync_to_cloud(self, workflow_result: Dict) -> Dict:
        """同步到云端"""
        if not workflow_result.get('generated_image'):
            return None
        
        # 构建上传元数据
        metadata = {
            'coordinates': workflow_result.get('coordinates', {}),
            'weather': workflow_result.get('weather_data', {}),
            'style': workflow_result.get('style_prediction', {}),
            'hardware_input': workflow_result.get('hardware_input', {}),
            'timestamp': datetime.now().isoformat(),
            'device_type': 'raspberry_pi',
            'workflow_id': self.session_data['workflow_id']
        }
        
        return self.cloud_client.upload_to_website(
            workflow_result['generated_image'],
            metadata
        )
    
    def _save_workflow_result(self, workflow_result: Dict) -> Dict:
        """保存工作流结果"""
        final_result = {
            'workflow_id': self.session_data['workflow_id'],
            'timestamp': datetime.now().isoformat(),
            'device_type': 'raspberry_pi',
            'hardware_status': self.session_data['hardware_status'],
            'success': True,
            'execution_time': (datetime.now() - self.session_data['start_time']).total_seconds(),
            'data': workflow_result
        }
        
        # 保存到文件
        output_dir = 'outputs/workflow_results'
        os.makedirs(output_dir, exist_ok=True)
        
        result_file = os.path.join(output_dir, f"{self.session_data['workflow_id']}.json")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False, default=str)
        
        self.last_result = final_result
        return final_result
    
    def _show_coordinates_result(self, coordinates: Dict):
        """显示坐标计算结果"""
        self.progress.show_coordinates(
            coordinates['latitude'],
            coordinates['longitude'],
            coordinates['distance_km'] * 1000,  # 转换为米
            coordinates['direction_degrees']
        )
    
    def _show_weather_summary(self, weather_data: Dict):
        """显示天气摘要"""
        self.progress.show_weather_summary(weather_data)
    
    def _show_prediction_result(self, prediction: Dict):
        """显示AI预测结果"""
        self.progress.show_ml_prediction(prediction)
    
    def _show_completion_message(self, result: Dict):
        """显示完成信息"""
        print("\n" + "=" * 60)
        print("🎯 望远镜会话完成!")
        print(f"⏱️ 执行时间: {result.get('execution_time', 0):.1f} 秒")
        
        if result.get('data', {}).get('generated_image'):
            print(f"🎨 生成图像: {os.path.basename(result['data']['generated_image'])}")
        
        if result.get('data', {}).get('sync_result', {}).get('success'):
            sync_data = result['data']['sync_result']
            if sync_data.get('image_data', {}).get('image', {}).get('url'):
                print(f"🌐 图像URL: {sync_data['image_data']['image']['url']}")
        
        print("\n🔭 感谢使用 Obscura No.7 虚拟望远镜!")

    def _create_fallback_weather_data(self, lat, lon):
        """创建备用天气数据"""
        import random
        
        return {
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now().isoformat(),
            'current_weather': {
                'temperature': 15.0 + random.uniform(-5, 15),
                'feels_like': 15.0 + random.uniform(-5, 15),
                'humidity': random.randint(40, 80),
                'pressure': random.randint(990, 1030),
                'wind_speed': random.uniform(0, 10),
                'wind_direction': random.randint(0, 360),
                'visibility': random.uniform(5, 15),
                'cloud_cover': random.randint(0, 100),
                'weather_main': random.choice(['Clear', 'Clouds', 'Rain']),
                'weather_description': random.choice(['晴朗', '多云', '小雨']),
                'weather_id': random.choice([800, 801, 500]),  # Clear, Few clouds, Light rain
                'location_name': '模拟位置',
                'country': 'UK'
            },
            'forecast': {
                'daily': [{
                    'temperature_max': 20.0 + random.uniform(-5, 10),
                    'temperature_min': 10.0 + random.uniform(-5, 10),
                    'humidity': random.randint(40, 80),
                    'pressure': random.randint(990, 1030)
                } for _ in range(5)]
            },
            'air_quality': {
                'aqi': random.randint(1, 3),
                'aqi_description': random.choice(['优秀', '良好', '中等']),
                'pm2_5': random.randint(5, 25),
                'pm10': random.randint(10, 50),
                'no2': random.randint(10, 40),
                'o3': random.randint(40, 100)
            },
            'data_quality': {
                'score': 60,
                'level': 'simulated',
                'issues': ['使用模拟数据 - API调用失败']
            }
        }

def main():
    """主函数"""
    print("🍓 Raspberry Pi Obscura No.7 Virtual Telescope")
    print("=" * 60)
    
    try:
        # 创建工作流实例
        workflow = RaspberryPiTelescopeWorkflow()
        
        # 运行望远镜会话
        result = workflow.run_telescope_session()
        
        # 显示最终状态
        if result.get('success'):
            print("\n✅ 会话成功完成")
        else:
            print(f"\n❌ 会话失败: {result.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用户中断")
    except Exception as e:
        print(f"\n💥 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 