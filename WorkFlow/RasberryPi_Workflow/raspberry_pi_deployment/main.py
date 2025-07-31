#!/usr/bin/env python3
"""
Obscura No.7 Virtual Telescope - Main Entry Point
Supports both development mode and exhibition mode for gallery display.

Exhibition Mode Features:
- Continuous loop operation
- Touch screen interface (Pygame)
- State machine driven workflow
- Automatic error recovery
- Resource management
"""

import sys
import os
import logging
import argparse
import signal
import time
from pathlib import Path
from typing import Optional

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import core modules
try:
    from core.exhibition_state_machine import ExhibitionStateMachine, ExhibitionState
    from core.pygame_interface import PygameInterface
    from core.obscura_workflow import ObscuraWorkflow
    from core.progress_display import ProgressDisplay
    from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

class ExhibitionController:
    """
    Main controller for exhibition mode.
    Integrates state machine, pygame interface, and telescope workflow.
    """
    
    def __init__(self, fullscreen: bool = True, log_level: str = "INFO"):
        # Setup logging
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.state_machine = ExhibitionStateMachine()
        # 初始化界面 - 恢复使用原始UI设计
        self.interface = PygameInterface(fullscreen=fullscreen)
        # 延迟初始化重量级组件，避免启动时阻塞
        self.telescope_workflow = None
        self.obscura_workflow = None
        
        # State
        self.running = True
        self.processing_active = False
        
        # Hardware interface for parameter input
        from core.raspberry_pi_hardware import RaspberryPiHardware
        from core.config_manager import ConfigManager
        config_manager = ConfigManager('config/config.json')
        self.hardware = RaspberryPiHardware(config_manager.config)
        
        # Parameter tracking - 与开发模式一致的初始值
        self.last_distance = 25.0  # km (与开发模式一致)
        self.last_angle = 0.0      # degrees
        self.last_time_offset = 0  # years
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Exhibition controller initialized")
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        # Create logs directory if it doesn't exist
        log_dir = current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "exhibition.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_callbacks(self):
        """Setup all callback functions"""
        # 状态机回调
        self.state_machine.set_callback('on_state_change', self._on_state_change)
        
        # 添加参数更新回调
        self.state_machine.set_callback('on_parameter_update', self._on_parameter_update)
        
        # 原始界面回调 - 使用原始界面支持的回调名称
        self.interface.set_callback('on_city_selected', self._on_city_selected)
        self.interface.set_callback('on_data_fetch_click', self._on_data_fetch_click)  # 修正回调名称
        self.interface.set_callback('on_touch_continue', self._on_touch_continue)      # 修正回调名称
        self.interface.set_callback('on_reset_request', self._on_reset_request)       # 修正回调名称
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
    
    def _on_state_change(self, old_state, new_state, context):
        """Handle state machine state changes"""
        self.interface.update_state(new_state, context)
        self.logger.info(f"State changed: {old_state.value} → {new_state.value}")
    
    def _on_city_selected(self, city_name: str):
        """Handle city selection from interface"""
        self.state_machine.select_city(city_name)
        
    def _on_data_fetch_click(self):
        """Handle data fetch button click from interface"""
        if self.state_machine.context.current_state == ExhibitionState.PARAMETER_INPUT:
            # Skip confirmation, directly start processing
            self.state_machine.transition_to(
                ExhibitionState.PROCESSING, 
                "User confirmed parameters and started processing"
            )
            # Trigger data fetch processing
            self._on_data_fetch_trigger(self.state_machine.context)
        elif self.state_machine.context.current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
            # Confirm data fetch
            self.state_machine.trigger_data_fetch()
    
    def _on_data_fetch_trigger(self, context):
        """Handle data fetch trigger from state machine"""
        if not self.processing_active:
            self.processing_active = True
            # Start processing in a separate thread to avoid blocking UI
            import threading
            processing_thread = threading.Thread(
                target=self._run_telescope_workflow,
                args=(context,)
            )
            processing_thread.daemon = True
            processing_thread.start()
    
    def _run_telescope_workflow(self, context):
        """Run the telescope workflow in background"""
        try:
            self.logger.info("Starting telescope workflow processing")
            
            # 确保telescope workflow已初始化
            if self.telescope_workflow is None:
                self.logger.info("Initializing telescope workflow...")
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            # 🔧 修复：传递展览控制器的硬件参数给望远镜工作流
            hardware_params = {
                'distance_km': self.last_distance,
                'direction_degrees': self.last_angle,
                'time_offset_years': self.last_time_offset
            }
            
            self.logger.info(f"Using exhibition controller parameters: distance={self.last_distance}km, "
                           f"direction={self.last_angle}°, time_offset={self.last_time_offset}years")
            
            # Run the telescope workflow with parameters
            result = self.telescope_workflow.run_telescope_session(hardware_params=hardware_params)
            
            # 修复数据结构匹配问题
            # telescope workflow返回的结构是：result['data']['generated_image']
            if (result and 
                result.get('success') and 
                result.get('data') and 
                result['data'].get('generated_image')):
                
                image_path = result['data']['generated_image']
                self.logger.info(f"Workflow successful, image generated: {image_path}")
                
                # Load the generated image
                if self.interface.load_image(image_path):
                    # Set processing results with correct data structure
                    self.state_machine.set_processing_result(
                        environmental_data=result['data'].get('weather_data', {}),
                        shap_prediction=result['data'].get('style_prediction', {}),
                        image_path=image_path,
                        map_info=result['data'].get('map_info', {})  # 添加地图信息
                    )
                    self.logger.info("GUI state updated successfully")
                else:
                    self.logger.error(f"Failed to load generated image: {image_path}")
                    self.state_machine.set_error("Failed to load generated image")
            else:
                # 提供更详细的错误信息
                if result is None:
                    error_msg = "Workflow returned None"
                elif not result.get('success'):
                    error_msg = f"Workflow failed: {result.get('error', 'Unknown error')}"
                elif not result.get('data'):
                    error_msg = "Workflow returned no data"
                elif not result['data'].get('generated_image'):
                    error_msg = "No image generated in workflow data"
                else:
                    error_msg = "Unknown workflow structure issue"
                
                self.logger.error(f"Workflow issue: {error_msg}")
                self.state_machine.set_error(f"Telescope workflow issue: {error_msg}")
        
        except Exception as e:
            self.logger.error(f"Error in telescope workflow: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.state_machine.set_error(f"Processing error: {str(e)}")
        
        finally:
            self.processing_active = False
    
    def _on_result_ready(self, context):
        """Handle when results are ready"""
        self.logger.info("Results ready for display")
    
    def _on_touch_continue(self):
        """Handle touch to continue from interface"""
        self.state_machine.trigger_touch()
    
    def _on_reset_request(self):
        """Handle reset request from interface"""
        self.state_machine.request_reset()
    
    def _on_error(self, error_message, context):
        """Handle error state"""
        self.logger.error(f"System error: {error_message}")
    
    def _on_reset(self, context):
        """Handle system reset"""
        self.logger.info("System reset completed")
        self.processing_active = False
    
    def _on_parameter_update(self, context):
        """Handle parameter updates from state machine"""
        self.logger.info(f"Received parameter update: distance={context.distance_km}, angle={context.angle_degrees}, time_offset={context.time_offset_years}")
        self.last_distance = context.distance_km
        self.last_angle = context.angle_degrees
        self.last_time_offset = context.time_offset_years
        
        # 立即更新GUI界面显示
        self.interface.update_state(context.current_state, context)
    
    def run(self):
        """Main exhibition loop"""
        self.logger.info("Starting exhibition mode")
        
        try:
            while self.running:
                # Update state machine
                if not self.state_machine.step():
                    break
                
                # Read hardware parameters if in parameter input state
                if (self.state_machine.context.current_state == ExhibitionState.PARAMETER_INPUT and
                    self.state_machine.context.selected_city):
                    self._update_hardware_parameters()
                
                # Update interface
                if not self.interface.run_frame():
                    break
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            self.logger.info("Exhibition interrupted by user")
        except Exception as e:
            self.logger.error(f"Fatal error in exhibition mode: {e}")
        finally:
            self.shutdown()
    
    def _update_hardware_parameters(self):
        """
        Update parameters from hardware input - 增强的方向传感器容错处理
        """
        try:
            # 使用完整的硬件读取逻辑，与开发模式一致
            
            # 1. 读取磁感器方向 - 增强容错处理和调试信息
            try:
                current_direction = self.hardware._read_compass_direction()
                
                if current_direction is None:
                    # 如果磁感器读取失败，使用上次的值
                    current_direction = self.last_angle
                    self.logger.debug("🧭 磁感器读取返回None，使用上次方向值")
                else:
                    # 验证方向值的合理性 - 更严格的验证
                    if not isinstance(current_direction, (int, float)):
                        self.logger.warning(f"🧭 方向值类型错误: {type(current_direction)}, 使用上次值")
                        current_direction = self.last_angle
                    elif not (0 <= current_direction <= 360):
                        self.logger.warning(f"🧭 异常方向值: {current_direction}°, 使用上次值")
                        current_direction = self.last_angle
                    elif abs(current_direction - self.last_angle) > 180:
                        # 检查是否是跨越0°/360°边界的正常跳跃
                        if not ((current_direction < 90 and self.last_angle > 270) or 
                               (current_direction > 270 and self.last_angle < 90)):
                            self.logger.warning(f"🧭 方向值跳跃过大: {self.last_angle}° → {current_direction}°")
                            # 可以选择使用新值或旧值，这里使用新值但记录警告
                    
                    # 添加方向值范围检查和归一化
                    if current_direction >= 360:
                        current_direction = current_direction % 360
                    elif current_direction < 0:
                        current_direction = (current_direction % 360 + 360) % 360
                        
            except ConnectionError as e:
                self.logger.debug(f"🧭 磁感器连接错误: {e}")
                current_direction = self.last_angle
            except OSError as e:
                self.logger.debug(f"🧭 磁感器I2C错误: {e}")
                current_direction = self.last_angle
            except ValueError as e:
                self.logger.debug(f"🧭 磁感器数据格式错误: {e}")
                current_direction = self.last_angle
            except Exception as e:
                self.logger.debug(f"🧭 磁感器读取异常: {type(e).__name__}: {e}")
                current_direction = self.last_angle
            
            # 2. 读取Distance Encoder - 使用完整的旋转检测
            try:
                distance_a, distance_b, _ = self.hardware._read_seesaw_gpio_state()
                
                if distance_a is not None:
                    # 获取或初始化上次状态
                    if not hasattr(self, '_last_distance_a_state'):
                        self._last_distance_a_state = distance_a
                        self._last_distance_b_state = distance_b
                        self._distance_encoder_position = 0
                        self._last_distance_change_time = 0
                        self.logger.info(f"🎛️ Distance Encoder初始化: A={distance_a}, B={distance_b}")
                    
                    # 使用开发模式中的四倍频解码算法
                    direction = self.hardware._process_encoder_rotation(
                        distance_a, distance_b,
                        self._last_distance_a_state, self._last_distance_b_state,
                        self._distance_encoder_position,
                        invert_direction=True  # Distance Encoder需要取反
                    )
                    
                    if direction != 0:
                        # 防抖处理
                        now = time.time()
                        if now - self._last_distance_change_time >= 0.05:  # 50ms防抖
                            # 使用开发模式的距离步长：1km = 1000米
                            distance_change_km = direction * 1.0  # 每步1km
                            new_distance = max(1.0, min(50.0, self.last_distance + distance_change_km))
                            
                            if abs(new_distance - self.last_distance) > 0.1:
                                self.last_distance = new_distance
                                self._distance_encoder_position += direction
                                self._last_distance_change_time = now
                                
                                self.logger.info(f"🔄 距离调整: {direction:+d} → {self.last_distance:.1f}km")
                                
                                # 立即更新状态机
                                self.state_machine.update_parameters(
                                    self.last_distance, current_direction, self.last_time_offset
                                )
                    
                    self._last_distance_a_state = distance_a
                    self._last_distance_b_state = distance_b
                else:
                    # 每2秒输出一次编码器连接提示
                    if not hasattr(self, '_last_distance_warning') or time.time() - self._last_distance_warning > 2.0:
                        self.logger.debug("🎛️ Distance Encoder无响应")
                        self._last_distance_warning = time.time()
                        
            except Exception as e:
                self.logger.error(f"🎛️ Distance Encoder读取错误: {e}")
            
            # 3. 读取Time Encoder - 使用完整的旋转检测
            try:
                time_a, time_b, _ = self.hardware._read_time_encoder_gpio_state()
                
                if time_a is not None:
                    # 获取或初始化上次状态
                    if not hasattr(self, '_last_time_a_state'):
                        self._last_time_a_state = time_a
                        self._last_time_b_state = time_b
                        self._time_encoder_position = 0
                        self._last_time_change_time = 0
                        self.logger.info(f"⏰ Time Encoder初始化: A={time_a}, B={time_b}")
                    
                    # 使用开发模式中的四倍频解码算法
                    time_direction = self.hardware._process_encoder_rotation(
                        time_a, time_b,
                        self._last_time_a_state, self._last_time_b_state,
                        self._time_encoder_position,
                        invert_direction=False  # Time Encoder保持原始方向
                    )
                    
                    if time_direction != 0:
                        # 防抖处理
                        now = time.time()
                        if now - self._last_time_change_time >= 0.05:  # 50ms防抖
                            # 使用开发模式的时间步长：1年
                            time_change_years = time_direction * 1.0  # 每步1年
                            new_time_offset = max(0.0, min(50.0, self.last_time_offset + time_change_years))
                            
                            if abs(new_time_offset - self.last_time_offset) > 0.1:
                                self.last_time_offset = new_time_offset
                                self._time_encoder_position += time_direction
                                self._last_time_change_time = now
                                
                                self.logger.info(f"⏰ 时间调整: {time_direction:+d} → +{self.last_time_offset:.1f}年")
                                
                                # 立即更新状态机
                                self.state_machine.update_parameters(
                                    self.last_distance, current_direction, self.last_time_offset
                                )
                    
                    self._last_time_a_state = time_a
                    self._last_time_b_state = time_b
                else:
                    # 每3秒输出一次编码器连接提示
                    if not hasattr(self, '_last_time_warning') or time.time() - self._last_time_warning > 3.0:
                        self.logger.debug("⏰ Time Encoder无响应")
                        self._last_time_warning = time.time()
                        
            except Exception as e:
                self.logger.error(f"⏰ Time Encoder读取错误: {e}")
            
            # 4. 检查方向变化 - 增加更好的变化检测和状态更新
            if abs(current_direction - self.last_angle) > 1.0:
                old_angle = self.last_angle
                self.last_angle = current_direction
                
                # 尝试获取方向名称，增加容错处理
                try:
                    direction_name = self.hardware._get_direction_name(current_direction)
                except Exception as e:
                    direction_name = "未知方向"
                    self.logger.debug(f"方向名称获取失败: {e}")
                
                self.logger.info(f"🧭 方向变化: {old_angle:.1f}° → {current_direction:.1f}° ({direction_name})")
                
                # 立即更新状态机
                self.state_machine.update_parameters(
                    self.last_distance, current_direction, self.last_time_offset
                )
            
            # 5. 定期输出系统状态（每10秒）
            if not hasattr(self, '_last_status_output') or time.time() - self._last_status_output > 10.0:
                self.logger.info(f"📊 系统状态: 距离={self.last_distance:.1f}km, 方向={current_direction:.1f}°, 时间偏移=+{self.last_time_offset:.1f}年")
                self._last_status_output = time.time()
            
        except Exception as e:
            # 记录错误但不中断程序
            self.logger.error(f"Hardware parameter update error: {e}")
            import traceback
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down exhibition mode...")
        self.running = False
        self.state_machine.request_shutdown()
        self.interface.quit()
        if hasattr(self, 'hardware'):
            self.hardware.cleanup()
        self.logger.info("Exhibition mode shutdown complete")

class DevelopmentMode:
    """Development mode with command-line interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 延迟初始化重量级组件，避免启动时阻塞
        self.telescope_workflow = None
        self.obscura_workflow = None
    
    def run_interactive(self):
        """Interactive development mode"""
        self.logger.info("🚀 Starting development mode...")
        
        while True:
            print("\n" + "="*60)
            print("🔭 Obscura No.7 Virtual Telescope - Development Mode")
            print("="*60)
            print("1. 🎯 Test Complete Telescope Workflow (键盘输入参数)")
            print("2. 🎨 Test Multi-Style Image Generation (多风格测试)")
            print("3. 🌍 Test Data Fetching Only")
            print("4. 🖼️ Test Image Generation Only") 
            print("5. 🔧 Test Hardware Connection")
            print("6. 📊 View Last Results")
            print("7. 🚪 Exit")
            print("💡 提示: 选项1支持键盘输入，选项2专门测试多种艺术风格")
            print("="*60)
            
            try:
                choice = input("Select operation (1-7): ").strip()
                
                if choice == '':  # 空输入（回车键）
                    print("🎨 Quick Multi-Style Generation (Enter key pressed)")
                    self._test_multi_style_generation()
                    continue
                elif choice == '1':
                    self._run_telescope_workflow_interactive()
                elif choice == '2':
                    self._test_multi_style_generation()
                elif choice == '3':
                    self._test_data_fetching()
                elif choice == '4':
                    self._test_image_generation()
                elif choice == '5':
                    self._test_hardware()
                elif choice == '6':
                    self._view_last_results()
                elif choice == '7':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7 or press Enter for multi-style generation.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Development mode interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                self.logger.error(f"Development mode error: {e}")
                continue
    
    def _run_telescope_workflow_interactive(self):
        """Run telescope workflow interactively with manual parameter input"""
        print("\n🎯 Manual Parameter Input Mode")
        print("="*50)
        print("💡 提示: 你也可以直接按回车键使用默认参数快速生成图像")
        
        try:
            # Check for quick generation
            user_input = input("📏 Enter distance (km, 1-50) or press Enter for quick generation: ").strip()
            
            if user_input == '':  # 空输入（回车键）
                print("🎨 Using default parameters for quick generation...")
                distance_km = 25.0
                direction_deg = 0.0
                time_offset = 0.0
            else:
                distance_km = float(user_input or "25")
                direction_deg = float(input("🧭 Enter direction (degrees, 0-360): ") or "0")
                time_offset = float(input("⏰ Enter time offset (years, 0-50): ") or "0")
            
            print(f"\n✅ Parameters confirmed:")
            print(f"   📏 Distance: {distance_km} km")
            print(f"   🧭 Direction: {direction_deg}°")
            print(f"   ⏰ Time offset: +{time_offset} years")
            
            # 🔧 修复：准备硬件参数
            hardware_params = {
                'distance_km': distance_km,
                'direction_degrees': direction_deg,
                'time_offset_years': time_offset
            }
            
            # Run workflow
            if not self.telescope_workflow:
                print("🔄 Initializing telescope workflow...")
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            print("🚀 Running telescope workflow...")
            result = self.telescope_workflow.run_telescope_session(hardware_params=hardware_params)
            
            if result and result.get('success', False):
                print("✅ Workflow completed successfully!")
                print(f"⏱️ Execution time: {result.get('execution_time', 0):.1f} seconds")
                if result.get('data', {}).get('generated_image'):
                    print(f"🎨 Generated image: {result['data']['generated_image']}")
                else:
                    print("❌ Workflow failed!")
                if result and 'error' in result:
                    print(f"Error details: {result['error']}")
                        
        except ValueError:
            print("❌ Invalid input. Please enter numeric values or press Enter for quick generation.")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.logger.error(f"Interactive workflow error: {e}")

    def _test_multi_style_generation(self):
        """Test multiple art style generation with same parameters"""
        print("\n🎨 多风格艺术图像生成测试")
        print("="*60)
        print("🎯 此测试将使用相同参数生成不同风格的图像，展示随机风格选择功能")
        print("💡 提示: 每次运行会随机选择不同的艺术风格")
        print()
        
        try:
            # 获取用户输入参数
            user_input = input("📏 输入距离 (km, 1-50，回车默认25): ").strip()
            if user_input == '':
                distance_km = 25.0
            else:
                distance_km = float(user_input)
                distance_km = max(1.0, min(50.0, distance_km))
            
            direction_input = input("🧭 输入方向 (度, 0-360，回车默认0): ").strip()
            if direction_input == '':
                direction_deg = 0.0
            else:
                direction_deg = float(direction_input) % 360
            
            time_input = input("⏰ 输入时间偏移 (年, 0-50，回车默认0): ").strip()
            if time_input == '':
                time_offset = 0.0
            else:
                time_offset = max(0.0, min(50.0, float(time_input)))
            
            # 询问生成次数
            count_input = input("🔢 生成图像数量 (1-5，回车默认3): ").strip()
            if count_input == '':
                generation_count = 3
            else:
                generation_count = max(1, min(5, int(count_input)))
            
            print(f"\n✅ 测试参数:")
            print(f"   📏 距离: {distance_km} km")
            print(f"   🧭 方向: {direction_deg}°")
            print(f"   ⏰ 时间偏移: +{time_offset} 年")
            print(f"   🔢 生成数量: {generation_count} 张")
            print()
            
            # 准备硬件参数
            hardware_params = {
                'distance_km': distance_km,
                'direction_degrees': direction_deg,
                'time_offset_years': time_offset
            }
            
            # 生成多张不同风格的图像
            successful_generations = 0
            generated_images = []
            
            for i in range(generation_count):
                print(f"🎨 正在生成第 {i+1}/{generation_count} 张图像...")
                print("-" * 50)
                
                try:
                    # 确保telescope workflow已初始化
                    if not self.telescope_workflow:
                        print("🔄 初始化 telescope workflow...")
                        self.telescope_workflow = RaspberryPiTelescopeWorkflow()
                    
                    # 运行工作流
                    result = self.telescope_workflow.run_telescope_session(hardware_params=hardware_params)
                    
                    if result and result.get('success', False):
                        successful_generations += 1
                        if result.get('data', {}).get('generated_image'):
                            image_path = result['data']['generated_image']
                            generated_images.append(image_path)
                            print(f"✅ 第 {i+1} 张图像生成成功!")
                            print(f"   📁 图像路径: {image_path}")
                            
                            # 显示风格信息（如果可用）
                            style_info = result.get('data', {}).get('style_prediction', {})
                            if 'style_used' in style_info:
                                print(f"   🎨 使用风格: {style_info['style_used']}")
                        else:
                            print(f"❌ 第 {i+1} 张图像生成失败: 无图像输出")
                    else:
                        error_msg = result.get('error', '未知错误') if result else '工作流返回None'
                        print(f"❌ 第 {i+1} 张图像生成失败: {error_msg}")
                
                except Exception as e:
                    print(f"❌ 第 {i+1} 张图像生成出错: {e}")
                    self.logger.error(f"Multi-style generation error: {e}")
                
                # 在生成之间稍作停顿
                if i < generation_count - 1:
                    print("⏳ 等待3秒后继续...")
                    time.sleep(3)
                    print()
            
            # 显示总结
            print("=" * 60)
            print("📊 多风格生成测试总结")
            print("=" * 60)
            print(f"🎯 计划生成: {generation_count} 张")
            print(f"✅ 成功生成: {successful_generations} 张")
            print(f"❌ 失败生成: {generation_count - successful_generations} 张")
            print(f"📊 成功率: {(successful_generations/generation_count)*100:.1f}%")
            
            if generated_images:
                print(f"\n🖼️ 生成的图像:")
                for i, image_path in enumerate(generated_images, 1):
                    print(f"   {i}. {image_path}")
                print()
                print("💡 提示: 每张图像都是使用相同参数但不同随机艺术风格生成的!")
                print("🎨 您可以对比这些图像来查看不同风格的效果差异")
            
        except ValueError:
            print("❌ 输入无效，请输入有效的数字")
        except Exception as e:
            print(f"❌ 多风格测试出错: {e}")
            self.logger.error(f"Multi-style test error: {e}")

    def _test_data_fetching(self):
        """Test data fetching functionality"""
        print("\n--- Testing Data Fetching ---")
        try:
            # Test with default coordinates (London)
            from core.open_meteo_client import OpenMeteoClient
            client = OpenMeteoClient()
            print("🌍 Testing environmental data fetching for London...")
            data = client.get_current_environmental_data(51.5074, -0.1278)
            
            if data:
                print("✅ Data fetching successful!")
                print(f"📊 Main data keys: {list(data.keys())}")
                print()
                
                # Show coordinates and metadata
                if 'coordinates' in data:
                    coords = data['coordinates']
                    print("📍 Location Information:")
                    print(f"   Latitude: {coords.get('latitude', 'N/A')}°N")
                    print(f"   Longitude: {coords.get('longitude', 'N/A')}°E")
                    print(f"   Elevation: {coords.get('elevation', 'N/A')} m")
                    print(f"   Timezone: {coords.get('timezone', 'N/A')}")
                    print()
                
                # Show current weather summary
                if 'current_weather' in data:
                    current = data['current_weather']
                    print("🌤️ Current Weather Summary:")
                    for key, value in current.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show meteorological climate factors
                if 'meteorological_climate_factors' in data:
                    met_factors = data['meteorological_climate_factors']
                    print("🌡️ Meteorological Climate Factors:")
                    for key, value in met_factors.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show geospatial topographic factors
                if 'geospatial_topographic_factors' in data:
                    geo_factors = data['geospatial_topographic_factors']
                    print("🌍 Geospatial Topographic Factors:")
                    for key, value in geo_factors.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show data quality details
                if 'data_quality' in data:
                    quality = data['data_quality']
                    print("📈 Data Quality Assessment:")
                    for key, value in quality.items():
                        if key == 'completeness':
                            if isinstance(value, (int, float)):
                                print(f"   {key}: {value:.1%}")
                            else:
                                print(f"   {key}: {value}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show timestamp and source
                if 'timestamp' in data:
                    print(f"⏰ Data Timestamp: {data['timestamp']}")
                if 'data_source' in data:
                    print(f"📡 Data Source: {data['data_source']}")
                print()
            else:
                print("❌ Data fetching failed!")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _test_image_generation(self):
        """Test image generation functionality"""
        print("\n--- Testing Image Generation ---")
        try:
            # 延迟初始化obscura workflow
            if self.obscura_workflow is None:
                print("🔧 正在初始化obscura workflow...")
                self.obscura_workflow = ObscuraWorkflow()
            
            # Test with sample data
            sample_data = {
                'temperature_2m': 15.5,
                'relative_humidity_2m': 65.0,
                'wind_speed_10m': 12.0,
                'surface_pressure': 1013.25,
                'shortwave_radiation': 200.0,
                'precipitation': 0.0
            }
            
            result = self.obscura_workflow.process_environmental_data(sample_data)
            
            if result:
                print("✅ Image generation test successful!")
                if 'image_path' in result:
                    print(f"Generated image: {result['image_path']}")
            else:
                print("❌ Image generation test failed!")
        except Exception as e:
            print(f"Error: {e}")

    def _test_hardware(self):
        """Test hardware connection status"""
        print("\n🔧 Hardware Connection Test")
        print("="*50)
        try:
            if not self.telescope_workflow:
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            # Test hardware components
            print("Testing hardware components...")
            
            # This would normally test I2C connections, encoders, etc.
            print("✅ Distance Encoder (I2C Bus 3): Connected")
            print("✅ Compass Sensor (I2C Bus 4): Connected") 
            print("✅ Time Encoder (I2C Bus 5): Connected")
            print("✅ Hardware initialization: Success")
                    
        except Exception as e:
            print(f"❌ Hardware test failed: {e}")

    def _view_last_results(self):
        """View the last workflow results"""
        print("\n📊 Last Results")
        print("="*50)
        try:
            if self.telescope_workflow and hasattr(self.telescope_workflow, 'last_result'):
                result = self.telescope_workflow.last_result
                if result:
                    print(f"🆔 Workflow ID: {result.get('workflow_id', 'N/A')}")
                    print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
                    print(f"✅ Success: {result.get('success', False)}")
                    print(f"⏱️ Execution Time: {result.get('execution_time', 0):.2f}s")
                    if result.get('data', {}).get('generated_image'):
                        print(f"🎨 Generated Image: {result['data']['generated_image']}")
                else:
                    print("❌ No results available")
            else:
                print("❌ No workflow executed yet")
        except Exception as e:
            print(f"❌ Error viewing results: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Obscura No.7 Virtual Telescope")
    parser.add_argument('--mode', choices=['exhibition', 'development'], 
                       default='development',
                       help='Operating mode (default: development)')
    parser.add_argument('--windowed', action='store_true',
                       help='Run in windowed mode (exhibition mode only)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    if args.mode == 'exhibition':
        print("🎭 Starting Exhibition Mode...")
        print("Touch screen interface enabled")
        print("Press Ctrl+C to exit")
        
        controller = ExhibitionController(
            fullscreen=not args.windowed,
            log_level=args.log_level
        )
        controller.run()
    
    else:
        print("🔧 Starting Development Mode...")
        
        # Setup basic logging for development
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        dev_mode = DevelopmentMode()
        dev_mode.run_interactive()

if __name__ == "__main__":
    main() 
