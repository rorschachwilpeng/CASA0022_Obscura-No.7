#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度显示模块
为望远镜工作流提供美观的进度指示和状态更新
"""

import time
import sys
from datetime import datetime
from enum import Enum

class ProgressStatus(Enum):
    """进度状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ProgressDisplay:
    def __init__(self):
        """初始化进度显示器"""
        self.steps = []
        self.current_step = 0
        self.start_time = None
        self.colors = {
            'reset': '\033[0m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'dim': '\033[2m'
        }
        self.emojis = {
            'telescope': '🔭',
            'coordinates': '📍',
            'weather': '🌤️',
            'ai': '🤖',
            'image': '🎨',
            'upload': '☁️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'loading': '⏳',
            'rocket': '🚀'
        }
    
    def init_workflow(self, title="工作流", total_steps=6, workflow_id=""):
        """初始化工作流显示"""
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
        self.workflow_id = workflow_id
        
        print(f"{self.emojis['telescope']} {self._colorize(title, 'bold')}")
        print("=" * 60)
        print(f"📅 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 总步骤数: {total_steps}")
        if workflow_id:
            print(f"🆔 工作流ID: {workflow_id}")
        print()
    
    def setup_workflow(self, steps):
        """设置工作流步骤"""
        self.steps = steps
        self.current_step = 0
        self.start_time = datetime.now()
        
        print(f"{self.emojis['telescope']} {self._colorize('Obscura No.7 虚拟望远镜工作流', 'bold')}")
        print("=" * 60)
        print(f"📅 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 总步骤数: {len(steps)}")
        print()
        
        # 显示所有步骤概览
        for i, step in enumerate(steps, 1):
            status_icon = "○"
            color = 'dim'
            print(f"  {status_icon} {self._colorize(f'{i}. {step}', color)}")
        print()
    
    def step(self, step_number, step_name, description=""):
        """创建步骤上下文管理器"""
        return StepContext(self, step_name, step_number, description)
    
    def start_step(self, step_name, description=""):
        """开始新步骤"""
        self.current_step += 1
        
        # 更新上一步状态（如果存在）
        if self.current_step > 1:
            self._update_step_status(self.current_step - 1, ProgressStatus.SUCCESS)
        
        total_steps = getattr(self, 'total_steps', len(getattr(self, 'steps', [])))
        print(f"{self.emojis['loading']} {self._colorize(f'步骤 {self.current_step}/{total_steps}: {step_name}', 'bold')}")
        if description:
            print(f"   {self._colorize(description, 'dim')}")
        
        return StepContext(self, step_name)
    
    def update_step_progress(self, message, status=ProgressStatus.RUNNING):
        """更新当前步骤进度"""
        icon = self._get_status_icon(status)
        color = self._get_status_color(status)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"   {icon} [{timestamp}] {self._colorize(message, color)}")
    
    def complete_workflow(self, success=True):
        """完成工作流"""
        if success and self.current_step > 0:
            self._update_step_status(self.current_step, ProgressStatus.SUCCESS)
        
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else None
        
        print("\n" + "=" * 60)
        if success:
            print(f"{self.emojis['success']} {self._colorize('工作流完成成功！', 'green', 'bold')}")
        else:
            print(f"{self.emojis['error']} {self._colorize('工作流执行失败', 'red', 'bold')}")
        
        print(f"🕐 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if duration:
            print(f"⏱️ 总耗时: {self._format_duration(duration)}")
        print()
    
    def show_error(self, error_message, details=None):
        """显示错误信息"""
        print(f"\n{self.emojis['error']} {self._colorize('错误', 'red', 'bold')}")
        print(f"   {self._colorize(error_message, 'red')}")
        if details:
            print(f"   {self._colorize('详细信息:', 'dim')}")
            for line in str(details).split('\n'):
                if line.strip():
                    print(f"   {self._colorize(f'  {line}', 'dim')}")
        print()
    
    def show_warning(self, warning_message):
        """显示警告信息"""
        print(f"{self.emojis['warning']} {self._colorize(f'警告: {warning_message}', 'yellow')}")
    
    def show_info(self, info_message):
        """显示信息"""
        print(f"{self.emojis['info']} {self._colorize(info_message, 'cyan')}")
    
    def show_coordinates(self, lat, lon, distance, direction):
        """显示坐标信息"""
        print(f"{self.emojis['coordinates']} {self._colorize('目标坐标计算结果:', 'bold')}")
        print(f"   📍 纬度: {self._colorize(f'{lat:.6f}', 'green')}")
        print(f"   📍 经度: {self._colorize(f'{lon:.6f}', 'green')}")
        print(f"   📏 距离: {self._colorize(f'{distance/1000:.1f} km', 'blue')}")
        print(f"   🧭 方向: {self._colorize(f'{direction:.1f}°', 'blue')}")
    
    def show_weather_summary(self, weather_data):
        """显示天气数据摘要"""
        if not weather_data or not weather_data.get('current_weather'):
            self.show_warning("无天气数据可显示")
            return
        
        current = weather_data['current_weather']
        print(f"{self.emojis['weather']} {self._colorize('环境数据摘要:', 'bold')}")
        temp_text = f'{current.get("temperature", "N/A")}°C'
        humidity_text = f'{current.get("humidity", "N/A")}%'
        pressure_text = f'{current.get("pressure", "N/A")} hPa'
        wind_text = f'{current.get("wind_speed", "N/A")} m/s'
        
        print(f"   🌡️ 温度: {self._colorize(temp_text, 'green')}")
        print(f"   💧 湿度: {self._colorize(humidity_text, 'blue')}")
        print(f"   📊 气压: {self._colorize(pressure_text, 'blue')}")
        print(f"   💨 风速: {self._colorize(wind_text, 'blue')}")
        print(f"   ☁️ 天气: {self._colorize(current.get('weather_description', 'N/A'), 'cyan')}")
        
        # 空气质量
        if weather_data.get('air_quality'):
            aqi = weather_data['air_quality']
            aqi_color = 'green' if aqi.get('aqi', 3) <= 2 else 'yellow' if aqi.get('aqi', 3) <= 3 else 'red'
            print(f"   🫁 空气质量: {self._colorize(aqi.get('aqi_description', 'N/A'), aqi_color)}")
    
    def show_ml_prediction(self, prediction_result):
        """显示ML预测结果"""
        print(f"{self.emojis['ai']} {self._colorize('AI艺术预测结果:', 'bold')}")
        if prediction_result:
            print(f"   🎯 预测类型: {self._colorize(prediction_result.get('prediction_type', 'N/A'), 'green')}")
            confidence_text = f'{prediction_result.get("confidence", 0)*100:.1f}%'
            print(f"   📊 置信度: {self._colorize(confidence_text, 'blue')}")
            print(f"   🎨 风格建议: {self._colorize(prediction_result.get('style_recommendation', 'N/A'), 'purple')}")
        else:
            print(f"   {self._colorize('预测失败或无结果', 'red')}")
    
    def show_progress_bar(self, current, total, prefix="进度", bar_length=40):
        """显示进度条"""
        percent = current / total
        filled_length = int(bar_length * percent)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r   {prefix}: |{bar}| {percent*100:.1f}% ({current}/{total})", end='', flush=True)
        
        if current == total:
            print()  # 换行
    
    def _colorize(self, text, *colors):
        """为文本添加颜色"""
        color_codes = ''.join(self.colors.get(color, '') for color in colors)
        return f"{color_codes}{text}{self.colors['reset']}"
    
    def _get_status_icon(self, status):
        """获取状态图标"""
        icons = {
            ProgressStatus.PENDING: "○",
            ProgressStatus.RUNNING: "●",
            ProgressStatus.SUCCESS: "✓",
            ProgressStatus.ERROR: "✗",
            ProgressStatus.WARNING: "⚠"
        }
        return icons.get(status, "○")
    
    def _get_status_color(self, status):
        """获取状态颜色"""
        colors = {
            ProgressStatus.PENDING: 'dim',
            ProgressStatus.RUNNING: 'blue',
            ProgressStatus.SUCCESS: 'green',
            ProgressStatus.ERROR: 'red',
            ProgressStatus.WARNING: 'yellow'
        }
        return colors.get(status, 'white')
    
    def _update_step_status(self, step_index, status):
        """更新步骤状态（在概览中不显示，仅内部记录）"""
        pass  # 在简化版本中，我们不重新绘制整个步骤列表
    
    def _format_duration(self, duration):
        """格式化持续时间"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"

class StepContext:
    """步骤上下文管理器"""
    def __init__(self, display, step_name, step_number=None, description=""):
        self.display = display
        self.step_name = step_name
        self.step_number = step_number
        self.description = description
        self.step_start_time = datetime.now()
        
        # 当进入上下文时自动开始步骤
        if step_number:
            self.display.current_step = step_number
            total_steps = getattr(self.display, 'total_steps', 6)
            print(f"{self.display.emojis['loading']} {self.display._colorize(f'步骤 {step_number}/{total_steps}: {step_name}', 'bold')}")
            if description:
                print(f"   {self.display._colorize(description, 'dim')}")
    
    def update(self, message, status=ProgressStatus.RUNNING):
        """更新步骤进度"""
        self.display.update_step_progress(message, status)
    
    def success(self, message=""):
        """标记步骤成功"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.SUCCESS)
    
    def error(self, message="", details=None):
        """标记步骤错误"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.ERROR)
        if details:
            self.display.show_error(message, details)
    
    def warning(self, message=""):
        """显示步骤警告"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.WARNING)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error("步骤执行失败", f"{exc_type.__name__}: {exc_val}")
            return False
        return True

if __name__ == "__main__":
    # 测试用例
    print("🎨 进度显示器测试")
    print("=" * 40)
    
    # 模拟工作流
    progress = ProgressDisplay()
    
    workflow_steps = [
        "硬件数据采集",
        "坐标计算",
        "环境数据获取",
        "AI艺术预测",
        "图片生成",
        "云端上传"
    ]
    
    progress.setup_workflow(workflow_steps)
    
    # 模拟步骤1
    with progress.start_step("硬件数据采集", "从磁感器和编码器读取数据") as step:
        step.update("初始化磁感器...")
        time.sleep(0.5)
        step.update("读取方向数据: 92.5°")
        step.update("读取距离数据: 5.2km")
        step.success("硬件数据采集完成")
    
    time.sleep(0.3)
    
    # 模拟步骤2
    with progress.start_step("坐标计算", "基于距离和方向计算目标坐标") as step:
        step.update("计算目标坐标...")
        time.sleep(0.3)
        progress.show_coordinates(51.5074, -0.0556, 5200, 92.5)
        step.success("坐标计算完成")
    
    time.sleep(0.3)
    
    # 模拟步骤3
    with progress.start_step("环境数据获取", "调用OpenWeather API") as step:
        step.update("连接OpenWeather API...")
        step.update("获取当前天气数据...")
        step.update("获取空气质量数据...")
        
        # 模拟天气数据
        mock_weather = {
            'current_weather': {
                'temperature': 15.2,
                'humidity': 65,
                'pressure': 1013,
                'wind_speed': 3.5,
                'weather_description': '多云'
            },
            'air_quality': {
                'aqi': 2,
                'aqi_description': '良好'
            }
        }
        progress.show_weather_summary(mock_weather)
        step.success("环境数据获取完成")
    
    time.sleep(0.3)
    
    # 模拟步骤4
    with progress.start_step("AI艺术预测", "使用机器学习模型生成艺术风格") as step:
        step.update("准备ML输入特征...")
        step.update("调用预测模型...")
        
        # 模拟预测结果
        mock_prediction = {
            'prediction_type': '印象派风景',
            'confidence': 0.87,
            'style_recommendation': '温暖色调，柔和笔触'
        }
        progress.show_ml_prediction(mock_prediction)
        step.success("AI预测完成")
    
    time.sleep(0.3)
    
    # 模拟进度条
    with progress.start_step("图片生成", "生成艺术作品") as step:
        step.update("开始图片生成...")
        for i in range(11):
            progress.show_progress_bar(i, 10, "生成进度")
            time.sleep(0.1)
        step.success("图片生成完成")
    
    time.sleep(0.3)
    
    # 完成工作流
    progress.complete_workflow(success=True)
    
    # 测试错误显示
    print("\n" + "="*40)
    print("🚨 错误处理测试")
    progress.show_error("网络连接失败", "ConnectionError: Failed to establish connection to api.example.com")
    progress.show_warning("API限额接近")
    progress.show_info("系统将在30秒后重试")
    
    print("\n✅ 进度显示器测试完成")
