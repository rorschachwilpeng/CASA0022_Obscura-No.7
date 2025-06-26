#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 主启动脚本
整合硬件交互和云端工作流的统一入口
"""

import sys
import signal
import json
 import sys
+ import os
+ sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+ from enhanced_telescope import EnhancedTelescope
from obscura_workflow import ObscuraWorkflow
from progress_display import ProgressDisplay
from config_manager import ConfigManager

class MainTelescope:
    def __init__(self):
        """初始化主控制器"""
        self.config = ConfigManager().load_config()
        
        # 初始化各模块
        self.hardware = EnhancedTelescope(
            api_key=self.config['google_maps_api_key'],
            distance_bus=3,
            compass_bus=4, 
            time_bus=5,
            encoder_addr=0x36
        )
        
        self.workflow = ObscuraWorkflow(self.config)
        self.progress = ProgressDisplay()
        
    def run_complete_session(self):
        """运行完整的Obscura No.7会话"""
        print("🌟 启动 Obscura No.7 完整会话...")
        
        try:
            # Phase 1: 硬件参数选择
            print("\n🎮 Phase 1: 硬件参数选择")
            params = self.hardware.run_enhanced_telescope_session()
            
            if not params:
                print("❌ 参数选择失败或用户取消")
                return False
            
            # Phase 2: 云端工作流执行
            print("\n🌐 Phase 2: 云端AI工作流")
            result = self.workflow.execute_full_pipeline(
                distance=params['distance'],
                direction=params['direction'], 
                target_year=params['target_year']
            )
            
            # Phase 3: 结果展示
            if result:
                print("\n🎉 Phase 3: 结果展示")
                self._show_final_result(result)
                return True
            else:
                print("❌ 云端工作流执行失败")
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断会话")
            return False
        except Exception as e:
            print(f"\n❌ 会话错误: {e}")
            return False
    
    def _show_final_result(self, result):
        """显示最终结果"""
        # TODO: 实现结果展示界面
        print("🎊 Obscura No.7 预测完成!")
        print(f"🌐 查看结果: {result.get('website_url', 'N/A')}")
        print(f"🎨 图片ID: {result.get('image_id', 'N/A')}")

def signal_handler(sig, frame):
    print("\n\n🛑 收到中断信号，正在退出...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    telescope = MainTelescope()
    success = telescope.run_complete_session()
    
    if success:
        print("🏁 Obscura No.7 会话成功完成")
    else:
        print("💥 Obscura No.7 会话异常结束")

if __name__ == "__main__":
    main()
