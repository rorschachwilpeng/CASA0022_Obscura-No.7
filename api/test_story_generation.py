#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试故事生成唯一性
验证不同图片是否生成不同的故事
"""

import requests
import json
import time
from datetime import datetime

def test_story_uniqueness():
    """测试多个图片的故事生成唯一性"""
    
    base_url = "http://localhost:5000"  # 根据实际情况调整
    test_image_ids = [1, 2, 3, 4, 5]  # 测试不同的图片ID
    
    print("🧪 开始测试故事生成唯一性...")
    print("=" * 60)
    
    stories = {}
    
    for image_id in test_image_ids:
        try:
            print(f"\n📖 测试图片 {image_id} 的故事生成...")
            
            # 1. 首先刷新故事（清除缓存）
            refresh_url = f"{base_url}/api/v1/images/{image_id}/refresh-story"
            refresh_response = requests.post(refresh_url)
            
            if refresh_response.status_code == 200:
                print(f"✅ 图片 {image_id} 故事缓存已清除")
            else:
                print(f"⚠️ 图片 {image_id} 缓存清除失败，继续测试...")
            
            # 等待一秒确保时间戳不同
            time.sleep(1)
            
            # 2. 获取SHAP分析数据（包含故事）
            shap_url = f"{base_url}/api/v1/images/{image_id}/shap-analysis"
            response = requests.get(shap_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    story = data['data'].get('ai_story', 'No story found')
                    stories[image_id] = story
                    
                    print(f"✅ 故事生成成功")
                    print(f"📝 故事长度: {len(story)} 字符")
                    print(f"🔍 故事前100字符: {story[:100]}...")
                else:
                    print(f"❌ 数据格式错误: {data}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试图片 {image_id} 时出错: {e}")
    
    # 3. 分析结果
    print("\n" + "=" * 60)
    print("📊 分析结果:")
    
    if len(stories) < 2:
        print("❌ 测试失败：生成的故事数量不足")
        return
    
    # 检查故事是否相同
    story_list = list(stories.values())
    unique_stories = set(story_list)
    
    print(f"📈 总共生成 {len(story_list)} 个故事")
    print(f"🎯 其中唯一故事 {len(unique_stories)} 个")
    
    if len(unique_stories) == len(story_list):
        print("✅ 测试通过：所有故事都是唯一的！")
    else:
        print("❌ 测试失败：发现重复的故事")
        
        # 找出重复的故事
        seen = set()
        duplicates = set()
        for story in story_list:
            if story in seen:
                duplicates.add(story)
            else:
                seen.add(story)
        
        print(f"🔍 重复故事数量: {len(duplicates)}")
    
    # 显示所有故事的详细信息
    print("\n" + "=" * 60)
    print("📚 所有生成的故事:")
    
    for image_id, story in stories.items():
        print(f"\n【图片 {image_id}】")
        print(f"故事: {story}")
        print(f"长度: {len(story)} 字符")
        print("-" * 40)
    
    return len(unique_stories) == len(story_list)

def test_single_image_multiple_refreshes(image_id=1, refresh_count=3):
    """测试单个图片多次刷新是否生成不同故事"""
    
    base_url = "http://localhost:5000"
    
    print(f"\n🔄 测试图片 {image_id} 多次刷新故事...")
    print("=" * 60)
    
    stories = []
    
    for i in range(refresh_count):
        try:
            print(f"\n🔄 第 {i+1} 次刷新...")
            
            # 刷新故事
            refresh_url = f"{base_url}/api/v1/images/{image_id}/refresh-story"
            refresh_response = requests.post(refresh_url)
            
            if refresh_response.status_code == 200:
                print(f"✅ 第 {i+1} 次刷新成功")
                
                # 等待确保时间戳不同
                time.sleep(2)
                
                # 获取新故事
                shap_url = f"{base_url}/api/v1/images/{image_id}/shap-analysis"
                response = requests.get(shap_url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and 'data' in data:
                        story = data['data'].get('ai_story', 'No story found')
                        stories.append(story)
                        print(f"📝 获取故事成功，长度: {len(story)} 字符")
                    else:
                        print(f"❌ 数据格式错误")
                else:
                    print(f"❌ 获取故事失败: {response.status_code}")
            else:
                print(f"❌ 刷新失败: {refresh_response.status_code}")
                
        except Exception as e:
            print(f"❌ 第 {i+1} 次刷新出错: {e}")
    
    # 分析结果
    print("\n" + "=" * 60)
    print("📊 多次刷新分析结果:")
    
    unique_stories = set(stories)
    print(f"📈 总共刷新 {len(stories)} 次")
    print(f"🎯 生成唯一故事 {len(unique_stories)} 个")
    
    if len(unique_stories) == len(stories):
        print("✅ 测试通过：每次刷新都生成了不同的故事！")
    else:
        print("❌ 测试失败：发现重复的故事")
    
    for i, story in enumerate(stories):
        print(f"\n【第 {i+1} 次】")
        print(f"故事: {story[:100]}...")
        print(f"长度: {len(story)} 字符")
    
    return len(unique_stories) == len(stories)

if __name__ == "__main__":
    print("🎬 Obscura No.7 故事生成唯一性测试")
    print("=" * 60)
    
    # 测试1: 不同图片的故事唯一性
    result1 = test_story_uniqueness()
    
    # 测试2: 单个图片多次刷新的故事唯一性
    result2 = test_single_image_multiple_refreshes()
    
    print("\n" + "=" * 60)
    print("🏁 最终测试结果:")
    print(f"📊 不同图片故事唯一性: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"🔄 单图片刷新唯一性: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n🎉 所有测试通过！故事生成唯一性问题已修复！")
    else:
        print("\n⚠️ 仍存在问题，需要进一步调试。") 