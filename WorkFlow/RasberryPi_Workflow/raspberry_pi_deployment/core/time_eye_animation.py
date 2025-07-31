"""
Time Eye Animation - 科技动感版"时间之眼"动效
为Obscura No.7虚拟望远镜的未来预测功能提供视觉动效
"""

import pygame
import math
import random
import time
from typing import Tuple, List

class Particle:
    """粒子类 - 用于光环边缘流动效果"""
    def __init__(self, x: float, y: float, angle: float, speed: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.alpha = random.randint(100, 255)
        self.life = 1.0
        self.decay_rate = random.uniform(0.005, 0.02)
    
    def update(self, dt: float):
        """更新粒子状态"""
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        self.life -= self.decay_rate * dt
        self.alpha = int(self.life * 255)
    
    def is_alive(self) -> bool:
        """检查粒子是否存活"""
        return self.life > 0

class StarPoint:
    """星点类 - 光环内部的闪烁星点"""
    def __init__(self, x: float, y: float, base_radius: float):
        self.x = x
        self.y = y
        self.base_radius = base_radius
        self.flicker_timer = random.uniform(0, 2 * math.pi)
        self.flicker_speed = random.uniform(1.5, 4.0)  # 降低星点闪烁速度：3.0-8.0 -> 1.5-4.0
        self.pulse_offset = random.uniform(0, 2 * math.pi)
        self.size_variance = random.uniform(0.5, 1.5)
        
    def update(self, dt: float, global_pulse: float):
        """更新星点状态"""
        self.flicker_timer += self.flicker_speed * dt
    
    def get_brightness(self, global_pulse: float) -> float:
        """获取星点亮度 (0.0 - 1.0)"""
        # 个体闪烁 + 全局脉冲
        individual_flicker = 0.5 + 0.3 * math.sin(self.flicker_timer)
        pulse_effect = 0.2 + 0.8 * global_pulse  # 脉冲时显著增亮
        return min(1.0, individual_flicker * pulse_effect)
    
    def get_size(self, global_pulse: float) -> float:
        """获取星点大小"""
        base_size = 2 + self.size_variance * math.sin(self.flicker_timer * 0.7)
        pulse_boost = 1.0 + 0.5 * global_pulse  # 脉冲时变大
        return base_size * pulse_boost
    
    def get_color(self, brightness: float) -> Tuple[int, int, int]:
        """获取星点颜色 - 蓝色到金色渐变，科技动感"""
        # 科技蓝 -> 电光蓝 -> 金色 -> 白色
        if brightness < 0.3:
            # 深蓝到电光蓝
            factor = brightness / 0.3
            return (
                int(30 + factor * 70),   # R: 30 -> 100
                int(144 + factor * 100), # G: 144 -> 244  
                int(255),                # B: 255 (保持蓝)
            )
        elif brightness < 0.7:
            # 电光蓝到金色
            factor = (brightness - 0.3) / 0.4
            return (
                int(100 + factor * 155), # R: 100 -> 255
                int(244 + factor * 11),  # G: 244 -> 255
                int(255 - factor * 105), # B: 255 -> 150
            )
        else:
            # 金色到纯白
            factor = (brightness - 0.7) / 0.3
            return (
                255,                     # R: 255
                255,                     # G: 255
                int(150 + factor * 105), # B: 150 -> 255
            )

class TimeEyeAnimation:
    """时间之眼动画类 - 科技动感版"""
    
    def __init__(self, screen_width: int, screen_height: int, location_info: str = "Unknown Location", future_time: str = "Unknown Time"):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # 将圆圈往上移动 - 从 screen_height // 2 改为稍微往上的位置
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2 - 60  # 往上移动60像素
        
        # 位置和时间信息
        self.location_info = location_info
        self.future_time = future_time
        
        # 动画参数
        self.cycle_duration = 5.0  # 5秒循环
        self.start_time = time.time()
        
        # 光环参数
        self.ring_radius = min(screen_width, screen_height) * 0.15  # 基础半径
        self.ring_thickness = 3
        self.rotation_speed = 0.045  # 进一步降速到0.5倍：0.09 * 0.5 = 0.045
        
        # 星点生成
        self.star_points = self._generate_star_points()
        
        # 粒子系统
        self.particles: List[Particle] = []
        self.particle_spawn_timer = 0
        self.particle_spawn_interval = 0.1  # 降低粒子生成频率：0.05 -> 0.1
        
        # 脉冲效果
        self.pulse_frequency = 1.0  # 降低脉冲频率：2.0 -> 1.0
        
    def _generate_star_points(self) -> List[StarPoint]:
        """生成光环内部的星点"""
        points = []
        num_points = 12  # 12个星点，形成神秘图案
        
        for i in range(num_points):
            # 在光环内部随机分布
            distance = random.uniform(0.2, 0.8) * self.ring_radius
            angle = random.uniform(0, 2 * math.pi)
            
            x = self.center_x + distance * math.cos(angle)
            y = self.center_y + distance * math.sin(angle)
            
            points.append(StarPoint(x, y, distance))
        
        return points
    
    def _get_ring_color(self, progress: float) -> Tuple[int, int, int]:
        """获取光环颜色 - 科技渐变"""
        # 科技蓝 -> 青色 -> 金色循环
        if progress < 0.33:
            factor = progress / 0.33
            return (
                int(0 + factor * 100),    # R: 0 -> 100
                int(200 + factor * 55),   # G: 200 -> 255
                int(255),                 # B: 255
            )
        elif progress < 0.66:
            factor = (progress - 0.33) / 0.33
            return (
                int(100 + factor * 155),  # R: 100 -> 255
                int(255),                 # G: 255
                int(255 - factor * 105),  # B: 255 -> 150
            )
        else:
            factor = (progress - 0.66) / 0.34
            return (
                int(255 - factor * 255),  # R: 255 -> 0
                int(255 - factor * 55),   # G: 255 -> 200
                int(150 + factor * 105),  # B: 150 -> 255
            )
    
    def _get_global_pulse(self, elapsed: float) -> float:
        """获取全局脉冲强度 (0.0 - 1.0)"""
        pulse_cycle = (elapsed * self.pulse_frequency) % 1.0
        if pulse_cycle < 0.2:  # 脉冲持续0.2秒
            return math.sin(pulse_cycle * math.pi / 0.2) ** 2
        return 0.0
    
    def _spawn_particles(self, dt: float):
        """生成粒子效果"""
        self.particle_spawn_timer += dt
        if self.particle_spawn_timer >= self.particle_spawn_interval:
            self.particle_spawn_timer = 0
            
            # 在光环上生成粒子
            angle = random.uniform(0, 2 * math.pi)
            spawn_x = self.center_x + self.ring_radius * math.cos(angle)
            spawn_y = self.center_y + self.ring_radius * math.sin(angle)
            
            # 粒子向外流动
            particle_angle = angle + random.uniform(-0.3, 0.3)
            particle_speed = random.uniform(20, 50)
            particle_color = (
                random.randint(100, 255),
                random.randint(200, 255),
                random.randint(150, 255)
            )
            
            self.particles.append(Particle(spawn_x, spawn_y, particle_angle, particle_speed, particle_color))
    
    def update(self, dt: float):
        """更新动画状态"""
        elapsed = time.time() - self.start_time
        
        # 更新星点
        global_pulse = self._get_global_pulse(elapsed)
        for star in self.star_points:
            star.update(dt, global_pulse)
        
        # 生成和更新粒子
        self._spawn_particles(dt)
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update(dt)
    
    def draw(self, screen: pygame.Surface):
        """绘制动画"""
        # 全黑背景
        screen.fill((0, 0, 0))
        
        elapsed = time.time() - self.start_time
        cycle_progress = (elapsed / self.cycle_duration) % 1.0
        rotation_angle = elapsed * self.rotation_speed
        global_pulse = self._get_global_pulse(elapsed)
        
        # 绘制旋转光环
        ring_color = self._get_ring_color(cycle_progress)
        
        # 增强脉冲时的光环效果
        pulse_boost = 1.0 + global_pulse * 0.5
        current_ring_radius = self.ring_radius * pulse_boost
        current_thickness = int(self.ring_thickness * pulse_boost)
        
        # 绘制多层光环产生光辉效果
        for i in range(current_thickness):
            alpha = int(255 * (1.0 - i / current_thickness) * (0.6 + 0.4 * global_pulse))
            color_with_alpha = (*ring_color, alpha)
            
            # 创建临时surface以支持alpha
            ring_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, color_with_alpha, 
                             (self.center_x, self.center_y), 
                             int(current_ring_radius + i), 1)
            screen.blit(ring_surface, (0, 0))
        
        # 绘制星点
        for star in self.star_points:
            brightness = star.get_brightness(global_pulse)
            size = star.get_size(global_pulse)
            color = star.get_color(brightness)
            alpha = int(brightness * 255)
            
            # 绘制星点光晕
            star_surface = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(star_surface, (*color, alpha), 
                             (int(size * 2), int(size * 2)), int(size))
            # 外光晕
            pygame.draw.circle(star_surface, (*color, alpha // 3), 
                             (int(size * 2), int(size * 2)), int(size * 1.5))
            
            screen.blit(star_surface, (star.x - size * 2, star.y - size * 2))
        
        # 绘制粒子
        for particle in self.particles:
            if particle.alpha > 0:
                particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (*particle.color, particle.alpha), 
                                 (3, 3), 2)
                screen.blit(particle_surface, (particle.x - 3, particle.y - 3))
        
        # 绘制中心状态文本
        font = pygame.font.Font(None, 48)
        title_text = font.render("PREDICTING THE FUTURE", True, (200, 200, 255))
        title_rect = title_text.get_rect(center=(self.center_x, self.center_y + self.ring_radius + 40))  # 减少距离：60 -> 40
        screen.blit(title_text, title_rect)
        
        # 动态状态提示
        status_font = pygame.font.Font(None, 32)
        pulse_alpha = int(150 + 105 * global_pulse)
        status_text = status_font.render("Analyzing temporal possibilities...", True, (150, 200, 255, pulse_alpha))
        status_rect = status_text.get_rect(center=(self.center_x, self.center_y + self.ring_radius + 75))  # 减少距离：100 -> 75
        screen.blit(status_text, status_rect)
        
        # 添加位置和时间信息 - 往上移动，增大字体
        info_font = pygame.font.Font(None, 36)  # 从28增加到36
        
        # Location信息 - 往上移动，优化显示格式
        location_text = info_font.render(f"Location: {self.location_info}", True, (200, 220, 240))  # 调亮颜色
        location_rect = location_text.get_rect(center=(self.center_x, self.center_y + self.ring_radius + 105))  
        screen.blit(location_text, location_rect)
        
        # Future Time信息 - 往上移动，优化显示格式
        future_text = info_font.render(f"Future Time: {self.future_time}", True, (200, 220, 240))  # 调亮颜色
        future_rect = future_text.get_rect(center=(self.center_x, self.center_y + self.ring_radius + 140))  # 从130增加到140，为更大字体留出空间
        screen.blit(future_text, future_rect) 