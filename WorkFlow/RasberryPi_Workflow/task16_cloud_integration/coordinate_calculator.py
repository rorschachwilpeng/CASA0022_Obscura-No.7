#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标计算模块
基于距离和方向计算目标地理坐标
"""

import math

class CoordinateCalculator:
    def __init__(self, base_location=(51.5074, -0.1278)):
        """初始化坐标计算器
        Args:
            base_location: 基础位置 (lat, lon)，默认为伦敦市中心
        """
        self.base_lat, self.base_lon = base_location
        self.earth_radius = 6371000  # 地球半径（米）
    
    def calculate_target_coordinates(self, distance, direction_degrees):
        """计算目标坐标
        Args:
            distance: 距离（米）
            direction_degrees: 方向角度（0=正北，90=正东）
        Returns:
            tuple: (纬度, 经度)
        """
        # 将角度转换为弧度
        lat1_rad = math.radians(self.base_lat)
        lon1_rad = math.radians(self.base_lon)
        bearing_rad = math.radians(direction_degrees)
        
        # 计算角距离
        angular_distance = distance / self.earth_radius
        
        # 使用球面三角学计算目标坐标
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(angular_distance) +
            math.cos(lat1_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1_rad),
            math.cos(angular_distance) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        # 转换回度数
        target_lat = math.degrees(lat2_rad)
        target_lon = math.degrees(lon2_rad)
        
        # 标准化经度到 -180 到 180 范围
        target_lon = ((target_lon + 180) % 360) - 180
        
        return (target_lat, target_lon)
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两点间距离（米）- Haversine公式"""
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine公式
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = self.earth_radius * c
        return distance
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """计算两点间方位角（度）"""
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        # 计算方位角
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # 标准化到 0-360 度范围
        bearing_deg = (bearing_deg + 360) % 360
        
        return bearing_deg
    
    def validate_coordinates(self, lat, lon):
        """验证坐标有效性"""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    def get_coordinate_info(self, lat, lon):
        """获取坐标详细信息"""
        if not self.validate_coordinates(lat, lon):
            return None
        
        # 计算相对于基础位置的距离和方向
        distance = self.calculate_distance(self.base_lat, self.base_lon, lat, lon)
        bearing = self.calculate_bearing(self.base_lat, self.base_lon, lat, lon)
        
        return {
            'latitude': lat,
            'longitude': lon,
            'distance_from_base': distance,
            'bearing_from_base': bearing,
            'distance_km': distance / 1000,
            'formatted_coords': f"{lat:.6f}, {lon:.6f}"
        }

if __name__ == "__main__":
    # 测试用例
    print("🧮 坐标计算器测试")
    print("=" * 40)
    
    calc = CoordinateCalculator()
    print(f"基础位置: {calc.base_lat}, {calc.base_lon} (伦敦市中心)")
    
    # 测试1: 计算目标坐标
    print("\n📍 测试1: 计算目标坐标")
    distance = 5000  # 5km
    direction = 90   # 正东
    target_lat, target_lon = calc.calculate_target_coordinates(distance, direction)
    print(f"距离: {distance}m, 方向: {direction}°")
    print(f"目标坐标: {target_lat:.6f}, {target_lon:.6f}")
    
    # 验证计算
    calculated_distance = calc.calculate_distance(calc.base_lat, calc.base_lon, target_lat, target_lon)
    calculated_bearing = calc.calculate_bearing(calc.base_lat, calc.base_lon, target_lat, target_lon)
    print(f"验证距离: {calculated_distance:.1f}m (误差: {abs(distance-calculated_distance):.1f}m)")
    print(f"验证方向: {calculated_bearing:.1f}° (误差: {abs(direction-calculated_bearing):.1f}°)")
    
    # 测试2: 多个方向测试
    print("\n🧭 测试2: 多个方向测试")
    test_cases = [
        (2000, 0, "正北"),
        (3000, 90, "正东"), 
        (4000, 180, "正南"),
        (5000, 270, "正西"),
        (1500, 45, "东北"),
        (2500, 135, "东南"),
        (3500, 225, "西南"),
        (4500, 315, "西北")
    ]
    
    for dist, dir_deg, dir_name in test_cases:
        lat, lon = calc.calculate_target_coordinates(dist, dir_deg)
        info = calc.get_coordinate_info(lat, lon)
        print(f"{dir_name:4s} {dist:4d}m: {lat:8.4f}, {lon:9.4f} (验证: {info['distance_km']:.2f}km)")
    
    print("\n✅ 坐标计算器测试完成")
