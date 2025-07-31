#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps API客户端模块
提供地理编码、静态地图、Places API等功能
从simple_workflow.py中提取的功能，并增强了建筑信息获取功能
"""

import requests
import math
import time
from PIL import Image
import io
from typing import Optional, Tuple, Dict, List

class MapsClient:
    """Google Maps API客户端 - 增强版，支持建筑信息获取"""
    
    def __init__(self, api_key: str):
        """初始化地图客户端
        
        Args:
            api_key: Google Maps API密钥
        """
        self.api_key = api_key
        self.base_geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.base_staticmap_url = "https://maps.googleapis.com/maps/api/staticmap"
        self.base_places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
    def get_location_info(self, lat: float, lon: float) -> str:
        """获取位置信息（逆地理编码）
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            str: 格式化的地址信息
        """
        try:
            params = {
                'latlng': f"{lat},{lon}",
                'key': self.api_key,
                'language': 'en'  # 改为英文，便于AI理解
            }
            
            response = requests.get(self.base_geocoding_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and data['results']:
                    # 获取最详细的地址
                    formatted_address = data['results'][0]['formatted_address']
                    return formatted_address
                else:
                    print(f"⚠️ 地理编码API返回: {data.get('status', 'Unknown')}")
            else:
                print(f"⚠️ 地理编码请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ 获取位置信息失败: {e}")
        
        return f"位置: {lat:.4f}, {lon:.4f}"

    def get_nearby_buildings(self, lat: float, lon: float, radius: int = 1000) -> Dict[str, List[str]]:
        """获取附近的建筑和地标信息 - 新增功能
        
        Args:
            lat: 纬度
            lon: 经度
            radius: 搜索半径（米）
            
        Returns:
            Dict: 分类的建筑信息 {
                'landmarks': ['Big Ben', 'Tower Bridge'],
                'cultural': ['British Museum'],
                'natural': ['Hyde Park'],
                'commercial': ['Oxford Street']
            }
        """
        print(f"🏛️ 获取附近建筑信息: 半径 {radius}m")
        
        # 定义地点类型分类
        place_categories = {
            'landmarks': ['tourist_attraction', 'establishment'],
            'cultural': ['museum', 'art_gallery', 'library', 'university'],
            'natural': ['park', 'natural_feature'],
            'commercial': ['shopping_mall', 'store', 'restaurant']
        }
        
        all_buildings = {}
        
        for category, place_types in place_categories.items():
            category_places = []
            
            for place_type in place_types:
                try:
                    params = {
                        'location': f"{lat},{lon}",
                        'radius': radius,
                        'type': place_type,
                        'key': self.api_key,
                        'language': 'en'
                    }
                    
                    response = requests.get(self.base_places_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'OK':
                            results = data.get('results', [])
                            
                            for place in results:
                                name = place.get('name', '')
                                rating = place.get('rating', 0)
                                
                                # 只选择高评分的著名地点
                                if rating >= 4.0 and name not in category_places:
                                    category_places.append(name)
                                    
                                    # 每个类别最多3个地点
                                    if len(category_places) >= 3:
                                        break
                    
                    # 避免API限制，稍微延迟
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"⚠️ 获取 {place_type} 失败: {e}")
                    continue
            
            all_buildings[category] = category_places[:3]  # 每类最多3个
        
        # 打印获取结果
        total_places = sum(len(places) for places in all_buildings.values())
        print(f"✅ 获取到 {total_places} 个著名建筑/地标")
        
        for category, places in all_buildings.items():
            if places:
                print(f"  {category}: {', '.join(places)}")
        
        return all_buildings

    def get_top_nearby_places(self, lat: float, lon: float, radius: int = 1000, max_places: int = 4) -> List[str]:
        """获取附近最著名的地点（简化版）
        
        Args:
            lat: 纬度
            lon: 经度
            radius: 搜索半径（米）
            max_places: 最大返回地点数
            
        Returns:
            List[str]: 著名地点名称列表
        """
        building_dict = self.get_nearby_buildings(lat, lon, radius)
        
        # 提取所有建筑，优先级：landmarks > cultural > natural > commercial
        top_places = []
        priority_order = ['landmarks', 'cultural', 'natural', 'commercial']
        
        for category in priority_order:
            places = building_dict.get(category, [])
            for place in places:
                if place not in top_places:
                    top_places.append(place)
                    if len(top_places) >= max_places:
                        break
            if len(top_places) >= max_places:
                break
        
        return top_places
    
    def get_static_map(self, center_lat: float, center_lon: float, distance: float, 
                      width: int = 480, height: int = 640) -> Optional[Image.Image]:
        """获取静态地图图像
        
        Args:
            center_lat: 中心点纬度
            center_lon: 中心点经度
            distance: 距离（米），用于确定缩放级别
            width: 地图宽度（像素）
            height: 地图高度（像素）
            
        Returns:
            PIL.Image: 地图图像，失败时返回None
        """
        # 根据距离确定合适的缩放级别
        if distance <= 500:
            zoom = 16
        elif distance <= 1000:
            zoom = 15
        elif distance <= 2000:
            zoom = 14
        elif distance <= 5000:
            zoom = 13
        else:
            zoom = 12
        
        params = {
            'center': f"{center_lat},{center_lon}",
            'zoom': str(zoom),
            'size': f"{width}x{height}",
            'maptype': 'roadmap',
            'markers': f"color:red|label:T|{center_lat},{center_lon}",  # T for Target
            'key': self.api_key,
            'format': 'png'
        }
        
        try:
            print(f"🌐 获取地图: 缩放级别 {zoom}, 尺寸 {width}x{height}")
            
            response = requests.get(self.base_staticmap_url, params=params, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    image = Image.open(io.BytesIO(response.content))
                    print(f"✅ 地图获取成功: {image.size}")
                    return image
                else:
                    print(f"❌ 响应不是图像格式: {content_type}")
            else:
                print(f"❌ 地图请求失败: {response.status_code}")
                if response.text:
                    print(f"错误信息: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 地图请求异常: {e}")
        
        return None
    
    def get_location_details(self, lat: float, lon: float) -> Dict:
        """获取位置详细信息
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            Dict: 包含详细地址信息的字典
        """
        try:
            params = {
                'latlng': f"{lat},{lon}",
                'key': self.api_key,
                'language': 'zh-CN'
            }
            
            response = requests.get(self.base_geocoding_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and data['results']:
                    result = data['results'][0]
                    
                    # 解析地址组件
                    components = {}
                    for component in result.get('address_components', []):
                        for comp_type in component.get('types', []):
                            components[comp_type] = component.get('long_name', '')
                    
                    return {
                        'formatted_address': result.get('formatted_address', ''),
                        'country': components.get('country', ''),
                        'administrative_area_level_1': components.get('administrative_area_level_1', ''),
                        'locality': components.get('locality', ''),
                        'sublocality': components.get('sublocality', ''),
                        'route': components.get('route', ''),
                        'street_number': components.get('street_number', ''),
                        'postal_code': components.get('postal_code', ''),
                        'location_type': result.get('geometry', {}).get('location_type', ''),
                        'place_id': result.get('place_id', '')
                    }
                    
        except Exception as e:
            print(f"⚠️ 获取详细位置信息失败: {e}")
        
        return {
            'formatted_address': f"位置: {lat:.4f}, {lon:.4f}",
            'country': '',
            'locality': '',
            'error': True
        }
    
    def format_distance(self, distance: float) -> str:
        """格式化距离显示
        
        Args:
            distance: 距离（米）
            
        Returns:
            str: 格式化的距离字符串
        """
        if distance >= 1000:
            return f"{distance/1000:.1f}km"
        else:
            return f"{int(distance)}m"
    
    def get_direction_name(self, angle: float) -> str:
        """将角度转换为方向名称
        
        Args:
            angle: 角度 (0-360)
            
        Returns:
            str: 方向名称
        """
        directions = [
            (0, "正北"), (22.5, "北-东北"), (45, "东北"), (67.5, "东-东北"),
            (90, "正东"), (112.5, "东-东南"), (135, "东南"), (157.5, "南-东南"),
            (180, "正南"), (202.5, "南-西南"), (225, "西南"), (247.5, "西-西南"),
            (270, "正西"), (292.5, "西-西北"), (315, "西北"), (337.5, "北-西北")
        ]
        
        # 找到最接近的方向
        min_diff = 360
        closest_direction = "正北"
        
        for dir_angle, dir_name in directions:
            diff = min(abs(angle - dir_angle), 360 - abs(angle - dir_angle))
            if diff < min_diff:
                min_diff = diff
                closest_direction = dir_name
        
        return closest_direction
    
    def test_api_connection(self) -> bool:
        """测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 测试地理编码 - 查询伦敦
            params = {
                'address': 'London, UK',
                'key': self.api_key
            }
            
            response = requests.get(self.base_geocoding_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    print("✅ Google Maps API连接测试成功")
                    return True
                else:
                    print(f"❌ API测试失败: {data.get('status', 'Unknown')}")
            else:
                print(f"❌ API请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API连接测试异常: {e}")
        
        return False

if __name__ == "__main__":
    # 测试用例
    import os
    
    print("🗺️ Google Maps客户端测试")
    print("=" * 40)
    
    # 从环境变量获取API密钥
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ 请设置 GOOGLE_MAPS_API_KEY 环境变量")
        exit(1)
    
    client = MapsClient(api_key)
    
    # 测试1: API连接
    print("\n📡 测试1: API连接")
    if not client.test_api_connection():
        print("❌ API连接失败")
        exit(1)
    
    # 测试2: 逆地理编码
    print("\n📍 测试2: 逆地理编码")
    test_locations = [
        (51.5074, -0.1278, "伦敦市中心"),
        (39.9042, 116.4074, "北京市中心"),
        (40.7128, -74.0060, "纽约市中心")
    ]
    
    for lat, lon, name in test_locations:
        location_info = client.get_location_info(lat, lon)
        print(f"{name}: {location_info}")
    
    # 测试3: 地图获取
    print("\n🗺️ 测试3: 静态地图获取")
    lat, lon = 51.5074, -0.1278  # 伦敦
    distance = 2000  # 2km
    
    map_image = client.get_static_map(lat, lon, distance, 400, 300)
    if map_image:
        filename = "test_map.png"
        map_image.save(filename)
        print(f"✅ 地图保存为: {filename}")
    else:
        print("❌ 地图获取失败")
    
    # 测试4: 详细位置信息
    print("\n📋 测试4: 详细位置信息")
    details = client.get_location_details(51.5074, -0.1278)
    print(f"完整地址: {details['formatted_address']}")
    print(f"国家: {details['country']}")
    print(f"城市: {details['locality']}")
    
    print("\n✅ 测试完成") 