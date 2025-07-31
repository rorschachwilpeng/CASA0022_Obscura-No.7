#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故事生成唯一性修复验证脚本
测试修复后的故事生成是否真正产生不同的内容
"""

import requests
import json
import time
from datetime import datetime
import hashlib

def test_story_uniqueness_fix():
    """测试故事生成修复的效果"""
    
    base_url = "http://localhost:5000"
    print("🧪 开始验证故事生成唯一性修复...")
    print("=" * 80)
    
    # 步骤1：清理所有故事缓存
    print("\n📝 步骤1：清理所有故事缓存...")
    try:
        clear_url = f"{base_url}/api/v1/images/refresh-all-stories"
        clear_response = requests.post(clear_url)
        
        if clear_response.status_code == 200:
            result = clear_response.json()
            print(f"✅ 缓存清理成功: {result.get('data', {}).get('cleared_cache_count', 0)} 条记录")
        else:
            print(f"⚠️ 缓存清理失败: {clear_response.status_code}")
    except Exception as e:
        print(f"⚠️ 缓存清理请求失败: {e}")
    
    time.sleep(2)  # 等待清理完成
    
    # 步骤2：测试单张图片多次刷新
    print("\n📝 步骤2：测试单张图片的故事刷新唯一性...")
    test_image_id = 1
    stories_from_same_image = []
    
    for i in range(3):
        try:
            print(f"\n🔄 第 {i+1} 次刷新图片 {test_image_id} 的故事...")
            
            # 强制刷新故事
            refresh_url = f"{base_url}/api/v1/images/{test_image_id}/refresh-story"
            refresh_response = requests.post(refresh_url)
            
            if refresh_response.status_code == 200:
                print(f"✅ 故事刷新请求成功")
                
                # 等待刷新完成
                time.sleep(2)
                
                # 获取新故事
                story_url = f"{base_url}/api/v1/images/{test_image_id}/shap-analysis"
                story_response = requests.get(story_url)
                
                if story_response.status_code == 200:
                    story_data = story_response.json()
                    if story_data.get('success'):
                        story = story_data.get('data', {}).get('ai_story', 'No story found')
                        stories_from_same_image.append(story)
                        
                        # 显示故事前50个字符
                        print(f"📖 故事预览: {story[:80]}...")
                        
                        # 检查故事类型
                        if story.startswith('[Simplified Analysis]'):
                            print("🔧 检测到: Fallback模式 + DeepSeek AI故事")
                        elif story.startswith('In a world'):
                            print("🔧 检测到: 动态Fallback故事")
                        elif "Environmental analysis temporarily unavailable" in story:
                            print("❌ 检测到: 旧的固定故事（修复未生效）")
                        else:
                            print("✅ 检测到: 正常SHAP + DeepSeek AI故事")
                    else:
                        print(f"❌ 获取故事失败: {story_data}")
                else:
                    print(f"❌ 获取故事请求失败: {story_response.status_code}")
            else:
                print(f"❌ 刷新故事失败: {refresh_response.status_code}")
                
        except Exception as e:
            print(f"❌ 刷新测试失败: {e}")
    
    # 步骤3：分析同一图片的故事唯一性
    print(f"\n📊 步骤3：分析图片 {test_image_id} 的故事唯一性...")
    if len(stories_from_same_image) >= 2:
        unique_stories = len(set(stories_from_same_image))
        total_stories = len(stories_from_same_image)
        
        print(f"📈 总故事数: {total_stories}")
        print(f"📈 唯一故事数: {unique_stories}")
        print(f"📈 唯一性比率: {unique_stories/total_stories*100:.1f}%")
        
        if unique_stories == total_stories:
            print("✅ 同一图片刷新生成了不同的故事！修复成功！")
        elif unique_stories > 1:
            print("⚠️ 部分故事不同，修复部分生效")
        else:
            print("❌ 所有故事都相同，修复未生效")
            
        # 显示故事差异
        for i, story in enumerate(stories_from_same_image):
            story_hash = hashlib.md5(story.encode()).hexdigest()[:8]
            print(f"故事 {i+1} 哈希: {story_hash}")
    
    # 步骤4：测试不同图片的故事唯一性
    print("\n📝 步骤4：测试不同图片之间的故事唯一性...")
    different_image_stories = {}
    test_image_ids = [1, 2, 3]  # 测试不同图片
    
    for image_id in test_image_ids:
        try:
            print(f"\n📸 测试图片 {image_id}...")
            
            # 刷新故事
            refresh_url = f"{base_url}/api/v1/images/{image_id}/refresh-story"
            refresh_response = requests.post(refresh_url)
            
            time.sleep(1)
            
            # 获取故事
            story_url = f"{base_url}/api/v1/images/{image_id}/shap-analysis"
            story_response = requests.get(story_url)
            
            if story_response.status_code == 200:
                story_data = story_response.json()
                if story_data.get('success'):
                    story = story_data.get('data', {}).get('ai_story', '')
                    different_image_stories[image_id] = story
                    print(f"✅ 获取图片 {image_id} 故事成功")
                    print(f"📖 预览: {story[:60]}...")
        
        except Exception as e:
            print(f"❌ 测试图片 {image_id} 失败: {e}")
    
    # 分析不同图片的故事唯一性
    print(f"\n📊 步骤5：分析不同图片之间的故事唯一性...")
    if len(different_image_stories) >= 2:
        story_values = list(different_image_stories.values())
        unique_stories = len(set(story_values))
        total_stories = len(story_values)
        
        print(f"📈 测试图片数: {total_stories}")
        print(f"📈 唯一故事数: {unique_stories}")
        print(f"📈 唯一性比率: {unique_stories/total_stories*100:.1f}%")
        
        if unique_stories == total_stories:
            print("✅ 不同图片生成了不同的故事！修复成功！")
        elif unique_stories > 1:
            print("⚠️ 部分故事不同，修复部分生效")
        else:
            print("❌ 所有图片故事都相同，问题仍然存在")
            
        # 检查是否还有固定的fallback故事
        fixed_story_count = sum(1 for story in story_values 
                              if "Environmental analysis temporarily unavailable" in story)
        if fixed_story_count > 0:
            print(f"❌ 发现 {fixed_story_count} 个旧的固定故事，修复未完全生效")
        else:
            print("✅ 没有发现旧的固定故事，修复已生效")
    
    # 总结
    print("\n" + "=" * 80)
    print("🎯 修复验证总结:")
    print("✅ 修复内容:")
    print("   - 移除了固定的fallback故事")
    print("   - 在fallback模式下也调用DeepSeek API")
    print("   - 添加了完全动态的故事生成兜底机制")
    print("   - 增强了故事生成的随机性和唯一性")
    
    print("\n🔍 预期结果:")
    print("   - 同一图片刷新应该产生不同故事")
    print("   - 不同图片应该有不同故事")
    print("   - 不再出现'Environmental analysis temporarily unavailable'")
    
    print("\n📝 如果仍有问题，请检查:")
    print("   - DeepSeek API密钥是否正确配置")
    print("   - 网络连接是否正常")
    print("   - 服务器日志中的错误信息")
    
    return different_image_stories


def check_api_connectivity():
    """检查API连接性"""
    print("🔗 检查API连接性...")
    
    try:
        base_url = "http://localhost:5000"
        health_url = f"{base_url}/api/v1/health"
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print("✅ API服务器连接正常")
            return True
        else:
            print(f"❌ API服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        print("💡 请确保服务器正在运行: python app.py")
        return False


if __name__ == "__main__":
    print("🧪 故事生成唯一性修复验证")
    print("=" * 80)
    
    # 检查连接
    if not check_api_connectivity():
        exit(1)
    
    # 运行测试
    try:
        result = test_story_uniqueness_fix()
        print(f"\n✅ 验证完成，测试了 {len(result)} 张图片的故事生成")
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}") 