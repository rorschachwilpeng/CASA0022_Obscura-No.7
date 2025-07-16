#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速触摸测试脚本 - 验证触摸偏置修复效果
用于快速验证触摸精度和pygame字体修复
"""

import pygame
import time
import sys

def quick_touch_test():
    """快速触摸测试"""
    print("🔧 启动快速触摸测试...")
    
    # 初始化pygame和字体 - 测试字体修复
    try:
        pygame.init()
        pygame.font.init()
        print("✅ pygame和字体系统初始化成功")
    except Exception as e:
        print(f"❌ pygame初始化失败: {e}")
        return False
    
    # 检测屏幕分辨率
    try:
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        print(f"✅ 检测到屏幕分辨率: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"❌ 屏幕分辨率检测失败: {e}")
        screen_width, screen_height = 800, 480
        print(f"⚠️ 使用默认分辨率: {screen_width}x{screen_height}")
    
    # 创建显示窗口
    try:
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Quick Touch Test")
        print("✅ 显示窗口创建成功")
    except Exception as e:
        print(f"❌ 显示窗口创建失败: {e}")
        return False
    
    # 测试字体创建
    try:
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 32)
        print("✅ 字体创建成功")
    except Exception as e:
        try:
            font_large = pygame.font.SysFont('arial', 48)
            font_medium = pygame.font.SysFont('arial', 32)
            print("✅ 系统字体创建成功")
        except Exception as e2:
            print(f"❌ 字体创建失败: {e2}")
            return False
    
    # 定义测试按钮
    test_buttons = [
        {'rect': pygame.Rect(100, 150, 150, 80), 'text': '左上', 'color': (255, 100, 100)},
        {'rect': pygame.Rect(550, 150, 150, 80), 'text': '右上', 'color': (100, 255, 100)},
        {'rect': pygame.Rect(100, 350, 150, 80), 'text': '左下', 'color': (100, 100, 255)},
        {'rect': pygame.Rect(550, 350, 150, 80), 'text': '右下', 'color': (255, 255, 100)},
        {'rect': pygame.Rect(325, 250, 150, 80), 'text': '中心', 'color': (255, 100, 255)},
    ]
    
    # 校准偏移量（基于用户反馈的偏置问题）
    calibration_offset_x = 30  # 向右偏移30像素
    calibration_offset_y = 0   # Y轴无偏移
    
    touch_hits = []
    clock = pygame.time.Clock()
    
    print("🎯 快速触摸测试开始")
    print("   - 请点击彩色按钮测试触摸精度")
    print("   - 按ESC退出测试")
    print("   - 测试会显示原始触摸点（红色）和校准后位置（绿色）")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.FINGERDOWN:
                # 原始触摸坐标
                raw_x = int(event.x * screen_width)
                raw_y = int(event.y * screen_height)
                
                # 应用校准偏移
                calibrated_x = raw_x + calibration_offset_x
                calibrated_y = raw_y + calibration_offset_y
                
                # 检查命中哪个按钮
                hit_button = None
                for button in test_buttons:
                    if button['rect'].collidepoint(calibrated_x, calibrated_y):
                        hit_button = button['text']
                        break
                
                # 记录触摸
                touch_hit = {
                    'raw_pos': (raw_x, raw_y),
                    'calibrated_pos': (calibrated_x, calibrated_y),
                    'hit_button': hit_button,
                    'timestamp': time.time()
                }
                touch_hits.append(touch_hit)
                
                print(f"👆 触摸: 原始({raw_x}, {raw_y}) → 校准({calibrated_x}, {calibrated_y}) → {hit_button or '未命中'}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 鼠标点击（用于调试）
                mouse_x, mouse_y = event.pos
                hit_button = None
                for button in test_buttons:
                    if button['rect'].collidepoint(mouse_x, mouse_y):
                        hit_button = button['text']
                        break
                print(f"🖱️ 鼠标点击: ({mouse_x}, {mouse_y}) → {hit_button or '未命中'}")
        
        # 绘制界面
        screen.fill((30, 30, 30))  # 深灰色背景
        
        # 标题
        title = font_large.render("Quick Touch Test", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=screen_width // 2, y=20)
        screen.blit(title, title_rect)
        
        # 校准信息
        calibration_text = f"校准偏移: ({calibration_offset_x:+d}, {calibration_offset_y:+d}) 像素"
        calibration_surface = font_medium.render(calibration_text, True, (200, 200, 100))
        calibration_rect = calibration_surface.get_rect(centerx=screen_width // 2, y=60)
        screen.blit(calibration_surface, calibration_rect)
        
        # 绘制测试按钮
        for button in test_buttons:
            pygame.draw.rect(screen, button['color'], button['rect'])
            pygame.draw.rect(screen, (255, 255, 255), button['rect'], 3)
            
            text_surface = font_medium.render(button['text'], True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=button['rect'].center)
            screen.blit(text_surface, text_rect)
        
        # 绘制最近的触摸点
        for i, touch in enumerate(touch_hits[-5:]):  # 显示最近5次触摸
            alpha = 255 - i * 40  # 逐渐淡化
            if alpha > 0:
                raw_pos = touch['raw_pos']
                calibrated_pos = touch['calibrated_pos']
                
                # 绘制原始触摸点（红色）
                pygame.draw.circle(screen, (255, 0, 0), raw_pos, 6)
                
                # 绘制校准后的触摸点（绿色）
                pygame.draw.circle(screen, (0, 255, 0), calibrated_pos, 8)
                
                # 绘制连接线
                pygame.draw.line(screen, (100, 100, 100), raw_pos, calibrated_pos, 2)
        
        # 绘制说明
        instructions = [
            "🎯 点击彩色按钮测试触摸精度",
            "🔴 红点=原始触摸位置, 🟢 绿点=校准后位置",
            "🚪 按ESC键退出测试"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font_medium.render(instruction, True, (180, 180, 180))
            screen.blit(text, (20, screen_height - 80 + i * 25))
        
        # 显示统计
        if touch_hits:
            hits = sum(1 for touch in touch_hits if touch['hit_button'])
            accuracy = hits / len(touch_hits) * 100
            stats_text = f"触摸: {len(touch_hits)} 次, 命中: {hits} 次, 准确率: {accuracy:.1f}%"
            stats_surface = font_medium.render(stats_text, True, (100, 255, 100))
            screen.blit(stats_surface, (screen_width - 400, 100))
        
        pygame.display.flip()
        clock.tick(60)
    
    # 测试结果报告
    print("\n" + "=" * 50)
    print("📊 快速触摸测试结果")
    print("=" * 50)
    
    if touch_hits:
        total_touches = len(touch_hits)
        successful_hits = sum(1 for touch in touch_hits if touch['hit_button'])
        accuracy = successful_hits / total_touches * 100
        
        print(f"总触摸次数: {total_touches}")
        print(f"成功命中: {successful_hits}")
        print(f"准确率: {accuracy:.1f}%")
        
        if accuracy >= 80:
            print("✅ 触摸精度良好，修复有效！")
        elif accuracy >= 60:
            print("⚠️ 触摸精度尚可，可能需要进一步调整校准偏移")
        else:
            print("❌ 触摸精度较差，需要调试硬件或校准参数")
            
        print(f"\n💡 当前使用的校准偏移: ({calibration_offset_x}, {calibration_offset_y})")
        print("   如果准确率较低，可以尝试调整这个偏移值")
    else:
        print("⚠️ 没有检测到触摸事件")
        print("   请检查:")
        print("   1. 触摸屏硬件连接")
        print("   2. 触摸驱动是否正常")
        print("   3. 是否在HyperPixel设备上运行")
    
    pygame.quit()
    return True

if __name__ == "__main__":
    print("🚀 Obscura No.7 - 快速触摸测试工具")
    print("=" * 50)
    
    try:
        success = quick_touch_test()
        if success:
            print("✅ 测试完成")
        else:
            print("❌ 测试失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 