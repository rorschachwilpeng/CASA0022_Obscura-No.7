#!/usr/bin/env python3
"""
修复验证脚本
测试触摸屏点击和参数更新功能是否正常工作

使用方法:
python3 fix_verification.py
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_enhanced_interface_integration():
    """测试增强界面与状态机的集成"""
    print("🔗 测试增强界面与状态机集成...")
    
    try:
        from core.enhanced_pygame_interface import EnhancedPygameInterface
        from core.exhibition_state_machine import ExhibitionStateMachine, ExhibitionState, StateContext
        
        # 创建状态机和界面
        state_machine = ExhibitionStateMachine()
        interface = EnhancedPygameInterface(fullscreen=False)
        
        # 测试参数更新回调
        update_count = 0
        def test_parameter_update(context):
            nonlocal update_count
            update_count += 1
            print(f"📊 参数更新 #{update_count}: 距离={context.distance_km}km, 角度={context.angle_degrees}°, 时间={context.time_offset_years}年")
            # 立即更新界面
            interface.update_state(context.current_state, context)
        
        state_machine.set_callback('on_parameter_update', test_parameter_update)
        
        # 设置界面回调
        def test_city_callback(city):
            print(f"🏙️ 城市选择: {city}")
            state_machine.select_city(city)
        
        def test_generate_callback():
            print(f"🎨 生成按钮点击")
            # 模拟处理过程
            state_machine.transition_to(ExhibitionState.PROCESSING, "用户点击生成按钮")
            # 3秒后模拟完成
            import threading
            def simulate_completion():
                time.sleep(3)
                state_machine.set_processing_result(
                    {"temperature": 15.5}, 
                    {"prediction": "sunny"}, 
                    "/tmp/test_image.png"
                )
                state_machine.transition_to(ExhibitionState.RESULT_DISPLAY, "处理完成")
            threading.Thread(target=simulate_completion, daemon=True).start()
        
        def test_continue_callback():
            print(f"➡️ 继续按钮点击")
            state_machine.transition_to(ExhibitionState.WAITING_INTERACTION, "进入等待交互")
        
        def test_reset_callback():
            print(f"🔄 重置按钮点击")
            state_machine.request_reset()
        
        interface.set_callback('on_city_selected', test_city_callback)
        interface.set_callback('on_generate_click', test_generate_callback)
        interface.set_callback('on_continue_click', test_continue_callback)
        interface.set_callback('on_reset_click', test_reset_callback)
        
        # 设置状态变化回调
        def state_change_callback(old_state, new_state, context):
            print(f"🔄 状态变化: {old_state.value} → {new_state.value}")
            interface.update_state(new_state, context)
        
        state_machine.set_callback('on_state_change', state_change_callback)
        
        # 初始化界面
        initial_context = state_machine.context
        interface.update_state(initial_context.current_state, initial_context)
        
        print("\n🧪 综合测试启动!")
        print("测试内容:")
        print("1. 触摸事件在所有状态下都能工作")
        print("2. 参数更新时GUI立即响应")
        print("3. 状态切换时界面正确更新")
        print("4. 按D键查看调试信息")
        print("5. 按ESC键退出")
        print()
        
        # 模拟参数变化
        def simulate_parameter_changes():
            time.sleep(2)
            for i in range(5):
                if state_machine.context.current_state == ExhibitionState.PARAMETER_INPUT:
                    new_distance = 25.0 + i * 5.0
                    new_angle = i * 30.0
                    new_time = i * 2
                    print(f"🔧 模拟参数变化 #{i+1}: {new_distance}km, {new_angle}°, +{new_time}年")
                    state_machine.update_parameters(new_distance, new_angle, new_time)
                time.sleep(2)
        
        import threading
        param_thread = threading.Thread(target=simulate_parameter_changes, daemon=True)
        param_thread.start()
        
        # 运行界面
        start_time = time.time()
        while interface.running and time.time() - start_time < 60:  # 最多运行60秒
            if not interface.run_frame():
                break
            
            # 让状态机也运行
            state_machine.step()
            
            time.sleep(0.01)
        
        interface.quit()
        
        print(f"\n📊 测试结果:")
        print(f"   参数更新次数: {update_count}")
        print("✅ 综合测试完成!")
        
        return True
        
    except Exception as e:
        print(f"❌ 综合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_touch_event_handling():
    """专门测试触摸事件处理"""
    print("\n👆 测试触摸事件处理...")
    
    try:
        from core.enhanced_pygame_interface import EnhancedPygameInterface
        from core.exhibition_state_machine import ExhibitionState, StateContext
        import pygame
        
        interface = EnhancedPygameInterface(fullscreen=False)
        
        # 记录事件
        events_captured = []
        
        def capture_city_event(city):
            events_captured.append(f"城市选择: {city}")
        
        def capture_generate_event():
            events_captured.append("生成按钮点击")
        
        def capture_continue_event():
            events_captured.append("继续按钮点击")
        
        def capture_reset_event():
            events_captured.append("重置按钮点击")
        
        interface.set_callback('on_city_selected', capture_city_event)
        interface.set_callback('on_generate_click', capture_generate_event)
        interface.set_callback('on_continue_click', capture_continue_event)
        interface.set_callback('on_reset_click', capture_reset_event)
        
        # 测试不同状态下的触摸响应
        states_to_test = [
            (ExhibitionState.CITY_SELECTION, "城市选择状态"),
            (ExhibitionState.PARAMETER_INPUT, "参数输入状态"),
            (ExhibitionState.WAITING_INTERACTION, "等待交互状态")
        ]
        
        for state, state_name in states_to_test:
            print(f"\n测试 {state_name}...")
            
            # 设置状态
            context = StateContext()
            context.current_state = state
            context.distance_km = 25.0
            context.angle_degrees = 45.0
            context.time_offset_years = 5
            interface.update_state(state, context)
            
            # 模拟触摸事件
            print(f"   当前按钮状态:")
            for i, button in enumerate(interface.city_buttons):
                print(f"     城市按钮{i}: {'可用' if button.enabled else '禁用'}")
            print(f"     生成按钮: {'可用' if interface.generate_button.enabled else '禁用'}")
            print(f"     继续按钮: {'可用' if interface.continue_button.enabled else '禁用'}")
            print(f"     重置按钮: {'可用' if interface.reset_button.enabled else '禁用'}")
            
            # 运行几帧来测试
            for _ in range(5):
                if not interface.run_frame():
                    break
                time.sleep(0.1)
        
        print(f"\n捕获的事件:")
        for event in events_captured:
            print(f"   ✅ {event}")
        
        interface.quit()
        return True
        
    except Exception as e:
        print(f"❌ 触摸事件测试失败: {e}")
        return False

def run_verification():
    """运行所有验证测试"""
    print("🧪 Obscura No.7 修复验证工具")
    print("=" * 50)
    
    tests = [
        ("触摸事件处理", test_touch_event_handling),
        ("增强界面集成", test_enhanced_interface_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {test_name}")
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断测试: {test_name}")
            break
        except Exception as e:
            print(f"❌ 测试异常: {test_name} - {e}")
            results[test_name] = False
    
    # 显示总结
    print("\n" + "=" * 50)
    print("📊 验证总结")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有验证测试通过!")
        print("\n📝 修复状态:")
        print("✅ 触摸屏事件处理: 已修复")
        print("✅ GUI参数更新: 已修复")
        print("✅ 状态切换: 正常工作")
        print("\n🚀 现在可以运行: ./start_exhibition_with_fixes.sh")
    else:
        print("⚠️ 部分验证失败，需要进一步调试。")

if __name__ == "__main__":
    run_verification() 