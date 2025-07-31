"""
Pygame Interface for Obscura No.7 Virtual Telescope Exhibition Mode
Designed for HyperPixel 4.0 touchscreen (800x480) on Raspberry Pi.

Features:
- Parameter visualization (distance, angle, time offset)
- Touch-friendly data fetch button
- Full-screen image display
- Touch to continue interaction
- State-based UI rendering
- Scientific time eye animation for future prediction
"""

import pygame
import sys
import math
import os
from typing import Tuple, Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import logging

from .exhibition_state_machine import ExhibitionState, StateContext
from .time_eye_animation import TimeEyeAnimation

# Initialize Pygame
pygame.init()

# Display configuration for HyperPixel 4.0
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
DISPLAY_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Steampunk Color Palette
COLORS = {
    'background': (45, 35, 25),        # Dark brown background
    'primary': (255, 235, 200),        # Warm cream text
    'secondary': (180, 150, 120),      # Muted bronze
    'accent': (200, 140, 60),          # Brass/copper
    'button': (80, 60, 40),            # Dark bronze button
    'button_hover': (120, 90, 60),     # Lighter bronze hover
    'button_active': (160, 120, 80),   # Active brass
    'city_button': (100, 70, 40),      # City button
    'city_hover': (140, 100, 60),      # City hover
    'city_active': (180, 140, 90),     # City active
    'gear': (160, 120, 70),            # Gear color
    'steam': (220, 220, 220),          # Steam white
    'copper': (184, 115, 51),          # Copper pipes
    'error': (180, 50, 50),            # Muted red
    'success': (120, 180, 80),         # Steampunk green
    'warning': (200, 160, 50),         # Brass warning
    'transparent': (0, 0, 0, 0)        # Transparent
}

# Font sizes - 针对HyperPixel模糊显示进行优化，大幅增加字体大小
FONT_SIZES = {
    'title': 48,        # 从32增加到48 (+50%)
    'subtitle': 36,     # 从24增加到36 (+50%)
    'normal': 28,       # 从18增加到28 (+55%)
    'small': 22,        # 从14增加到22 (+57%)
    'large': 42         # 从28增加到42 (+50%)
}

class ButtonState(Enum):
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"

class Button:
    """Touch-friendly button widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, font_size: int = FONT_SIZES['normal'], 
                 button_type: str = 'normal'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        # 使用加粗字体提升按钮文字可读性
        try:
            self.font = pygame.font.SysFont('arial', font_size, bold=True)
        except:
            self.font = pygame.font.Font(None, font_size)
        self.state = ButtonState.NORMAL
        self.enabled = True
        self.callback = None
        self.button_type = button_type  # 'normal', 'city'
        
    def set_callback(self, callback: Callable):
        """Set callback function for button click"""
        self.callback = callback
    
    def handle_event(self, event) -> bool:
        """Handle mouse/touch events. Returns True if button was clicked."""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = ButtonState.PRESSED
                return False
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.state == ButtonState.PRESSED and self.rect.collidepoint(event.pos):
                self.state = ButtonState.NORMAL
                if self.callback:
                    self.callback()
                return True
            self.state = ButtonState.NORMAL
        
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos) and self.state != ButtonState.PRESSED:
                self.state = ButtonState.HOVER
            elif not self.rect.collidepoint(event.pos) and self.state != ButtonState.PRESSED:
                self.state = ButtonState.NORMAL
        
        return False
    
    def draw(self, surface):
        """Draw the button with steampunk styling"""
        # Choose color based on button type and state
        if self.button_type == 'city':
            if not self.enabled:
                color = COLORS['secondary']
            elif self.state == ButtonState.PRESSED:
                color = COLORS['city_active']
            elif self.state == ButtonState.HOVER:
                color = COLORS['city_hover']
            else:
                color = COLORS['city_button']
        else:
            if not self.enabled:
                color = COLORS['secondary']
            elif self.state == ButtonState.PRESSED:
                color = COLORS['button_active']
            elif self.state == ButtonState.HOVER:
                color = COLORS['button_hover']
            else:
                color = COLORS['button']
        
        # Draw button with rounded corners (steampunk style)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        # Draw brass border
        border_color = COLORS['accent'] if self.enabled else COLORS['secondary']
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=8)
        
        # Add subtle inner shadow effect
        inner_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, 
                                self.rect.width - 4, self.rect.height - 4)
        pygame.draw.rect(surface, (0, 0, 0, 30), inner_rect, border_radius=6)
        
        # Draw text
        text_color = COLORS['primary'] if self.enabled else COLORS['secondary']
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class CircularKnob:
    """Circular parameter display (like a knob or dial)"""
    
    def __init__(self, x: int, y: int, radius: int, 
                 min_value: float, max_value: float, 
                 current_value: float, label: str):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.label = label
        # 增大字体尺寸，让数值和标签更清晰可读
        self.font = pygame.font.Font(None, FONT_SIZES['large'])  # 数值用大字体
        self.small_font = pygame.font.Font(None, FONT_SIZES['large'])  # 标签也改为大字体，让Distance/Angle/Time Offset更显眼
    
    def set_value(self, value: float):
        """Update the current value with circular wrapping logic"""
        # 循环逻辑：当超过最大值时，从最小值重新开始
        value_range = self.max_value - self.min_value
        if value > self.max_value:
            # 超过最大值，计算循环后的位置
            excess = value - self.max_value
            wrapped_value = self.min_value + (excess % value_range)
            self.current_value = wrapped_value
        elif value < self.min_value:
            # 低于最小值，从最大值向下循环
            deficit = self.min_value - value
            wrapped_value = self.max_value - (deficit % value_range)
            self.current_value = wrapped_value
        else:
            # 在正常范围内
            self.current_value = value
    
    def draw(self, surface):
        """Draw the circular knob"""
        # Draw outer circle
        pygame.draw.circle(surface, COLORS['accent'], 
                         (self.center_x, self.center_y), self.radius, 3)
        
        # Calculate angle for current value - 360度循环逻辑
        normalized_value = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        # 使用360度范围，-90度开始（12点方向），顺时针旋转
        angle = -90 + (normalized_value * 360)  # -90度到270度，完整360度范围
        angle_rad = math.radians(angle)
        
        # Draw indicator line
        end_x = self.center_x + (self.radius - 10) * math.cos(angle_rad)
        end_y = self.center_y + (self.radius - 10) * math.sin(angle_rad)
        pygame.draw.line(surface, COLORS['primary'], 
                        (self.center_x, self.center_y), (end_x, end_y), 4)
        
        # Draw center dot
        pygame.draw.circle(surface, COLORS['primary'], 
                         (self.center_x, self.center_y), 8)
        
        # Draw value text - 增加数值显示的醒目度
        value_text = f"{self.current_value:.1f}"
        if self.label == "Time Offset (y)":
            value_text = f"{int(self.current_value)}"
        
        # 使用更醒目的颜色和粗体效果
        text_surface = self.font.render(value_text, True, COLORS['primary'])
        # 绘制文本阴影增加对比度
        shadow_surface = self.font.render(value_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(self.center_x + 2, self.center_y + self.radius + 35))  # 从27增加到35
        surface.blit(shadow_surface, shadow_rect)
        
        text_rect = text_surface.get_rect(center=(self.center_x, self.center_y + self.radius + 33))  # 从25增加到33
        surface.blit(text_surface, text_rect)
        
        # Draw label - 标签颜色和字体调整，更显眼，增加与数值的距离
        label_surface = self.small_font.render(self.label, True, COLORS['primary'])  # 从accent改为primary，使用白色更显眼
        # 绘制标签阴影
        label_shadow = self.small_font.render(self.label, True, (0, 0, 0))
        label_shadow_rect = label_shadow.get_rect(center=(self.center_x + 1, self.center_y + self.radius + 60))  # 从46增加到60，增加间距
        surface.blit(label_shadow, label_shadow_rect)
        
        label_rect = label_surface.get_rect(center=(self.center_x, self.center_y + self.radius + 58))  # 从45增加到58，增加间距
        surface.blit(label_surface, label_rect)

class ProgressBar:
    """Progress bar for processing state"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.progress = 0.0  # 0.0 to 1.0
        self.animated = True
        self.animation_offset = 0
        
    def set_progress(self, progress: float):
        """Set progress value (0.0 to 1.0)"""
        self.progress = max(0.0, min(1.0, progress))
    
    def update_animation(self, dt: float):
        """Update animation (call in main loop)"""
        if self.animated:
            self.animation_offset += dt * 2  # Animation speed
            if self.animation_offset > 1.0:
                self.animation_offset = 0.0
    
    def draw(self, surface):
        """Draw the progress bar"""
        # Draw background
        pygame.draw.rect(surface, COLORS['secondary'], self.rect)
        pygame.draw.rect(surface, COLORS['primary'], self.rect, 2)
        
        # Draw progress fill
        if self.progress > 0:
            fill_width = int(self.rect.width * self.progress)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, COLORS['accent'], fill_rect)
            
            # Animated shimmer effect
            if self.animated and fill_width > 20:
                shimmer_x = self.rect.x + (self.animation_offset * (fill_width - 20))
                shimmer_rect = pygame.Rect(shimmer_x, self.rect.y, 20, self.rect.height)
                pygame.draw.rect(surface, COLORS['primary'], shimmer_rect)

class PygameInterface:
    """Main interface manager for the exhibition mode"""
    
    def __init__(self, fullscreen: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # 确保pygame字体系统正确初始化 - 防止 "font not initialized" 错误
        pygame.font.init()
        
        # Initialize display
        if fullscreen:
            self.screen = pygame.display.set_mode(DISPLAY_SIZE, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(DISPLAY_SIZE)
        
        pygame.display.set_caption("Obscura No.7 Virtual Telescope")
        
        # Hide mouse cursor in fullscreen mode
        if fullscreen:
            pygame.mouse.set_visible(False)
        
        # Initialize fonts - 使用加粗字体提升模糊屏幕可读性
        self.fonts = {}
        for size_name, size in FONT_SIZES.items():
            try:
                # 尝试使用系统字体并设置为粗体
                self.fonts[size_name] = pygame.font.SysFont('arial', size, bold=True)
                self.logger.info(f"字体 '{size_name}' 使用Arial粗体 {size}px")
            except pygame.error:
                try:
                    # 回退：使用默认字体
                    self.fonts[size_name] = pygame.font.Font(None, size)
                    self.logger.warning(f"字体 '{size_name}' 使用默认字体 {size}px")
                except pygame.error:
                    # 最终回退
                    self.fonts[size_name] = pygame.font.SysFont(None, size)
                    self.logger.warning(f"字体 '{size_name}' 使用系统默认字体 {size}px")
        
        # Initialize UI elements
        self._init_ui_elements()
        
        # State management
        self.current_state = ExhibitionState.CITY_SELECTION
        self.context = None
        self.available_cities = {}
        
        # Animation and timing
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
        
        # Image display
        self.current_image = None
        self.image_rect = None
        
        # Callbacks
        self.callbacks = {
            'on_city_selected': None,
            'on_data_fetch_click': None,
            'on_touch_continue': None,
            'on_reset_request': None,
            'on_parameter_change': None
        }
        
        # Initialize time eye animation
        # self.time_eye_animation = TimeEyeAnimation(SCREEN_WIDTH, SCREEN_HEIGHT)
        # 改为动态创建，以便传递实时的location和time信息
        self.time_eye_animation = None
        
        self.logger.info("Pygame interface initialized")
    
    def _init_ui_elements(self):
        """Initialize UI elements"""
        # Parameter knobs - 上移位置，从220调整到180
        self.distance_knob = CircularKnob(150, 180, 90, 1.0, 50.0, 1.0, "Distance (km)")
        self.angle_knob = CircularKnob(400, 180, 90, 0.0, 360.0, 0.0, "Angle (°)")
        self.time_knob = CircularKnob(650, 180, 90, -50.0, 50.0, -50.0, "Time Offset (y)")
        
        # City selection buttons - 调整尺寸和位置，增大宽度适应Manchester，整体向左移动
        self.city_buttons = {}
        city_names = ["London", "Edinburgh", "Manchester"]
        button_width = 240  # 从220增加到240，为Manchester提供更多空间
        button_height = 100  # 保持100不变
        button_spacing = 40  # 保持40不变
        # 计算总宽度：240*3 + 40*2 = 720 + 80 = 800px，正好填满屏幕
        # 向左平移：减少start_x的值，让按钮组整体左移
        calculated_start_x = (SCREEN_WIDTH - (len(city_names) * button_width + (len(city_names)-1) * button_spacing)) // 2
        start_x = calculated_start_x - 15  # 向左平移15像素
        
        for i, city in enumerate(city_names):
            x = start_x + i * (button_width + button_spacing)
            y = 200
            button = Button(x, y, button_width, button_height, city, 
                          FONT_SIZES['large'], 'city')
            button.set_callback(lambda c=city: self._on_city_selected(c))
            self.city_buttons[city] = button
        
        # Main control buttons - 扩大PREDICT THE FUTURE按钮完全包裹文字
        self.fetch_button = Button(170, 380, 460, 120, "PREDICT THE FUTURE", FONT_SIZES['large'])  # 宽度从420增加到460，X从190调整到170居中
        self.fetch_button.set_callback(self._on_fetch_button_click)
        
        # 其他按钮位置调整
        self.continue_button = Button(250, 420, 300, 90, "TOUCH TO CONTINUE", FONT_SIZES['normal'])
        self.continue_button.set_callback(self._on_continue_button_click)
        
        # Reset按钮 - 进一步缩小尺寸，让整体构图更协调
        self.reset_button = Button(20, 350, 130, 50, "RESET", FONT_SIZES['normal'])  # 从(20,350,150,60)调整为(20,350,130,50)
        self.reset_button.set_callback(self._on_reset_button_click)
        
        # Progress bar - 增大尺寸50%，width从400增加到600，height从30增加到45
        self.progress_bar = ProgressBar(100, 260, 600, 45)
        
        # UI element lists for easy management
        self.buttons = [self.fetch_button, self.continue_button, self.reset_button]
        self.knobs = [self.distance_knob, self.angle_knob, self.time_knob]
    
    def set_callback(self, event: str, callback: Callable):
        """Set callback function for specific events"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"Unknown callback event: {event}")
    
    def _on_city_selected(self, city_name: str):
        """Handle city selection"""
        if self.callbacks['on_city_selected']:
            self.callbacks['on_city_selected'](city_name)

    def _on_fetch_button_click(self):
        """Handle fetch button click"""
        if self.callbacks['on_data_fetch_click']:
            self.callbacks['on_data_fetch_click']()
    
    def _on_continue_button_click(self):
        """Handle continue button click"""
        if self.callbacks['on_touch_continue']:
            self.callbacks['on_touch_continue']()
    
    def _on_reset_button_click(self):
        """Handle reset button click"""
        if self.callbacks['on_reset_request']:
            self.callbacks['on_reset_request']()
    
    def update_state(self, state: ExhibitionState, context: StateContext):
        """Update the interface based on current state"""
        self.current_state = state
        self.context = context
        
        # Update knob values from context
        if context:
            self.distance_knob.set_value(context.distance_km)
            self.angle_knob.set_value(context.angle_degrees)
            self.time_knob.set_value(context.time_offset_years)
        
        # Update button states based on current state
        self.fetch_button.enabled = (state in [ExhibitionState.PARAMETER_INPUT, ExhibitionState.DATA_FETCH_CONFIRMATION])
        self.continue_button.enabled = (state == ExhibitionState.WAITING_INTERACTION)
        self.reset_button.enabled = (state not in [ExhibitionState.PROCESSING])
    
    def load_image(self, image_path: str) -> bool:
        """Load and scale image for display"""
        try:
            if os.path.exists(image_path):
                # Load image
                self.current_image = pygame.image.load(image_path)
                
                # Scale to fit screen while maintaining aspect ratio
                image_rect = self.current_image.get_rect()
                screen_rect = self.screen.get_rect()
                
                # Calculate scaling factor
                scale_x = screen_rect.width / image_rect.width
                scale_y = screen_rect.height / image_rect.height
                scale = min(scale_x, scale_y)
                
                # Scale image
                new_width = int(image_rect.width * scale)
                new_height = int(image_rect.height * scale)
                self.current_image = pygame.transform.scale(self.current_image, (new_width, new_height))
                
                # Center image
                self.image_rect = self.current_image.get_rect(center=screen_rect.center)
                
                self.logger.info(f"Image loaded and scaled: {image_path}")
                return True
            else:
                self.logger.error(f"Image file not found: {image_path}")
                return False
        except Exception as e:
            self.logger.error(f"Error loading image {image_path}: {e}")
            return False
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    self._on_reset_button_click()
            
            # Handle button events - 确保按钮事件被正确处理
            button_handled = False
            
            # Handle city button events first
            for button in self.city_buttons.values():
                if button.handle_event(event):
                    button_handled = True
                    break
            
            # Handle other buttons if no city button was clicked
            if not button_handled:
                for button in self.buttons:
                    if button.handle_event(event):
                        button_handled = True
                        break  # Only one button should be clicked at a time
            
            # 移除全屏触摸继续逻辑 - 修复用户报告的问题
            # 现在只有点击"Touch to continue"按钮才会触发返回事件
            # 这解决了"随意点击屏幕都会触发返回事件"的问题
        
        return True
    
    def update(self, dt: float):
        """Update interface animations and state"""
        # Update progress bar animation
        self.progress_bar.update_animation(dt)
        
        # Update progress based on state
        if self.current_state == ExhibitionState.PROCESSING:
            # 动态创建或更新时间之眼动画，传递最新的location和future_time信息
            if self.time_eye_animation is None:
                location_info = self._get_location_display_text()
                future_time = self._get_future_time_display_text()
                self.time_eye_animation = TimeEyeAnimation(SCREEN_WIDTH, SCREEN_HEIGHT, location_info, future_time)
            
            # 使用科技动感版"时间之眼"动效替代旧的进度条
            # 更新动画状态
            dt = self.clock.get_time() / 1000.0  # 转换为秒
            self.time_eye_animation.update(dt)
            
            # 绘制时间之眼动效（全屏黑色背景 + 动画）
            self.time_eye_animation.draw(self.screen)
        else:
            # 其他状态时清除动画对象
            self.time_eye_animation = None
            self.progress_bar.set_progress(0.0)
    
    def draw(self):
        """Draw the interface"""
        # 特殊处理：PROCESSING状态使用全屏时间之眼动效
        if self.current_state == ExhibitionState.PROCESSING:
            # 确保动画对象存在
            if self.time_eye_animation is None:
                location_info = self._get_location_display_text()
                future_time = self._get_future_time_display_text()
                self.time_eye_animation = TimeEyeAnimation(SCREEN_WIDTH, SCREEN_HEIGHT, location_info, future_time)
            
            # 更新动画状态
            dt = self.clock.get_time() / 1000.0  # 转换为秒
            self.time_eye_animation.update(dt)
            
            # 绘制时间之眼动效（包含全黑背景）
            self.time_eye_animation.draw(self.screen)
            
            # 只绘制状态指示器，不绘制其他元素
            self._draw_state_indicator()
        else:
            # 其他状态的正常绘制流程
            # Clear screen
            self.screen.fill(COLORS['background'])
            
            # Draw steampunk background elements
            self._draw_steampunk_background()
            
            if self.current_state == ExhibitionState.CITY_SELECTION:
                self._draw_city_selection()
            elif self.current_state == ExhibitionState.RESULT_DISPLAY:
                self._draw_result_display()
            elif self.current_state == ExhibitionState.WAITING_INTERACTION:
                self._draw_waiting_interaction()
            else:
                self._draw_main_interface()
            
            # Always draw current state indicator in top-right corner
            self._draw_state_indicator()
        
        # Update display
        pygame.display.flip()

    def _draw_steampunk_background(self):
        """Draw steampunk-style background elements"""
        # Draw copper pipes - 增大管道宽度50%，从8像素增加到12像素
        pipe_color = COLORS['copper']
        # Horizontal pipes
        pygame.draw.rect(self.screen, pipe_color, (0, 100, SCREEN_WIDTH, 12))
        pygame.draw.rect(self.screen, pipe_color, (0, 350, SCREEN_WIDTH, 12))
        # Vertical pipes
        pygame.draw.rect(self.screen, pipe_color, (100, 0, 12, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, pipe_color, (SCREEN_WIDTH-108, 0, 12, SCREEN_HEIGHT))
        
        # Draw gears - 增大齿轮半径50%，从25增加到38
        gear_color = COLORS['gear']
        # Corner gears
        pygame.draw.circle(self.screen, gear_color, (80, 80), 38, 5)
        pygame.draw.circle(self.screen, gear_color, (SCREEN_WIDTH-80, 80), 38, 5)
        pygame.draw.circle(self.screen, gear_color, (80, SCREEN_HEIGHT-80), 38, 5)
        pygame.draw.circle(self.screen, gear_color, (SCREEN_WIDTH-80, SCREEN_HEIGHT-80), 38, 5)
        
        # Gear teeth (simple lines) - 增大齿轮齿尺寸50%
        for gear_pos in [(80, 80), (SCREEN_WIDTH-80, 80), (80, SCREEN_HEIGHT-80), (SCREEN_WIDTH-80, SCREEN_HEIGHT-80)]:
            for angle in range(0, 360, 45):
                x = gear_pos[0] + 45 * math.cos(math.radians(angle))  # 从30增加到45 (+50%)
                y = gear_pos[1] + 45 * math.sin(math.radians(angle))  # 从30增加到45 (+50%)
                pygame.draw.line(self.screen, gear_color, gear_pos, (x, y), 3)  # 线条宽度从2增加到3

    def _draw_city_selection(self):
        """Draw city selection interface"""
        # Title - 位置稍微下移以适应更大字体
        title_text = self.fonts['title'].render("OBSCURA No.7", True, COLORS['primary'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 60))  # 从50增加到60
        self.screen.blit(title_text, title_rect)
        
        # Subtitle - 调整颜色和位置，避免与背景重叠，添加背景增强可读性
        subtitle_text = self.fonts['subtitle'].render("Virtual Time-Space Telescope", True, COLORS['primary'])  # 改为主色调
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 105))  # 从85增加到105
        
        # 为副标题添加背景，增强可读性
        bg_rect = subtitle_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (*COLORS['background'], 180), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS['accent'], bg_rect, 2, border_radius=5)
        
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Instructions - 位置下移以适应更大的标题，调整颜色增强对比度
        instruction_text = self.fonts['normal'].render("Select a destination city for your temporal exploration:", True, COLORS['primary'])  # 改为主色调
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 160))  # 从170调整到160，上移一点
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw city buttons
        for button in self.city_buttons.values():
            button.draw(self.screen)
        
        # Draw selected city info if any - 位置下移
        if self.context and self.context.selected_city:
            selected_text = self.fonts['normal'].render(f"Selected: {self.context.selected_city}", True, COLORS['success'])
            selected_rect = selected_text.get_rect(center=(SCREEN_WIDTH // 2, 360))  # 从340增加到360，为按钮让出空间
            self.screen.blit(selected_text, selected_rect)
        
        # Draw decorative steam
        self._draw_steam_effects()

    def _draw_steam_effects(self):
        """Draw decorative steam effects"""
        steam_color = COLORS['steam']
        # Simple steam puffs - draw as small dots/circles
        for i in range(5):
            x = 100 + i * 150
            y = 380 + (i % 3) * 15
            # Draw small steam dots
            pygame.draw.circle(self.screen, steam_color, (x, y), 3)
            pygame.draw.circle(self.screen, steam_color, (x-5, y-8), 2)
            pygame.draw.circle(self.screen, steam_color, (x+3, y-5), 2)
    
    def _draw_main_interface(self):
        """Draw the main parameter interface"""
        # Title - 向上移动避免与旋钮重叠
        title_text = self.fonts['title'].render("OBSCURA No.7", True, COLORS['primary'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 35))  # 从50上移到35
        self.screen.blit(title_text, title_rect)
        
        # 删除副标题"Temporal Environmental Observatory"，为其他控件提供更多空间
        
        # Show selected city - 向上移动避免与旋钮重叠
        if self.context and self.context.selected_city:
            city_text = self.fonts['large'].render(f"Destination: {self.context.selected_city}", True, COLORS['success'])  # 从normal改为large
            city_rect = city_text.get_rect(center=(SCREEN_WIDTH // 2, 70))  # 从85上移到70
            self.screen.blit(city_text, city_rect)
        
        # Draw parameter knobs - 旋钮会通过_init_ui_elements中的位置调整来上移
        for knob in self.knobs:
            knob.draw(self.screen)
        
        # Draw buttons based on state
        if self.current_state == ExhibitionState.PARAMETER_INPUT:
            # 删除"Adjust parameters using hardware encoders"说明文字
            pass
            
            # Show generate art button
            self.fetch_button.draw(self.screen)
        
        elif self.current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
            self.fetch_button.draw(self.screen)
        
        # PROCESSING状态现在在draw()方法中独立处理，不在这里处理
        
        elif self.current_state == ExhibitionState.ERROR:
            # Show error message
            error_text = self.fonts['large'].render("ERROR", True, COLORS['error'])
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(error_text, error_rect)
            
            if self.context and self.context.error_message:
                error_msg = self.fonts['normal'].render(
                    self.context.error_message, True, COLORS['error'])
                error_msg_rect = error_msg.get_rect(center=(SCREEN_WIDTH // 2, 230))
                self.screen.blit(error_msg, error_msg_rect)
        
        # Always show reset button in main interface
        self.reset_button.draw(self.screen)
    
    def _draw_result_display(self):
        """Draw the result display with generated image"""
        if self.current_image and self.image_rect:
            # Fill background with dark color
            self.screen.fill(COLORS['background'])
            
            # Draw the generated image
            self.screen.blit(self.current_image, self.image_rect)
            
            # Draw title overlay
            title_text = self.fonts['subtitle'].render("Generated View", True, COLORS['primary'])
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            # Add semi-transparent background for text
            pygame.draw.rect(self.screen, (*COLORS['background'], 180), 
                           title_rect.inflate(20, 10))
            self.screen.blit(title_text, title_rect)
        else:
            # Fallback if no image is loaded
            self._draw_main_interface()
            no_image_text = self.fonts['large'].render("No Image Available", True, COLORS['error'])
            no_image_rect = no_image_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(no_image_text, no_image_rect)
    
    def _draw_waiting_interaction(self):
        """Draw the waiting for interaction screen"""
        # Show the image with touch prompt
        if self.current_image and self.image_rect:
            self.screen.blit(self.current_image, self.image_rect)
        
        # Draw touch prompt with pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.003)) * 0.3 + 0.7
        touch_color = tuple(int(c * pulse) for c in COLORS['primary'])
        
        touch_text = self.fonts['large'].render("TOUCH TO CONTINUE", True, touch_color)
        touch_rect = touch_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        
        # Add background for text
        bg_rect = touch_rect.inflate(40, 20)
        pygame.draw.rect(self.screen, (*COLORS['background'], 180), bg_rect)
        pygame.draw.rect(self.screen, touch_color, bg_rect, 3)
        
        self.screen.blit(touch_text, touch_rect)
    
    def _draw_state_indicator(self):
        """Draw current state indicator"""
        if self.context:
            state_text = self.current_state.value.replace('_', ' ').title()
            indicator_text = self.fonts['small'].render(state_text, True, COLORS['secondary'])
            indicator_rect = indicator_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
            self.screen.blit(indicator_text, indicator_rect)
    
    def run_frame(self) -> bool:
        """Run one frame of the interface. Returns False if should quit."""
        # Calculate delta time
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        self.last_time = current_time
        
        # Handle events
        if not self.handle_events():
            return False
        
        # Update
        self.update(dt)
        
        # Draw
        self.draw()
        
        # Cap framerate
        self.clock.tick(60)
        
        return True
    
    def quit(self):
        """Clean up and quit pygame"""
        pygame.quit()
        self.logger.info("Pygame interface shut down")

    def _get_location_display_text(self) -> str:
        """获取位置显示文本"""
        # 优先使用工作流获取的真实地址信息
        if (self.context and 
            hasattr(self.context, 'map_info') and 
            self.context.map_info and 
            self.context.map_info.get('success')):
            
            # 获取完整地址信息
            location_info = self.context.map_info.get('location_info', '')
            location_details = self.context.map_info.get('location_details', {})
            
            # 优先使用完整地址并智能简化
            if location_info:
                # 清理地址：移除邮编、国家后缀等
                simplified_address = location_info.replace('英国', '').replace('UK', '').replace('United Kingdom', '').strip()
                
                # 移除邮编（匹配英国邮编格式）
                import re
                simplified_address = re.sub(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b', '', simplified_address).strip()
                
                # 清理多余的逗号和空格
                simplified_address = re.sub(r',\s*,', ',', simplified_address)  # 连续逗号
                simplified_address = re.sub(r',\s*$', '', simplified_address)   # 末尾逗号
                simplified_address = simplified_address.strip(', ')
                
                # 如果地址太长，智能截取最重要的部分
                if len(simplified_address) > 35:
                    parts = [part.strip() for part in simplified_address.split(',')]
                    if len(parts) >= 2:
                        # 取前两个最重要的部分：通常是街道名和区域名
                        return f"{parts[0]}, {parts[1]}"
                    else:
                        return simplified_address[:35] + "..."
                
                return simplified_address
            
            # 如果完整地址不可用，尝试从详细组件构建
            if location_details:
                # 提取关键地址组件
                street_number = location_details.get('street_number', '')
                route = location_details.get('route', '')  # 街道名称
                locality = location_details.get('locality', '')  # 城市
                sublocality = location_details.get('sublocality', '')  # 子区域
                admin_area = location_details.get('administrative_area_level_1', '')  # 州/省
                
                # 构建显示文本：优先显示街道信息
                if street_number and route:
                    street_info = f"{street_number} {route}"
                    if locality:
                        return f"{street_info}, {locality}"
                    elif sublocality:
                        return f"{street_info}, {sublocality}"
                    elif admin_area:
                        return f"{street_info}, {admin_area}"
                    else:
                        return street_info
                elif route:
                    if locality:
                        return f"{route}, {locality}"
                    elif sublocality:
                        return f"{route}, {sublocality}"
                    elif admin_area:
                        return f"{route}, {admin_area}"
                    else:
                        return route
                elif sublocality and locality:
                    return f"{sublocality}, {locality}"
                elif locality:
                    return locality
        
        # 回退到默认的城市名称
        if self.context and self.context.selected_city:
            city = self.context.selected_city
            if city in {"London", "Edinburgh", "Manchester"}:
                # 添加简化的地理名称，更易读
                city_display_names = {
                    "London": "London, England",
                    "Edinburgh": "Edinburgh, Scotland", 
                    "Manchester": "Manchester, England"
                }
                if city in city_display_names:
                    return city_display_names[city]
            return city
        return "Unknown Location"
    
    def _get_future_time_display_text(self) -> str:
        """获取未来时间显示文本"""
        if self.context and hasattr(self.context, 'time_offset_years'):
            years_offset = self.context.time_offset_years
            if years_offset == 0:
                return "Present Time"
            elif years_offset > 0:
                return f"+{years_offset} years from now"
            else:
                return f"{abs(years_offset)} years ago"
        return "Unknown Time"

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create interface
    interface = PygameInterface(fullscreen=False)  # Windowed mode for testing
    
    # Example callback functions
    def on_data_fetch():
        print("Data fetch button clicked!")
    
    def on_touch_continue():
        print("Touch to continue!")
    
    def on_reset():
        print("Reset requested!")
    
    # Set callbacks
    interface.set_callback('on_data_fetch_click', on_data_fetch)
    interface.set_callback('on_touch_continue', on_touch_continue)
    interface.set_callback('on_reset_request', on_reset)
    
    # Simulate state changes
    from .exhibition_state_machine import StateContext
    
    context = StateContext()
    context.distance_km = 30.0
    context.angle_degrees = 45.0
    context.time_offset_years = -5
    
    interface.update_state(ExhibitionState.DATA_FETCH_CONFIRMATION, context)
    
    # Main loop
    running = True
    while running:
        running = interface.run_frame()
    
    interface.quit() 