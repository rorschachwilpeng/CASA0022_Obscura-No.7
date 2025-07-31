"""
Adaptive Pygame Interface for Obscura No.7 Virtual Telescope Exhibition Mode
Automatically adapts to any HyperPixel screen resolution.

Features:
- Dynamic resolution detection and adaptation
- Scalable UI elements and fonts
- Touch-friendly responsive design
- Full-screen optimization for exhibition mode
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

# Initialize Pygame
pygame.init()

class ScreenAdapter:
    """Handles dynamic screen adaptation for different HyperPixel models"""
    
    def __init__(self, force_landscape: bool = True, rotation_angle: int = 0):
        self.logger = logging.getLogger(__name__)
        self.force_landscape = force_landscape
        self.rotation_angle = rotation_angle  # 0, 90, 180, 270 degrees
        self.detect_screen_info()
        self.calculate_scale_factors()
        
    def detect_screen_info(self):
        """Detect actual screen resolution and capabilities"""
        try:
            # Get pygame display info
            info = pygame.display.Info()
            detected_width = info.current_w
            detected_height = info.current_h
            
            self.logger.info(f"🖥️ Pygame检测分辨率: {detected_width}x{detected_height}")
            
            # For HyperPixel screens, force correct physical dimensions
            # Many HyperPixel screens are physically 480x800 but pygame detects 800x480
            if (detected_width == 800 and detected_height == 480) or (detected_width == 480 and detected_height == 800):
                # This is likely a HyperPixel 4.0, force portrait physical orientation
                self.native_width = 480
                self.native_height = 800
                self.logger.info(f"🔧 强制HyperPixel物理尺寸: {self.native_width}x{self.native_height}")
            else:
                # Use detected dimensions for other screens
                self.native_width = detected_width
                self.native_height = detected_height
            
            # Virtual surface dimensions for UI layout (independent of rotation)
            if self.force_landscape:
                # Virtual surface should be landscape for UI layout
                self.display_width = 800
                self.display_height = 480
                self.logger.info(f"🔄 虚拟表面设为横屏布局: {self.display_width}x{self.display_height}")
            else:
                # Use detected dimensions as base
                self.display_width = detected_width
                self.display_height = detected_height
            
            # Rotation is handled in render_with_rotation(), not here
            
            # Common HyperPixel resolutions
            hyperpixel_configs = {
                (800, 480): "HyperPixel 4.0 (横屏)",
                (480, 800): "HyperPixel 4.0 (竖屏)",
                (720, 720): "HyperPixel 4.0 Square", 
                (640, 480): "HyperPixel 2.1",
                (480, 320): "HyperPixel 1.54"
            }
            
            resolution = (self.native_width, self.native_height)
            self.device_type = hyperpixel_configs.get(resolution, f"Custom {resolution[0]}x{resolution[1]}")
            
            if self.rotation_angle != 0:
                self.device_type += f" (旋转{self.rotation_angle}°)"
                
            self.logger.info(f"🎯 识别设备类型: {self.device_type}")
            self.logger.info(f"📱 物理屏幕: {self.native_width}x{self.native_height}")
            self.logger.info(f"🖼️ 虚拟表面: {self.display_width}x{self.display_height}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 屏幕检测失败，使用默认值: {e}")
            self.native_width = 480
            self.native_height = 800
            self.display_width = 800
            self.display_height = 480
            self.device_type = "Default"
    
    def calculate_scale_factors(self):
        """Calculate scaling factors for UI elements"""
        # Base design is for 800x480
        self.base_width = 800
        self.base_height = 480
        
        # Use display dimensions (which may be rotated) for scaling
        display_width = getattr(self, 'display_width', self.native_width)
        display_height = getattr(self, 'display_height', self.native_height)
        
        # Calculate scale factors based on display dimensions
        self.scale_x = display_width / self.base_width
        self.scale_y = display_height / self.base_height
        
        # Use minimum scale to maintain aspect ratio
        self.scale_factor = min(self.scale_x, self.scale_y)
        
        # Calculate offset for centering if aspect ratios don't match
        self.offset_x = (display_width - self.base_width * self.scale_factor) // 2
        self.offset_y = (display_height - self.base_height * self.scale_factor) // 2
        
        self.logger.info(f"📏 缩放因子: {self.scale_factor:.2f} (x:{self.scale_x:.2f}, y:{self.scale_y:.2f})")
        self.logger.info(f"📍 居中偏移: ({self.offset_x}, {self.offset_y})")
        self.logger.info(f"📐 基于尺寸: {display_width}x{display_height}")
    
    def scale_font_size(self, base_size: int) -> int:
        """Scale font size based on screen resolution"""
        scaled_size = int(base_size * self.scale_factor)
        return max(scaled_size, 8)  # Minimum readable size
    
    def scale_rect(self, x: int, y: int, width: int, height: int) -> pygame.Rect:
        """Scale and position a rectangle for the current screen"""
        scaled_x = int(x * self.scale_factor + self.offset_x)
        scaled_y = int(y * self.scale_factor + self.offset_y)
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)
        return pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
    
    def scale_point(self, x: int, y: int) -> Tuple[int, int]:
        """Scale a point for the current screen"""
        scaled_x = int(x * self.scale_factor + self.offset_x)
        scaled_y = int(y * self.scale_factor + self.offset_y)
        return (scaled_x, scaled_y)

# Dynamic color palette (same as before)
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

# Base font sizes (will be scaled dynamically)
BASE_FONT_SIZES = {
    'title': 32,
    'subtitle': 24,
    'normal': 18,
    'small': 14,
    'large': 28
}

class AdaptiveButton:
    """Automatically scaling button widget"""
    
    def __init__(self, screen_adapter: ScreenAdapter, x: int, y: int, width: int, height: int, 
                 text: str, font_size_key: str = 'normal', button_type: str = 'normal'):
        self.adapter = screen_adapter
        self.base_rect = pygame.Rect(x, y, width, height)
        self.rect = screen_adapter.scale_rect(x, y, width, height)
        self.text = text
        
        # Create scaled font
        base_font_size = BASE_FONT_SIZES[font_size_key]
        scaled_font_size = screen_adapter.scale_font_size(base_font_size)
        self.font = pygame.font.Font(None, scaled_font_size)
        
        self.state = "normal"
        self.enabled = True
        self.callback = None
        self.button_type = button_type
        
    def set_callback(self, callback: Callable):
        """Set callback function for button click"""
        self.callback = callback
    
    def handle_event(self, event) -> bool:
        """Handle mouse/touch events with scaled coordinates"""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = "pressed"
                if self.callback:
                    self.callback()
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.state == "pressed":
                self.state = "normal"
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if self.state != "pressed":
                    self.state = "hover"
            else:
                if self.state == "hover":
                    self.state = "normal"
        
        return False
    
    def draw(self, surface):
        """Draw the button with appropriate scaling"""
        if not self.enabled:
            color = COLORS['secondary']
        else:
            if self.button_type == 'city':
                color_map = {
                    'normal': COLORS['city_button'],
                    'hover': COLORS['city_hover'],
                    'pressed': COLORS['city_active']
                }
            else:
                color_map = {
                    'normal': COLORS['button'],
                    'hover': COLORS['button_hover'],
                    'pressed': COLORS['button_active']
                }
            color = color_map[self.state]
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLORS['primary'], self.rect, max(1, int(2 * self.adapter.scale_factor)))
        
        # Draw text (centered)
        text_surface = self.font.render(self.text, True, COLORS['primary'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class AdaptivePygameInterface:
    """Main adaptive interface manager for exhibition mode"""
    
    def __init__(self, fullscreen: bool = True, force_landscape: bool = True, rotation_angle: int = 0):
        self.logger = logging.getLogger(__name__)
        
        # Initialize screen adapter with landscape forcing and rotation
        self.adapter = ScreenAdapter(force_landscape=force_landscape, rotation_angle=rotation_angle)
        self.rotation_angle = rotation_angle
        
        # Initialize display with native resolution (physical screen)
        display_size = (self.adapter.native_width, self.adapter.native_height)
        
        # Set display mode with proper resolution
        try:
            if fullscreen:
                self.screen = pygame.display.set_mode(display_size, pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode(display_size)
            
            self.logger.info(f"🖥️ 成功设置显示模式: {display_size[0]}x{display_size[1]}")
        except pygame.error as e:
            self.logger.warning(f"⚠️ 显示模式设置失败，尝试默认模式: {e}")
            # Fallback to default resolution
            self.screen = pygame.display.set_mode((800, 480))
            self.adapter.native_width = 800
            self.adapter.native_height = 480
            
        # Create virtual surface for rendering (uses display dimensions for rotation)
        if rotation_angle in [90, 270]:
            self.virtual_surface = pygame.Surface((self.adapter.display_width, self.adapter.display_height))
        else:
            self.virtual_surface = pygame.Surface((self.adapter.native_width, self.adapter.native_height))
            
        pygame.display.set_caption("Obscura No.7 Virtual Telescope")
        
        # Hide mouse cursor in fullscreen mode
        if fullscreen:
            pygame.mouse.set_visible(False)
        
        # Initialize fonts with scaling
        self.fonts = {}
        for size_name, base_size in BASE_FONT_SIZES.items():
            scaled_size = self.adapter.scale_font_size(base_size)
            self.fonts[size_name] = pygame.font.Font(None, scaled_size)
        
        # Initialize UI elements with adaptive positioning
        self._init_adaptive_ui_elements()
        
        # State management
        self.state_context = StateContext()
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.logger.info(f"✅ 自适应界面初始化完成 - {self.adapter.device_type}")
        self.logger.info(f"🎯 物理显示尺寸: {display_size[0]}x{display_size[1]}")
        self.logger.info(f"🎯 虚拟渲染尺寸: {self.virtual_surface.get_width()}x{self.virtual_surface.get_height()}")
        self.logger.info(f"📏 缩放因子: {self.adapter.scale_factor:.2f}")
        if rotation_angle != 0:
            self.logger.info(f"🔄 界面旋转: {rotation_angle}度")
    
    def _init_adaptive_ui_elements(self):
        """Initialize UI elements with adaptive positioning"""
        # Get actual virtual surface dimensions
        virtual_width = self.virtual_surface.get_width()
        virtual_height = self.virtual_surface.get_height()
        
        # City selection buttons (arranged in grid)
        cities = ['London', 'Edinburgh', 'Manchester']
        self.city_buttons = []
        
        # Calculate grid layout based on actual virtual surface size
        cols = 3
        button_width = 120
        button_height = 50
        spacing = 20
        start_x = (virtual_width - (cols * button_width + (cols-1) * spacing)) // 2
        start_y = virtual_height // 3  # Position at 1/3 of virtual height
        
        for i, city in enumerate(cities):
            x = start_x + (i % cols) * (button_width + spacing)
            y = start_y + (i // cols) * (button_height + spacing)
            
            button = AdaptiveButton(
                self.adapter, x, y, button_width, button_height, 
                city, 'large', 'city'
            )
            button.set_callback(lambda c=city: self.select_city(c))
            self.city_buttons.append(button)
        
        # Main action buttons - center them based on virtual surface
        button_x = (virtual_width - 200) // 2  # 200 is button width
        
        self.fetch_button = AdaptiveButton(
            self.adapter, button_x, virtual_height * 2 // 3, 200, 60, "GENERATE ART", 'large'
        )
        
        self.continue_button = AdaptiveButton(
            self.adapter, button_x, virtual_height * 3 // 4, 200, 60, "TOUCH TO CONTINUE", 'normal'
        )
        
        self.reset_button = AdaptiveButton(
            self.adapter, 50, virtual_height - 70, 120, 50, "RESET", 'normal'
        )
        
        # Parameter sliders (will be implemented as touch areas)
        self.distance_value = 5.0  # km
        self.angle_value = 0.0     # degrees
        self.time_offset = 0       # years
        
        self.logger.info(f"🔧 UI布局基于虚拟表面: {virtual_width}x{virtual_height}")
    
    def select_city(self, city: str):
        """Handle city selection"""
        self.state_context.selected_city = city
        self.state_context.change_state(ExhibitionState.PARAMETER_INPUT)
        self.logger.info(f"🌍 已选择城市: {city}")
    
    def render_with_rotation(self):
        """Render the virtual surface to the physical screen with rotation"""
        if self.rotation_angle == 0:
            # No rotation needed
            self.screen.blit(self.virtual_surface, (0, 0))
        else:
            # Rotate the virtual surface
            rotated_surface = pygame.transform.rotate(self.virtual_surface, self.rotation_angle)
            
            # Get physical screen dimensions
            screen_rect = self.screen.get_rect()
            target_width = screen_rect.width
            target_height = screen_rect.height
            
            # Always scale the rotated surface to exactly match physical screen
            # This ensures no black borders and complete screen filling
            scaled_rotated_surface = pygame.transform.scale(
                rotated_surface, 
                (target_width, target_height)
            )
            
            rotated_size = rotated_surface.get_size()
            self.logger.debug(f"🔧 旋转结果: {rotated_size[0]}x{rotated_size[1]} → 缩放到: {target_width}x{target_height}")
            
            # Clear physical screen first
            self.screen.fill((0, 0, 0))
            
            # Blit the scaled rotated surface to fill entire screen
            self.screen.blit(scaled_rotated_surface, (0, 0))
    
    def get_render_surface(self):
        """Get the surface to render to (virtual surface or actual screen)"""
        return self.virtual_surface if self.rotation_angle != 0 else self.screen
    
    def draw_scaled_text(self, text: str, font_key: str, x: int, y: int, 
                        color=COLORS['primary'], center=False):
        """Draw text with appropriate scaling"""
        font = self.fonts[font_key]
        text_surface = font.render(text, True, color)
        
        # Scale position
        scaled_pos = self.adapter.scale_point(x, y)
        
        # Get the surface to draw on
        surface = self.get_render_surface()
        
        if center:
            text_rect = text_surface.get_rect(center=scaled_pos)
            surface.blit(text_surface, text_rect)
        else:
            surface.blit(text_surface, scaled_pos)
    
    def draw_background(self):
        """Draw adaptive background with steampunk elements"""
        # Get the surface to draw on
        surface = self.get_render_surface()
        
        # Get virtual surface dimensions
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        # Fill background
        surface.fill(COLORS['background'])
        
        # Draw scaled decorative elements
        # Gear patterns (scaled appropriately) - position relative to virtual surface
        gear_radius = int(30 * self.adapter.scale_factor)
        gear_centers = [
            self.adapter.scale_point(virtual_width * 0.125, virtual_height * 0.2),  # Top-left area
            self.adapter.scale_point(virtual_width * 0.875, virtual_height * 0.8),  # Bottom-right area  
            self.adapter.scale_point(virtual_width * 0.0625, virtual_height * 0.75) # Bottom-left area
        ]
        
        for center in gear_centers:
            pygame.draw.circle(surface, COLORS['gear'], center, gear_radius, 
                             max(1, int(3 * self.adapter.scale_factor)))
        
        # Title - center based on virtual surface
        title_x = virtual_width // 2
        self.draw_scaled_text("OBSCURA No.7", 'title', title_x, virtual_height * 0.1, center=True)
        self.draw_scaled_text("Virtual Telescope Exhibition", 'subtitle', title_x, virtual_height * 0.167, center=True)
    
    def run_exhibition_mode(self):
        """Main exhibition loop with adaptive interface"""
        self.logger.info("🎭 开始展览模式")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                
                # Handle button events
                for button in self.city_buttons:
                    button.handle_event(event)
                
                self.fetch_button.handle_event(event)
                self.continue_button.handle_event(event)
                self.reset_button.handle_event(event)
            
            # Clear screen and draw background
            self.draw_background()
            
            # Draw current state
            current_state = self.state_context.current_state
            
            if current_state == ExhibitionState.CITY_SELECTION:
                self.draw_city_selection()
            elif current_state == ExhibitionState.PARAMETER_INPUT:
                self.draw_parameter_input()
            elif current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
                self.draw_confirmation()
            elif current_state == ExhibitionState.PROCESSING:
                self.draw_processing()
            elif current_state == ExhibitionState.RESULT_DISPLAY:
                self.draw_result_display()
            
            # Render with rotation and update display
            self.render_with_rotation()
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        self.cleanup()
    
    def draw_city_selection(self):
        """Draw city selection interface"""
        surface = self.get_render_surface()
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        self.draw_scaled_text("Select Target City:", 'large', virtual_width // 2, virtual_height * 0.25, center=True)
        
        for button in self.city_buttons:
            button.draw(surface)
    
    def draw_parameter_input(self):
        """Draw parameter input interface"""
        surface = self.get_render_surface()
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        city = self.state_context.selected_city or "Unknown"
        self.draw_scaled_text(f"Target: {city}", 'large', virtual_width // 2, virtual_height * 0.25, center=True)
        
        # Parameter display
        self.draw_scaled_text(f"Distance: {self.distance_value:.1f} km", 'normal', virtual_width * 0.125, virtual_height * 0.42)
        self.draw_scaled_text(f"Direction: {self.angle_value:.0f}°", 'normal', virtual_width * 0.125, virtual_height * 0.5)
        self.draw_scaled_text(f"Time Offset: {self.time_offset} years", 'normal', virtual_width * 0.125, virtual_height * 0.58)
        
        # Action button
        self.fetch_button.draw(surface)
    
    def draw_confirmation(self):
        """Draw data fetch confirmation"""
        surface = self.get_render_surface()
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        self.draw_scaled_text("Ready to Generate Art?", 'large', virtual_width // 2, virtual_height * 0.42, center=True)
        self.draw_scaled_text("This will fetch environmental data and create artwork", 'normal', virtual_width // 2, virtual_height * 0.5, center=True)
        
        self.fetch_button.draw(surface)
        self.reset_button.draw(surface)
    
    def draw_processing(self):
        """Draw processing animation"""
        surface = self.get_render_surface()
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        self.draw_scaled_text("Generating Artwork...", 'large', virtual_width // 2, virtual_height * 0.42, center=True)
        
        # Animated progress indicator
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        self.draw_scaled_text(f"Please wait{dots}", 'normal', virtual_width // 2, virtual_height * 0.5, center=True)
    
    def draw_result_display(self):
        """Draw result display"""
        surface = self.get_render_surface()
        virtual_width = surface.get_width()
        virtual_height = surface.get_height()
        
        self.draw_scaled_text("Artwork Generated!", 'large', virtual_width // 2, virtual_height * 0.31, center=True)
        self.draw_scaled_text("Touch screen to view full image", 'normal', virtual_width // 2, virtual_height * 0.79, center=True)
        
        self.continue_button.draw(surface)
        self.reset_button.draw(surface)
    
    def cleanup(self):
        """Cleanup pygame resources"""
        pygame.quit()
        self.logger.info("🔚 自适应界面已关闭")

# Convenience function for easy initialization
def create_adaptive_interface(fullscreen: bool = True, force_landscape: bool = True, rotation_angle: int = 0) -> AdaptivePygameInterface:
    """Create and return an adaptive pygame interface with landscape orientation and rotation support"""
    return AdaptivePygameInterface(fullscreen=fullscreen, force_landscape=force_landscape, rotation_angle=rotation_angle) 