"""
增强的 Pygame 界面 - 修复触摸和参数更新问题
针对 HyperPixel 触摸屏优化的界面组件

修复内容:
1. 修复pygame初始化顺序
2. 正确的触摸坐标映射
3. 实时参数更新显示
4. 更好的事件调试
"""

import pygame
import sys
import math
import time
import logging
from typing import Tuple, Optional, Dict, Any, Callable
from enum import Enum

from .exhibition_state_machine import ExhibitionState, StateContext

# 强制初始化pygame和字体系统 - 修复字体初始化问题
pygame.init()
pygame.font.init()

# 启用所有输入事件
pygame.event.set_allowed(None)

def detect_screen_resolution():
    """动态检测屏幕分辨率"""
    try:
        pygame.display.init()  # 确保显示系统已初始化
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        
        # HyperPixel 4.0 支持的分辨率
        if screen_width == 480 and screen_height == 800:
            # 竖屏模式
            return 480, 800
        elif screen_width == 800 and screen_height == 480:
            # 横屏模式
            return 800, 480
        else:
            # 默认使用 800x480
            return 800, 480
    except:
        # 如果检测失败，使用默认值
        return 800, 480

SCREEN_WIDTH, SCREEN_HEIGHT = detect_screen_resolution()
print(f"🖥️ 检测到屏幕分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

# 颜色定义
COLORS = {
    'background': (45, 35, 25),
    'primary': (255, 235, 200),
    'secondary': (180, 150, 120),
    'accent': (200, 140, 60),
    'success': (120, 180, 120),
    'warning': (255, 180, 80),
    'error': (220, 80, 80),
    'hover': (220, 190, 160),
    'pressed': (160, 120, 80),
}

# 字体大小定义
BASE_FONT_SIZES = {
    'small': 24,
    'normal': 32,  # 添加回missing的'normal'键 - 修复KeyError
    'medium': 32,
    'large': 48,
    'title': 64,
    'button': 28
}

class EnhancedButton:
    """增强型按钮，支持鼠标和触摸双重输入"""
    
    def __init__(self, x, y, width, height, text, callback=None, font_size=BASE_FONT_SIZES['button']):
        self.rect = pygame.Rect(x, y, width, height)
        # 扩大触摸区域 - 增加触摸容差解决精度问题
        touch_padding = 20
        self.touch_rect = pygame.Rect(x - touch_padding, y - touch_padding, 
                                    width + 2*touch_padding, height + 2*touch_padding)
        self.text = text
        self.callback = callback
        self.state = "normal"  # normal, hover, pressed
        self.enabled = True
        self.last_touch_time = 0
        self.touch_count = 0
        
        # 初始化字体 - 增加容错处理
        try:
            self.font = pygame.font.Font(None, font_size)
        except pygame.error:
            try:
                self.font = pygame.font.SysFont('arial', font_size)
                print(f"⚠️ 按钮 '{text}' 使用系统arial字体")
            except pygame.error:
                self.font = pygame.font.SysFont(None, font_size)
                print(f"⚠️ 按钮 '{text}' 使用系统默认字体")
    
    def handle_event(self, event):
        """处理事件，支持鼠标和触摸"""
        if not self.enabled:
            return False
        
        clicked = False
        
        # 处理鼠标事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = "pressed"
                print(f"🖱️ 按钮 '{self.text}' 鼠标按下")
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.state == "pressed" and self.rect.collidepoint(event.pos):
                clicked = True
                print(f"✅ 按钮 '{self.text}' 鼠标点击成功!")
            self.state = "normal"
            
        elif event.type == pygame.MOUSEMOTION:
            if self.touch_rect.collidepoint(event.pos):
                if self.state != "pressed":
                    self.state = "hover"
            else:
                if self.state == "hover":
                    self.state = "normal"
        
        # 处理触摸事件 - 修复坐标映射和精度问题
        elif event.type == pygame.FINGERDOWN:
            # 改进的触摸坐标转换 - 使用更精确的映射
            # 增加触摸校准偏移量来解决偏置问题
            touch_x = int(event.x * SCREEN_WIDTH)
            touch_y = int(event.y * SCREEN_HEIGHT)
            
            # 应用校准偏移 - 根据HyperPixel特性调整
            # 基于用户报告的"需要点击左边"问题，添加X轴偏移
            calibration_offset_x = 30  # 向右偏移30像素
            calibration_offset_y = 0   # Y轴暂不调整
            
            calibrated_x = touch_x + calibration_offset_x
            calibrated_y = touch_y + calibration_offset_y
            
            # 检查触摸区域（使用扩大的触摸区域）
            if self.touch_rect.collidepoint((calibrated_x, calibrated_y)):
                self.state = "pressed"
                self.last_touch_time = time.time()
                self.touch_count += 1
                print(f"👆 按钮 '{self.text}' 触摸按下: 原始({touch_x}, {touch_y}) → 校准({calibrated_x}, {calibrated_y})")
                
        elif event.type == pygame.FINGERUP:
            touch_x = int(event.x * SCREEN_WIDTH)
            touch_y = int(event.y * SCREEN_HEIGHT)
            
            # 应用相同的校准偏移
            calibrated_x = touch_x + 30
            calibrated_y = touch_y + 0
            
            if self.state == "pressed" and self.touch_rect.collidepoint((calibrated_x, calibrated_y)):
                clicked = True
                print(f"✅ 按钮 '{self.text}' 触摸点击成功! 校准坐标: ({calibrated_x}, {calibrated_y})")
            self.state = "normal"
        
        # 如果点击成功，调用回调
        if clicked and self.callback:
            self.callback()
        
        return clicked
    
    def set_enabled(self, enabled):
        """设置按钮启用状态"""
        self.enabled = enabled
        if not enabled:
            self.state = "normal"
    
    def draw(self, screen):
        """绘制按钮"""
        # 选择颜色
        if not self.enabled:
            color = (100, 100, 100)
            text_color = (150, 150, 150)
        elif self.state == "pressed":
            color = COLORS['pressed']
            text_color = COLORS['primary']
        elif self.state == "hover":
            color = COLORS['hover']
            text_color = COLORS['background']
        else:
            color = COLORS['secondary']
            text_color = COLORS['background']
        
        # 绘制按钮背景
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, COLORS['primary'], self.rect, 2)
        
        # 绘制按钮文本
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        # 调试模式：绘制触摸区域
        if hasattr(self, 'debug_mode') and self.debug_mode:
            pygame.draw.rect(screen, (255, 0, 0, 50), self.touch_rect, 1)

class ParameterDisplay:
    """参数显示组件"""
    
    def __init__(self, x, y, width, height, label, value, unit):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = value
        self.unit = unit
        
        # 初始化字体 - 增加容错处理
        try:
            self.label_font = pygame.font.Font(None, BASE_FONT_SIZES['small'])
            self.value_font = pygame.font.Font(None, BASE_FONT_SIZES['medium'])
        except pygame.error:
            try:
                self.label_font = pygame.font.SysFont('arial', BASE_FONT_SIZES['small'])
                self.value_font = pygame.font.SysFont('arial', BASE_FONT_SIZES['medium'])
            except pygame.error:
                self.label_font = pygame.font.SysFont(None, BASE_FONT_SIZES['small'])
                self.value_font = pygame.font.SysFont(None, BASE_FONT_SIZES['medium'])
    
    def update_value(self, value):
        """更新参数值"""
        self.value = value
    
    def draw(self, screen):
        """绘制参数显示"""
        # 背景
        pygame.draw.rect(screen, COLORS['background'], self.rect)
        pygame.draw.rect(screen, COLORS['accent'], self.rect, 2)
        
        # 标签
        label_surface = self.label_font.render(self.label, True, COLORS['secondary'])
        label_rect = label_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 5)
        screen.blit(label_surface, label_rect)
        
        # 数值
        value_text = f"{self.value:.1f}{self.unit}"
        value_surface = self.value_font.render(value_text, True, COLORS['primary'])
        value_rect = value_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 35)
        screen.blit(value_surface, value_rect)

class EnhancedPygameInterface:
    """增强的pygame界面，修复触摸精度和字体初始化问题"""
    
    def __init__(self, fullscreen: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # 确保pygame已完全初始化
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        # 初始化显示
        display_flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
        pygame.display.set_caption("Obscura No.7 - Enhanced Interface")
        
        # 隐藏鼠标光标
        if fullscreen:
            pygame.mouse.set_visible(False)
        
        # 初始化字体系统 - 增加完整的容错处理
        self.fonts = {}
        for name, size in BASE_FONT_SIZES.items():
            try:
                self.fonts[name] = pygame.font.Font(None, size)
            except pygame.error:
                try:
                    self.fonts[name] = pygame.font.SysFont('arial', size)
                    self.logger.warning(f"字体 '{name}' 使用系统arial字体")
                except pygame.error:
                    try:
                        self.fonts[name] = pygame.font.SysFont('liberation', size)
                        self.logger.warning(f"字体 '{name}' 使用liberation字体")  
                    except pygame.error:
                        self.fonts[name] = pygame.font.SysFont(None, size)
                        self.logger.warning(f"字体 '{name}' 使用系统默认字体")
        
        # 时钟
        self.clock = pygame.time.Clock()
        
        # 状态
        self.current_state = ExhibitionState.CITY_SELECTION
        self.context = None
        self.running = True
        
        # 参数显示
        self.distance_display = ParameterDisplay(50, 100, 150, 80, "距离", 25.0, "km")
        self.angle_display = ParameterDisplay(250, 100, 150, 80, "方向", 0.0, "°")
        self.time_display = ParameterDisplay(450, 100, 150, 80, "时间偏移", 0.0, "年")
        
        # 城市按钮
        city_button_y = 300
        city_button_width = 200
        city_button_height = 60
        city_button_spacing = 220
        
        self.city_buttons = [
            EnhancedButton(50, city_button_y, city_button_width, city_button_height, "伦敦", self._on_city_london),
            EnhancedButton(270, city_button_y, city_button_width, city_button_height, "爱丁堡", self._on_city_edinburgh),
            EnhancedButton(490, city_button_y, city_button_width, city_button_height, "曼彻斯特", self._on_city_manchester),
        ]
        
        # 控制按钮
        control_button_y = 400
        control_button_width = 150
        control_button_height = 50
        
        self.generate_button = EnhancedButton(50, control_button_y, control_button_width, control_button_height, "生成", self._on_generate)
        self.continue_button = EnhancedButton(250, control_button_y, control_button_width, control_button_height, "继续", self._on_continue)
        self.reset_button = EnhancedButton(450, control_button_y, control_button_width, control_button_height, "重置", self._on_reset)
        
        # 回调函数
        self.on_city_selected = None
        self.on_generate_click = None
        self.on_continue_click = None
        self.on_reset_click = None
        
        # 调试模式
        self.debug_mode = False
        
        # 触摸校准设置
        self.touch_calibration_enabled = True
        self.touch_events_log = []
        
        self.logger.info("Enhanced pygame interface initialized with touch calibration fixes")
    
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event == 'on_city_selected':
            self.on_city_selected = callback
        elif event == 'on_generate_click':
            self.on_generate_click = callback
        elif event == 'on_continue_click':
            self.on_continue_click = callback
        elif event == 'on_reset_click':
            self.on_reset_click = callback
    
    def on_city_selected(self, city: str):
        self.logger.info(f"City selected: {city}")
        if self.on_city_selected:
            self.on_city_selected(city)
    
    def on_generate_click(self):
        self.logger.info("Generate button clicked")
        if self.on_generate_click:
            self.on_generate_click()
    
    def on_continue_click(self):
        self.logger.info("Continue button clicked")
        if self.on_continue_click:
            self.on_continue_click()
    
    def on_reset_click(self):
        self.logger.info("Reset button clicked")
        if self.on_reset_click:
            self.on_reset_click()
    
    def update_state(self, state: ExhibitionState, context: StateContext):
        """更新界面状态"""
        self.current_state = state
        self.context = context
        
        # 更新参数显示
        if context:
            self.distance_display.update_value(context.distance_km)
            self.angle_display.update_value(context.angle_degrees)
            self.time_display.update_value(context.time_offset_years)
        
        # 根据状态更新按钮可见性和可用性
        self._update_button_states()
        
        self.logger.info(f"Interface state updated: {state.value}")
    
    def _update_button_states(self):
        """根据当前状态更新按钮状态"""
        # 城市按钮只在城市选择状态可用
        for button in self.city_buttons:
            button.enabled = (self.current_state == ExhibitionState.CITY_SELECTION)
        
        # 生成按钮在参数输入状态可用
        self.generate_button.enabled = (self.current_state == ExhibitionState.PARAMETER_INPUT)
        
        # 继续按钮在等待交互状态可用
        self.continue_button.enabled = (self.current_state == ExhibitionState.WAITING_INTERACTION)
        
        # 重置按钮在大部分状态下可用，除了处理中
        self.reset_button.enabled = (self.current_state != ExhibitionState.PROCESSING)
    
    def handle_events(self) -> bool:
        """处理事件 - 在所有状态下处理触摸事件"""
        for event in pygame.event.get():
            # 记录调试事件
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, 
                             pygame.FINGERDOWN, pygame.FINGERUP]:
                event_info = f"{pygame.event.event_name(event.type)}"
                if hasattr(event, 'pos'):
                    event_info += f" at {event.pos}"
                elif hasattr(event, 'x'):
                    event_info += f" at ({event.x:.3f}, {event.y:.3f})"
                
                # self.debug_events.append((time.time(), event_info)) # Original line commented out
                # self.debug_events = self.debug_events[-10:] # Original line commented out
            
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_d:  # 切换调试显示
                    self.debug_mode = not self.debug_mode
            
            # 在所有状态下都处理按钮事件
            button_handled = False
            
            # 处理城市按钮（只在城市选择状态）
            if self.current_state == ExhibitionState.CITY_SELECTION:
                for button in self.city_buttons:
                    if button.handle_event(event):
                        button_handled = True
                        break
            
            # 处理主要控制按钮
            if not button_handled:
                if self.generate_button.handle_event(event):
                    button_handled = True
                elif self.continue_button.handle_event(event):
                    button_handled = True
                elif self.reset_button.handle_event(event):
                    button_handled = True
            
            # 处理全屏触摸（在等待交互状态）
            if not button_handled and self.current_state == ExhibitionState.WAITING_INTERACTION:
                if event.type == pygame.MOUSEBUTTONUP or event.type == pygame.FINGERUP:
                    self.on_continue_click()
                    button_handled = True
        
        return True
    
    def draw(self):
        """绘制界面"""
        # 清屏
        self.screen.fill(COLORS['background'])
        
        # 绘制标题
        title = self.fonts['large'].render("Obscura No.7 虚拟望远镜", True, COLORS['primary'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=20)
        self.screen.blit(title, title_rect)
        
        # 绘制状态信息
        state_text = self.current_state.value.replace('_', ' ').title()
        state_surface = self.fonts['normal'].render(f"状态: {state_text}", True, COLORS['secondary'])
        self.screen.blit(state_surface, (50, 60))
        
        # 根据状态绘制不同内容
        if self.current_state == ExhibitionState.CITY_SELECTION:
            self.draw_city_selection()
        elif self.current_state == ExhibitionState.PARAMETER_INPUT:
            self.draw_parameter_input()
        elif self.current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
            self.draw_confirmation()
        elif self.current_state == ExhibitionState.PROCESSING:
            self.draw_processing()
        elif self.current_state == ExhibitionState.RESULT_DISPLAY:
            self.draw_result_display()
        elif self.current_state == ExhibitionState.WAITING_INTERACTION:
            self.draw_waiting_interaction()
        elif self.current_state == ExhibitionState.ERROR:
            self.draw_error()
        else:
            # 默认状态显示
            self.draw_default()
        
        # 绘制调试信息
        if self.debug_mode:
            self.draw_debug_info()
    
    def draw_city_selection(self):
        """绘制城市选择界面"""
        instruction = self.fonts['normal'].render("请选择一个城市:", True, COLORS['primary'])
        self.screen.blit(instruction, (50, 200))
        
        for button in self.city_buttons:
            button.draw(self.screen)
    
    def draw_parameter_input(self):
        """绘制参数输入界面"""
        # 绘制参数显示
        self.distance_display.draw(self.screen)
        self.angle_display.draw(self.screen)
        self.time_display.draw(self.screen)
        
        # 绘制说明
        instruction = self.fonts['normal'].render("调整参数后点击生成艺术", True, COLORS['primary'])
        instruction_rect = instruction.get_rect(centerx=SCREEN_WIDTH // 2, y=200)
        self.screen.blit(instruction, instruction_rect)
        
        # 绘制生成按钮
        self.generate_button.draw(self.screen)
        self.reset_button.draw(self.screen)
    
    def draw_confirmation(self):
        """绘制数据获取确认界面"""
        confirmation_text = self.fonts['large'].render("确认参数并开始处理?", True, COLORS['primary'])
        confirmation_rect = confirmation_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(confirmation_text, confirmation_rect)
        
        # 显示当前参数
        if self.context:
            params_text = f"距离: {self.context.distance_km:.1f}km  方向: {self.context.angle_degrees:.0f}°  时间: +{self.context.time_offset_years}年"
            params_surface = self.fonts['normal'].render(params_text, True, COLORS['secondary'])
            params_rect = params_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            self.screen.blit(params_surface, params_rect)
        
        self.generate_button.draw(self.screen)
        self.reset_button.draw(self.screen)
    
    def draw_result_display(self):
        """绘制结果显示界面"""
        result_text = self.fonts['large'].render("图像生成完成!", True, COLORS['success'])
        result_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(result_text, result_rect)
        
        # 如果有生成的图像，显示缩略图
        if self.context and self.context.generated_image_path:
            info_text = f"图像已保存: {self.context.generated_image_path}"
            info_surface = self.fonts['normal'].render(info_text[:60] + "...", True, COLORS['secondary'])
            info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(info_surface, info_rect)
        
        continue_text = self.fonts['normal'].render("即将切换到交互模式...", True, COLORS['secondary'])
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_error(self):
        """绘制错误状态界面"""
        error_text = self.fonts['large'].render("系统错误", True, COLORS['error'])
        error_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(error_text, error_rect)
        
        if self.context and self.context.error_message:
            # 显示错误消息（截断长消息）
            error_msg = self.context.error_message[:80] + "..." if len(self.context.error_message) > 80 else self.context.error_message
            msg_surface = self.fonts['normal'].render(error_msg, True, COLORS['error'])
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            self.screen.blit(msg_surface, msg_rect)
        
        # 显示重置提示
        reset_hint = self.fonts['normal'].render("系统将自动重置...", True, COLORS['secondary'])
        reset_rect = reset_hint.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(reset_hint, reset_rect)
        
        self.reset_button.draw(self.screen)
    
    def draw_default(self):
        """绘制默认状态界面"""
        default_text = self.fonts['large'].render("系统准备中...", True, COLORS['primary'])
        default_rect = default_text.get_rect(center=(SCREEN_WIDTH // 2, 240))
        self.screen.blit(default_text, default_rect)
    
    def draw_processing(self):
        """绘制处理中界面"""
        processing_text = self.fonts['large'].render("正在处理...", True, COLORS['primary'])
        processing_rect = processing_text.get_rect(center=(SCREEN_WIDTH // 2, 240))
        self.screen.blit(processing_text, processing_rect)
        
        # 简单的进度动画
        angle = (time.time() * 180) % 360
        center = (SCREEN_WIDTH // 2, 300)
        end_x = center[0] + 30 * math.cos(math.radians(angle))
        end_y = center[1] + 30 * math.sin(math.radians(angle))
        pygame.draw.line(self.screen, COLORS['accent'], center, (end_x, end_y), 5)
    
    def draw_waiting_interaction(self):
        """绘制等待交互界面"""
        # 绘制继续按钮（带脉冲效果）
        pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7
        
        waiting_text = self.fonts['large'].render("生成完成!", True, COLORS['success'])
        waiting_rect = waiting_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(waiting_text, waiting_rect)
        
        self.continue_button.draw(self.screen)
        self.reset_button.draw(self.screen)
    
    def draw_debug_info(self):
        """绘制调试信息"""
        debug_y = 10
        
        # 当前时间
        current_time = time.strftime("%H:%M:%S")
        time_text = self.fonts['debug'].render(f"时间: {current_time}", True, COLORS['debug'])
        self.screen.blit(time_text, (SCREEN_WIDTH - 150, debug_y))
        debug_y += 20
        
        # 最近的事件
        events_text = self.fonts['debug'].render("最近事件:", True, COLORS['debug'])
        self.screen.blit(events_text, (SCREEN_WIDTH - 150, debug_y))
        debug_y += 20
        
        # self.debug_events = self.debug_events[-5:] # Original line commented out
        for event_time, event_info in self.debug_events[-5:]:  # 显示最近5个事件
            age = time.time() - event_time
            if age < 10.0:  # 只显示10秒内的事件
                event_text = self.fonts['debug'].render(f"{event_info[:20]}...", True, COLORS['debug'])
                self.screen.blit(event_text, (SCREEN_WIDTH - 150, debug_y))
                debug_y += 15
        
        # 按键提示
        help_text = self.fonts['debug'].render("按D切换调试", True, COLORS['debug'])
        self.screen.blit(help_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))
    
    def run_frame(self) -> bool:
        """运行一帧"""
        if not self.handle_events():
            return False
        
        self.draw()
        pygame.display.flip()
        self.clock.tick(60)
        
        return True
    
    def quit(self):
        """退出"""
        self.running = False
        pygame.quit()
        self.logger.info("Enhanced pygame interface terminated")

    def _on_city_london(self):
        """伦敦按钮回调"""
        self.on_city_selected("London") if self.on_city_selected else None
    
    def _on_city_edinburgh(self):
        """爱丁堡按钮回调"""
        self.on_city_selected("Edinburgh") if self.on_city_selected else None
    
    def _on_city_manchester(self):
        """曼彻斯特按钮回调"""
        self.on_city_selected("Manchester") if self.on_city_selected else None
    
    def _on_generate(self):
        """生成按钮回调"""
        self.on_generate_click() if self.on_generate_click else None
    
    def _on_continue(self):
        """继续按钮回调"""
        self.on_continue_click() if self.on_continue_click else None
    
    def _on_reset(self):
        """重置按钮回调"""
        self.on_reset_click() if self.on_reset_click else None

    def create_touch_calibration_test(self):
        """创建触摸校准测试界面"""
        calibration_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        calibration_surface.fill(COLORS['background'])
        
        # 绘制校准说明
        title = self.fonts['large'].render("触摸校准测试", True, COLORS['primary'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=50)
        calibration_surface.blit(title, title_rect)
        
        # 绘制校准目标点
        test_points = [
            (100, 150),    # 左上
            (SCREEN_WIDTH - 100, 150),  # 右上
            (100, SCREEN_HEIGHT - 150), # 左下
            (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 150), # 右下
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),   # 中心
        ]
        
        for i, (x, y) in enumerate(test_points):
            # 绘制目标圆圈
            pygame.draw.circle(calibration_surface, COLORS['accent'], (x, y), 30, 3)
            pygame.draw.circle(calibration_surface, COLORS['primary'], (x, y), 5)
            
            # 绘制编号
            number = self.fonts['medium'].render(str(i + 1), True, COLORS['primary'])
            number_rect = number.get_rect(center=(x, y + 50))
            calibration_surface.blit(number, number_rect)
        
        return calibration_surface
    
    def log_touch_event(self, event_type, original_pos, calibrated_pos, hit_target=None):
        """记录触摸事件用于调试"""
        timestamp = time.time()
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'original_pos': original_pos,
            'calibrated_pos': calibrated_pos,
            'hit_target': hit_target
        }
        self.touch_events_log.append(log_entry)
        
        # 只保留最近20个事件
        if len(self.touch_events_log) > 20:
            self.touch_events_log = self.touch_events_log[-20:]
        
        # 调试输出
        if self.debug_mode:
            print(f"📍 {event_type}: {original_pos} → {calibrated_pos}")

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    interface = EnhancedPygameInterface(fullscreen=False)
    
    def test_callback(event_name):
        def callback(*args):
            print(f"回调触发: {event_name} {args}")
        return callback
    
    interface.set_callback('on_city_selected', test_callback('城市选择'))
    interface.set_callback('on_generate_click', test_callback('生成点击'))
    interface.set_callback('on_continue_click', test_callback('继续点击'))
    interface.set_callback('on_reset_click', test_callback('重置点击'))
    
    print("增强界面测试运行中...")
    print("按ESC退出，按D切换调试显示")
    
    while interface.running:
        if not interface.run_frame():
            break
    
    interface.quit() 