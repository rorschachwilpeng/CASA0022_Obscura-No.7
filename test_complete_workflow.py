#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整Obscura工作流 - 自动化测试脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obscura_workflow import ObscuraWorkflow

def main():
    print("🚀 启动完整Obscura工作流自动化测试")
    print("=" * 60)
    
    try:
        # 初始化工作流
        workflow = ObscuraWorkflow()
        
        # 运行完整工作流
        print("🔭 执行完整工作流...")
        result = workflow.run_complete_workflow()
        
        # 显示结果
        print("\n" + "=" * 60)
        print("📊 工作流执行结果:")
        print(f"✅ 成功状态: {result.get('success', False)}")
        print(f"🕐 执行时间: {result.get('execution_time', 0):.2f} 秒")
        
        if result.get('data', {}).get('generated_image'):
            print(f"🎨 生成图像: {result['data']['generated_image']}")
        
        if result.get('upload_result', {}).get('success'):
            upload = result['upload_result']
            print(f"☁️ 网站上传: 成功")
            if upload.get('image_data', {}).get('image', {}).get('url'):
                print(f"🌐 图像URL: {upload['image_data']['image']['url']}")
        else:
            print("☁️ 网站上传: 失败或跳过")
        
        print("\n🎯 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 