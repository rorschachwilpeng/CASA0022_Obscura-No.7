#!/usr/bin/env python3
"""
HyperPixel 触摸屏校准和测试工具
用于诊断和修复触摸精度问题

使用方法:
python3 touch_calibration.py
"""

import pygame
import sys
import time
import math
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

class TouchCalibration:
    """触摸屏校准工具"""
    
    def __init__(self):
        # 初始化pygame
        pygame.init()
        pygame.font.init()
        
        # 检测屏幕分辨率
        self.detect_resolution()
        
        # 创建显示
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("触摸屏校准工具")
        
        # 字体
        self.font_large = pygame.font.Font(None, 48)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # 颜色
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'gray': (128, 128, 128)
        }
        
        # 校准数据
        self.calibration_points = []
        self.touch_events = []
        
        # 当前测试模式
        self.test_mode = "main_menu"
        
        self.clock = pygame.time.Clock()
        self.running = True
        
    def detect_resolution(self):
        """检测屏幕分辨率"""
        try:
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            print(f"🖥️ 检测到屏幕分辨率: {self.screen_width}x{self.screen_height}")
        except:
            # 默认分辨率
            self.screen_width = 800
            self.screen_height = 480
            print(f"🖥️ 使用默认分辨率: {self.screen_width}x{self.screen_height}")
    
    def draw_crosshair(self, pos, color, size=20):
        """绘制十字准星"""
        x, y = pos
        pygame.draw.line(self.screen, color, (x-size, y), (x+size, y), 3)
        pygame.draw.line(self.screen, color, (x, y-size), (x, y+size), 3)
        pygame.draw.circle(self.screen, color, pos, size//2, 2)
    
    def draw_text_centered(self, text, y, color=None, font=None):
        """绘制居中文本"""
        if color is None:
            color = self.colors['white']
        if font is None:
            font = self.font_normal
            
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, y))
        self.screen.blit(text_surface, text_rect)
    
    def main_menu(self):
        """主菜单"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("HyperPixel 触摸屏校准工具", 50, self.colors['yellow'], self.font_large)
        
        menu_items = [
            "1. 触摸精度测试",
            "2. 四角校准测试", 
            "3. 多点触摸测试",
            "4. 触摸偏置诊断",  # 新增选项
            "5. 事件日志测试",
            "6. 坐标映射测试",
            "ESC. 退出"
        ]
        
        for i, item in enumerate(menu_items):
            self.draw_text_centered(item, 150 + i * 50, self.colors['white'])
        
        self.draw_text_centered("请按对应数字键或触摸屏幕", self.screen_height - 50, self.colors['green'])
    
    def precision_test(self):
        """触摸精度测试"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("触摸精度测试", 30, self.colors['yellow'], self.font_large)
        self.draw_text_centered("请尽可能精确地触摸十字准星中心", 80, self.colors['white'])
        self.draw_text_centered("按ESC返回菜单", self.screen_height - 30, self.colors['gray'])
        
        # 绘制测试点
        test_points = [
            (self.screen_width // 4, self.screen_height // 4),
            (3 * self.screen_width // 4, self.screen_height // 4),
            (self.screen_width // 2, self.screen_height // 2),
            (self.screen_width // 4, 3 * self.screen_height // 4),
            (3 * self.screen_width // 4, 3 * self.screen_height // 4)
        ]
        
        for point in test_points:
            self.draw_crosshair(point, self.colors['red'], 30)
        
        # 显示触摸历史
        y_offset = 120
        for i, (event_time, pos, target) in enumerate(self.touch_events[-10:]):
            if target:
                distance = math.sqrt((pos[0] - target[0])**2 + (pos[1] - target[1])**2)
                text = f"#{i+1}: 触摸({pos[0]}, {pos[1]}) 目标({target[0]}, {target[1]}) 误差:{distance:.1f}px"
                color = self.colors['green'] if distance < 20 else self.colors['red']
                text_surface = self.font_small.render(text, True, color)
                self.screen.blit(text_surface, (10, y_offset + i * 25))
    
    def corner_calibration(self):
        """四角校准测试"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("四角校准测试", 30, self.colors['yellow'], self.font_large)
        self.draw_text_centered("请依次触摸四个角落的十字准星", 80, self.colors['white'])
        
        # 四个角落的校准点
        corners = [
            (50, 50),  # 左上
            (self.screen_width - 50, 50),  # 右上
            (50, self.screen_height - 50),  # 左下
            (self.screen_width - 50, self.screen_height - 50)  # 右下
        ]
        
        for i, corner in enumerate(corners):
            completed = i < len(self.calibration_points)
            color = self.colors['green'] if completed else self.colors['red']
            self.draw_crosshair(corner, color, 25)
            
            # 标注角落
            labels = ["左上", "右上", "左下", "右下"]
            label_text = self.font_small.render(labels[i], True, color)
            self.screen.blit(label_text, (corner[0] - 20, corner[1] + 35))
        
        # 显示校准结果
        if len(self.calibration_points) >= 4:
            self.draw_text_centered("校准完成！分析结果:", 200, self.colors['green'])
            
            for i, (expected, actual) in enumerate(zip(corners, self.calibration_points[-4:])):
                error = math.sqrt((expected[0] - actual[0])**2 + (expected[1] - actual[1])**2)
                text = f"角落{i+1}: 期望({expected[0]}, {expected[1]}) 实际({actual[0]}, {actual[1]}) 误差:{error:.1f}px"
                color = self.colors['green'] if error < 30 else self.colors['red']
                text_surface = self.font_small.render(text, True, color)
                self.screen.blit(text_surface, (10, 240 + i * 25))
        
        self.draw_text_centered("按R重置校准，ESC返回菜单", self.screen_height - 30, self.colors['gray'])
    
    def multi_touch_test(self):
        """多点触摸测试"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("多点触摸测试", 30, self.colors['yellow'], self.font_large)
        self.draw_text_centered("同时用多个手指触摸屏幕", 80, self.colors['white'])
        self.draw_text_centered("按ESC返回菜单", self.screen_height - 30, self.colors['gray'])
        
        # 显示当前触摸点
        for i, (event_time, pos, _) in enumerate(self.touch_events[-5:]):
            age = time.time() - event_time
            if age < 2.0:  # 显示2秒内的触摸
                alpha = int(255 * (2.0 - age) / 2.0)
                color = (*self.colors['blue'][:3], alpha) if age < 1.0 else self.colors['gray']
                pygame.draw.circle(self.screen, color[:3], pos, 20, 3)
                
                # 标注坐标
                coord_text = self.font_small.render(f"({pos[0]}, {pos[1]})", True, color[:3])
                self.screen.blit(coord_text, (pos[0] + 25, pos[1] - 10))
    
    def event_log_test(self):
        """事件日志测试"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("事件日志测试", 30, self.colors['yellow'], self.font_large)
        self.draw_text_centered("触摸屏幕查看详细事件信息", 80, self.colors['white'])
        self.draw_text_centered("按ESC返回菜单", self.screen_height - 30, self.colors['gray'])
        
        # 显示最近的事件
        y_offset = 120
        for i, (event_time, pos, event_type) in enumerate(self.touch_events[-15:]):
            age = time.time() - event_time
            if age < 10.0:  # 显示10秒内的事件
                time_str = time.strftime("%H:%M:%S", time.localtime(event_time))
                text = f"{time_str} - {event_type} at ({pos[0]}, {pos[1]})"
                color = self.colors['green'] if age < 2.0 else self.colors['gray']
                text_surface = self.font_small.render(text, True, color)
                self.screen.blit(text_surface, (10, y_offset + i * 20))
    
    def coordinate_mapping_test(self):
        """坐标映射测试"""
        self.screen.fill(self.colors['black'])
        
        self.draw_text_centered("坐标映射测试", 30, self.colors['yellow'], self.font_large)
        self.draw_text_centered("显示触摸坐标和归一化坐标", 80, self.colors['white'])
        
        # 绘制网格
        grid_size = 50
        for x in range(0, self.screen_width, grid_size):
            pygame.draw.line(self.screen, self.colors['gray'], (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, grid_size):
            pygame.draw.line(self.screen, self.colors['gray'], (0, y), (self.screen_width, y), 1)
        
        # 显示坐标信息
        info_lines = [
            f"屏幕分辨率: {self.screen_width}x{self.screen_height}",
            f"网格大小: {grid_size}px",
            "触摸屏幕查看坐标映射"
        ]
        
        for i, line in enumerate(info_lines):
            text_surface = self.font_small.render(line, True, self.colors['white'])
            self.screen.blit(text_surface, (10, 120 + i * 25))
        
        # 显示最近的触摸点
        for event_time, pos, _ in self.touch_events[-1:]:
            if time.time() - event_time < 5.0:
                # 绘制触摸点
                pygame.draw.circle(self.screen, self.colors['red'], pos, 10, 2)
                
                # 显示坐标信息
                pixel_x, pixel_y = pos
                norm_x = pixel_x / self.screen_width
                norm_y = pixel_y / self.screen_height
                
                coord_lines = [
                    f"像素坐标: ({pixel_x}, {pixel_y})",
                    f"归一化坐标: ({norm_x:.3f}, {norm_y:.3f})",
                    f"网格位置: ({pixel_x // grid_size}, {pixel_y // grid_size})"
                ]
                
                for i, line in enumerate(coord_lines):
                    text_surface = self.font_small.render(line, True, self.colors['yellow'])
                    self.screen.blit(text_surface, (pixel_x + 15, pixel_y + i * 20))
        
        self.draw_text_centered("按ESC返回菜单", self.screen_height - 30, self.colors['gray'])
    
    def test_touch_precision(self):
        """精密触摸测试 - 专门诊断触摸偏置问题"""
        print("🎯 触摸精度测试模式")
        print("=" * 50)
        print("这个测试将帮助诊断触摸偏置问题")
        print("按 ESC 退出测试")
        print("=" * 50)
        
        # 创建测试目标
        test_targets = [
            {'pos': (100, 100), 'size': 50, 'label': '左上', 'color': (255, 100, 100)},
            {'pos': (700, 100), 'size': 50, 'label': '右上', 'color': (100, 255, 100)},
            {'pos': (100, 380), 'size': 50, 'label': '左下', 'color': (100, 100, 255)},
            {'pos': (700, 380), 'size': 50, 'label': '右下', 'color': (255, 255, 100)},
            {'pos': (400, 240), 'size': 60, 'label': '中心', 'color': (255, 100, 255)},
        ]
        
        # 校准偏移测试值
        calibration_offsets = [
            (0, 0),      # 无偏移
            (30, 0),     # 向右偏移30像素
            (50, 0),     # 向右偏移50像素  
            (-30, 0),    # 向左偏移30像素
            (0, 30),     # 向下偏移30像素
            (30, 30),    # 对角偏移
        ]
        
        current_offset_index = 1  # 从30像素偏移开始
        touch_log = []
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # 切换校准偏移
                        current_offset_index = (current_offset_index + 1) % len(calibration_offsets)
                        print(f"📐 切换到偏移: {calibration_offsets[current_offset_index]}")
                    elif event.key == pygame.K_c:
                        # 清除日志
                        touch_log.clear()
                        print("🧹 清除触摸日志")
                        
                elif event.type == pygame.FINGERDOWN:
                    # 原始触摸坐标
                    raw_x = int(event.x * self.screen_width)
                    raw_y = int(event.y * self.screen_height)
                    
                    # 应用当前校准偏移
                    offset_x, offset_y = calibration_offsets[current_offset_index]
                    calibrated_x = raw_x + offset_x
                    calibrated_y = raw_y + offset_y
                    
                    # 检查命中了哪个目标
                    hit_target = None
                    for i, target in enumerate(test_targets):
                        target_x, target_y = target['pos']
                        target_size = target['size']
                        
                        # 检查是否命中目标
                        distance = ((calibrated_x - target_x) ** 2 + (calibrated_y - target_y) ** 2) ** 0.5
                        if distance <= target_size:
                            hit_target = target['label']
                            print(f"🎯 命中目标: {hit_target}")
                            break
                    
                    # 记录触摸事件
                    touch_event = {
                        'raw_pos': (raw_x, raw_y),
                        'calibrated_pos': (calibrated_x, calibrated_y),
                        'offset': (offset_x, offset_y),
                        'hit_target': hit_target,
                        'timestamp': time.time()
                    }
                    touch_log.append(touch_event)
                    
                    print(f"👆 触摸: 原始({raw_x}, {raw_y}) → 校准({calibrated_x}, {calibrated_y}) → {hit_target or '未命中'}")
            
            # 清屏
            self.screen.fill((30, 30, 30))
            
            # 绘制标题
            title = self.font_large.render("触摸精度测试", True, (255, 255, 255))
            title_rect = title.get_rect(centerx=self.screen_width // 2, y=20)
            self.screen.blit(title, title_rect)
            
            # 显示当前偏移
            offset_x, offset_y = calibration_offsets[current_offset_index]
            offset_text = f"当前偏移: ({offset_x:+d}, {offset_y:+d}) 像素"
            offset_surface = self.font_small.render(offset_text, True, (200, 200, 100))
            offset_rect = offset_surface.get_rect(centerx=self.screen_width // 2, y=60)
            self.screen.blit(offset_surface, offset_rect)
            
            # 绘制测试目标
            for target in test_targets:
                pos = target['pos']
                size = target['size']
                color = target['color']
                label = target['label']
                
                # 绘制目标圆
                pygame.draw.circle(self.screen, color, pos, size, 3)
                pygame.draw.circle(self.screen, (255, 255, 255), pos, 5)
                
                # 绘制标签
                label_surface = self.font_small.render(label, True, (255, 255, 255))
                label_rect = label_surface.get_rect(center=(pos[0], pos[1] + size + 20))
                self.screen.blit(label_surface, label_rect)
            
            # 绘制最近的触摸点
            if touch_log:
                for i, touch in enumerate(touch_log[-5:]):  # 显示最近5次触摸
                    alpha = 255 - i * 40  # 逐渐透明
                    if alpha > 0:
                        calibrated_pos = touch['calibrated_pos']
                        raw_pos = touch['raw_pos']
                        
                        # 绘制校准后的触摸点（绿色）
                        pygame.draw.circle(self.screen, (0, 255, 0), calibrated_pos, 8)
                        
                        # 绘制原始触摸点（红色）
                        pygame.draw.circle(self.screen, (255, 0, 0), raw_pos, 6)
                        
                        # 绘制连接线
                        pygame.draw.line(self.screen, (100, 100, 100), raw_pos, calibrated_pos, 2)
            
            # 绘制说明
            instructions = [
                "🎯 点击彩色圆圈测试精度",
                "⌨️ SPACE: 切换校准偏移",
                "🧹 C: 清除日志",
                "🚪 ESC: 退出测试"
            ]
            
            for i, instruction in enumerate(instructions):
                text = self.font_small.render(instruction, True, (180, 180, 180))
                self.screen.blit(text, (20, self.screen_height - 100 + i * 20))
            
            # 显示统计信息
            if touch_log:
                stats_y = self.screen_height - 200
                stats = [
                    f"触摸次数: {len(touch_log)}",
                    f"命中次数: {sum(1 for t in touch_log if t['hit_target'])}",
                    f"准确率: {sum(1 for t in touch_log if t['hit_target']) / len(touch_log) * 100:.1f}%"
                ]
                
                for i, stat in enumerate(stats):
                    text = self.font_small.render(stat, True, (100, 255, 100))
                    self.screen.blit(text, (self.screen_width - 200, stats_y + i * 20))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # 输出详细的测试报告
        print("\n" + "=" * 60)
        print("📊 触摸精度测试报告")
        print("=" * 60)
        
        if touch_log:
            # 按偏移分组统计
            offset_stats = {}
            for touch in touch_log:
                offset = touch['offset']
                if offset not in offset_stats:
                    offset_stats[offset] = {'total': 0, 'hits': 0}
                offset_stats[offset]['total'] += 1
                if touch['hit_target']:
                    offset_stats[offset]['hits'] += 1
            
            for offset, stats in offset_stats.items():
                accuracy = stats['hits'] / stats['total'] * 100 if stats['total'] > 0 else 0
                print(f"偏移 {offset}: {stats['hits']}/{stats['total']} 命中 ({accuracy:.1f}%)")
            
            # 找出最佳偏移
            best_offset = max(offset_stats.keys(), 
                            key=lambda k: offset_stats[k]['hits'] / offset_stats[k]['total'])
            best_accuracy = offset_stats[best_offset]['hits'] / offset_stats[best_offset]['total'] * 100
            
            print(f"\n🎯 推荐校准偏移: {best_offset} (准确率: {best_accuracy:.1f}%)")
            print(f"💡 在enhanced_pygame_interface.py中使用:")
            print(f"   calibration_offset_x = {best_offset[0]}")
            print(f"   calibration_offset_y = {best_offset[1]}")
        else:
            print("⚠️ 没有收集到触摸数据")
        
        print("=" * 60)
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.test_mode == "main_menu":
                        self.running = False
                    else:
                        self.test_mode = "main_menu"
                        self.touch_events.clear()
                        
                elif self.test_mode == "main_menu":
                    if event.key == pygame.K_1:
                        self.test_mode = "precision"
                        self.touch_events.clear()
                    elif event.key == pygame.K_2:
                        self.test_mode = "calibration"
                        self.calibration_points.clear()
                    elif event.key == pygame.K_3:
                        self.test_mode = "multi_touch"
                        self.touch_events.clear()
                    elif event.key == pygame.K_4:
                        # 启动触摸偏置诊断
                        self.test_touch_precision()
                        self.test_mode = "main_menu"  # 诊断完成后返回菜单
                    elif event.key == pygame.K_5:
                        self.test_mode = "event_log"
                        self.touch_events.clear()
                    elif event.key == pygame.K_6:
                        self.test_mode = "coordinate_mapping"
                        self.touch_events.clear()
                        
                elif self.test_mode == "calibration" and event.key == pygame.K_r:
                    self.calibration_points.clear()
            
            # 处理触摸事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                self.handle_touch(pos, "MOUSE_DOWN")
                
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = event.pos
                self.handle_touch(pos, "MOUSE_UP")
                
            elif event.type == pygame.FINGERDOWN:
                # 转换触摸坐标
                touch_x = int(event.x * self.screen_width)
                touch_y = int(event.y * self.screen_height)
                pos = (touch_x, touch_y)
                self.handle_touch(pos, "FINGER_DOWN")
                
            elif event.type == pygame.FINGERUP:
                touch_x = int(event.x * self.screen_width)
                touch_y = int(event.y * self.screen_height)
                pos = (touch_x, touch_y)
                self.handle_touch(pos, "FINGER_UP")
    
    def handle_touch(self, pos, event_type):
        """处理触摸事件"""
        current_time = time.time()
        
        # 记录事件
        if self.test_mode == "precision":
            # 精度测试 - 检查最近的目标点
            test_points = [
                (self.screen_width // 4, self.screen_height // 4),
                (3 * self.screen_width // 4, self.screen_height // 4),
                (self.screen_width // 2, self.screen_height // 2),
                (self.screen_width // 4, 3 * self.screen_height // 4),
                (3 * self.screen_width // 4, 3 * self.screen_height // 4)
            ]
            
            closest_target = min(test_points, 
                                key=lambda p: math.sqrt((p[0] - pos[0])**2 + (p[1] - pos[1])**2))
            self.touch_events.append((current_time, pos, closest_target))
            
        elif self.test_mode == "calibration":
            # 校准测试
            if event_type in ["MOUSE_UP", "FINGER_UP"]:
                self.calibration_points.append(pos)
                
        elif self.test_mode == "touch_bias_diagnosis": # 新增模式
            # 触摸偏置诊断测试
            if event_type in ["MOUSE_DOWN", "FINGER_DOWN"]:
                self.touch_events.append((current_time, pos, "TOUCH_START"))
            elif event_type in ["MOUSE_UP", "FINGER_UP"]:
                self.touch_events.append((current_time, pos, "TOUCH_END"))
            else:
                self.touch_events.append((current_time, pos, "TOUCH_MOVE"))
                
        else:
            # 其他测试
            self.touch_events.append((current_time, pos, event_type))
    
    def run(self):
        """运行校准工具"""
        print("🎯 HyperPixel 触摸屏校准工具启动")
        print("使用说明:")
        print("- 使用数字键1-5选择测试模式")
        print("- ESC键返回菜单或退出")
        print("- 按照屏幕提示进行测试")
        
        while self.running:
            self.handle_events()
            
            # 根据当前模式绘制界面
            if self.test_mode == "main_menu":
                self.main_menu()
            elif self.test_mode == "precision":
                self.precision_test()
            elif self.test_mode == "calibration":
                self.corner_calibration()
            elif self.test_mode == "multi_touch":
                self.multi_touch_test()
            elif self.test_mode == "event_log":
                self.event_log_test()
            elif self.test_mode == "coordinate_mapping":
                self.coordinate_mapping_test()
            elif self.test_mode == "touch_bias_diagnosis": # 新增模式
                self.test_touch_precision()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        print("👋 触摸屏校准工具已退出")

if __name__ == "__main__":
    try:
        calibration = TouchCalibration()
        calibration.run()
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出校准工具")
    except Exception as e:
        print(f"❌ 校准工具错误: {e}")
        import traceback
        traceback.print_exc() 