#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行所有测试脚本
完整验证Obscura No.7系统功能
"""

import subprocess
import sys
import os
from datetime import datetime

def run_test_script(script_name, description):
    """运行单个测试脚本"""
    print(f"\n{'='*60}")
    print(f"🚀 运行测试: {description}")
    print(f"📁 脚本: {script_name}")
    print(f"{'='*60}")
    
    try:
        if os.path.exists(script_name):
            result = subprocess.run([sys.executable, script_name], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {description} - 测试成功")
                print(result.stdout)
                return True
            else:
                print(f"❌ {description} - 测试失败")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
        else:
            print(f"❌ 脚本文件不存在: {script_name}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 测试超时")
        return False
    except Exception as e:
        print(f"❌ {description} - 运行异常: {e}")
        return False

def main():
    """主函数"""
    print("🎯 Obscura No.7 - 完整系统测试套件")
    print("=" * 60)
    print(f"🚀 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 云端API: https://casa0022-obscura-no-7.onrender.com")
    print("=" * 60)
    
    # 测试脚本列表
    tests = [
        {
            'script': 'quick_api_test.py',
            'description': '快速API连通性测试',
            'critical': True
        },
        {
            'script': 'test_website_frontend.py',
            'description': '网站前端功能测试',
            'critical': True
        },
        {
            'script': 'test_raspberry_pi_simulation.py',
            'description': '树莓派完整工作流模拟测试',
            'critical': True
        },
        {
            'script': 'test_complete_workflow.py',
            'description': '端到端工作流验证',
            'critical': False
        }
    ]
    
    results = []
    
    # 运行所有测试
    for test in tests:
        success = run_test_script(test['script'], test['description'])
        results.append({
            'name': test['description'],
            'success': success,
            'critical': test['critical']
        })
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    critical_tests = [r for r in results if r['critical']]
    critical_passed = sum(1 for r in critical_tests if r['success'])
    
    print(f"📈 总体统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过测试: {passed_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
    print(f"   关键测试: {len(critical_tests)} ({critical_passed} 通过)")
    
    print(f"\n📋 详细结果:")
    for result in results:
        status = "✅ 通过" if result['success'] else "❌ 失败"
        critical = "🔴 关键" if result['critical'] else "🟡 一般"
        print(f"   {status} {critical} {result['name']}")
    
    # 判断整体状态
    if critical_passed == len(critical_tests):
        print(f"\n🎉 系统状态: 全部就绪！")
        print("✅ 所有关键测试通过")
        print("🚀 可以开始使用系统")
        
        print(f"\n🌐 你可以访问以下链接:")
        print("   主页: https://casa0022-obscura-no-7.onrender.com/")
        print("   预测页面: https://casa0022-obscura-no-7.onrender.com/prediction")
        print("   图库: https://casa0022-obscura-no-7.onrender.com/gallery")
        
        print(f"\n🎯 下一步行动:")
        print("   1. 在浏览器中测试预测页面")
        print("   2. 准备树莓派硬件连接")
        print("   3. 配置Tailscale网络")
        print("   4. 部署真实的树莓派代码")
        
    elif critical_passed > 0:
        print(f"\n⚠️ 系统状态: 部分功能可用")
        print("❌ 部分关键测试失败")
        print("🔧 需要修复问题后再试")
        
    else:
        print(f"\n❌ 系统状态: 需要排查问题")
        print("💥 关键测试全部失败")
        print("🚨 请检查云端API状态")
    
    print(f"\n🏁 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 交互式选项
    print("\n" + "=" * 60)
    print("🎮 交互式选项")
    print("1. 在浏览器中打开网站")
    print("2. 运行特定测试")
    print("3. 查看系统状态")
    print("4. 退出")
    
    while True:
        choice = input("\n选择操作 (1-4): ").strip()
        
        if choice == '1':
            import webbrowser
            webbrowser.open('https://casa0022-obscura-no-7.onrender.com/')
            webbrowser.open('https://casa0022-obscura-no-7.onrender.com/prediction')
            print("🌐 已在浏览器中打开网站")
            
        elif choice == '2':
            print("\n可运行的测试:")
            for i, test in enumerate(tests, 1):
                print(f"{i}. {test['description']}")
            
            try:
                test_choice = int(input("选择测试编号: ")) - 1
                if 0 <= test_choice < len(tests):
                    selected_test = tests[test_choice]
                    run_test_script(selected_test['script'], selected_test['description'])
                else:
                    print("❌ 无效的测试编号")
            except ValueError:
                print("❌ 请输入有效数字")
                
        elif choice == '3':
            # 快速状态检查
            print("\n🔍 快速状态检查...")
            subprocess.run([sys.executable, 'quick_api_test.py'])
            
        elif choice == '4':
            print("👋 测试结束，再见！")
            break
            
        else:
            print("❌ 无效选择，请选择 1-4")

if __name__ == "__main__":
    main() 