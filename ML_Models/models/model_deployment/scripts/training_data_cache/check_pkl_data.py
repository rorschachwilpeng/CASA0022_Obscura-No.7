#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看PKL训练数据文件的内容
"""

import pickle
import numpy as np
import pandas as pd
import sys
import os

def load_and_analyze_pkl(file_path):
    """加载并分析PKL文件"""
    print(f"🔍 正在分析文件: {file_path}")
    print("=" * 60)
    
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"📊 数据类型: {type(data)}")
        
        if isinstance(data, dict):
            print(f"📋 字典键: {list(data.keys())}")
            print()
            
            for key, value in data.items():
                print(f"🔑 键 '{key}':")
                print(f"   类型: {type(value)}")
                
                if isinstance(value, np.ndarray):
                    print(f"   形状: {value.shape}")
                    print(f"   数据类型: {value.dtype}")
                    print(f"   最小值: {np.min(value):.4f}")
                    print(f"   最大值: {np.max(value):.4f}")
                    print(f"   均值: {np.mean(value):.4f}")
                    print(f"   标准差: {np.std(value):.4f}")
                    
                    # 显示前几个样本
                    if len(value.shape) == 2:
                        print(f"   前3行数据:")
                        print(f"   {value[:3]}")
                    elif len(value.shape) == 1:
                        print(f"   前10个值: {value[:10]}")
                
                elif isinstance(value, list):
                    print(f"   长度: {len(value)}")
                    if len(value) > 0:
                        print(f"   第一个元素类型: {type(value[0])}")
                        print(f"   前3个元素: {value[:3]}")
                
                elif isinstance(value, (int, float)):
                    print(f"   值: {value}")
                
                print()
        
        elif isinstance(data, (np.ndarray, pd.DataFrame)):
            print(f"   形状: {data.shape}")
            print(f"   数据类型: {data.dtype}")
            print(f"   前几行数据:")
            print(data[:5])
        
        else:
            print(f"   内容: {data}")
            
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

def main():
    """主函数"""
    print("🔍 PKL文件内容查看器")
    print("=" * 60)
    
    # 检查当前目录下的PKL文件
    pkl_files = [f for f in os.listdir('.') if f.endswith('.pkl')]
    
    if not pkl_files:
        print("❌ 当前目录没有找到PKL文件")
        return
    
    print(f"📁 找到的PKL文件: {pkl_files}")
    print()
    
    for pkl_file in pkl_files:
        load_and_analyze_pkl(pkl_file)
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main() 