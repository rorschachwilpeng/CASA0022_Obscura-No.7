#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理Gallery中所有图片的脚本
"""

import os
import sys
import psycopg2
import cloudinary
import cloudinary.uploader
from datetime import datetime
import json

def clear_database_images():
    """清理数据库中的所有图片数据"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL 环境变量未设置")
            return False
        
        print(f"🔗 正在连接数据库...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 查询将被删除的图片数量
        cur.execute("SELECT COUNT(*) FROM images")
        image_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM image_analysis")
        analysis_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM predictions")
        prediction_count = cur.fetchone()[0]
        
        if image_count == 0 and analysis_count == 0 and prediction_count == 0:
            print("📋 数据库中没有找到任何需要删除的记录")
            return True
        
        print(f"📊 即将删除:")
        print(f"  - 图片记录: {image_count} 条")
        print(f"  - 分析记录: {analysis_count} 条")
        print(f"  - 预测记录: {prediction_count} 条")
        
        # 获取用户确认
        confirm = input("\n⚠️  确定要删除所有数据吗? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return False
        
        print("🗑️  正在删除数据...")
        
        # 按照外键依赖关系删除数据
        # 1. 删除image_analysis表（依赖images表）
        cur.execute("DELETE FROM image_analysis")
        print(f"✅ 已删除 {analysis_count} 条分析记录")
        
        # 2. 删除images表
        cur.execute("DELETE FROM images")
        print(f"✅ 已删除 {image_count} 条图片记录")
        
        # 3. 删除predictions表
        cur.execute("DELETE FROM predictions")
        print(f"✅ 已删除 {prediction_count} 条预测记录")
        
        # 重置自增序列
        cur.execute("ALTER SEQUENCE images_id_seq RESTART WITH 1")
        cur.execute("ALTER SEQUENCE image_analysis_id_seq RESTART WITH 1")
        cur.execute("ALTER SEQUENCE predictions_id_seq RESTART WITH 1")
        print("✅ 已重置ID序列")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ 数据库清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")
        return False

def clear_cloudinary_images():
    """清理Cloudinary中的图片"""
    try:
        cloudinary_url = os.getenv("CLOUDINARY_URL")
        if not cloudinary_url:
            print("❌ CLOUDINARY_URL 环境变量未设置")
            return False
        
        print("☁️  正在连接Cloudinary...")
        cloudinary.config()
        
        # 获取obscura_images文件夹中的所有图片
        try:
            result = cloudinary.api.resources(
                type="upload",
                prefix="obscura_images/",
                max_results=500
            )
            
            resources = result.get('resources', [])
            
            if not resources:
                print("📋 Cloudinary中没有找到obscura_images文件夹下的图片")
                return True
            
            print(f"📊 找到 {len(resources)} 个图片文件")
            
            # 获取用户确认
            confirm = input(f"\n⚠️  确定要删除Cloudinary中的 {len(resources)} 个图片吗? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ 操作已取消")
                return False
            
            print("🗑️  正在删除Cloudinary图片...")
            
            # 批量删除图片
            public_ids = [resource['public_id'] for resource in resources]
            
            if public_ids:
                delete_result = cloudinary.api.delete_resources(public_ids)
                deleted_count = len(delete_result.get('deleted', {}))
                print(f"✅ 已删除 {deleted_count} 个图片文件")
            
            print("✅ Cloudinary清理完成")
            return True
            
        except Exception as api_error:
            print(f"❌ Cloudinary API调用失败: {api_error}")
            return False
        
    except Exception as e:
        print(f"❌ Cloudinary清理失败: {e}")
        return False

def clear_local_storage():
    """清理本地存储的图片数据"""
    print("🔍 清理本地存储的图片数据...")
    
    try:
        # 导入本地存储
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from routes.images import LOCAL_IMAGES_STORE, LOCAL_ANALYSIS_STORE
        
        image_count = len(LOCAL_IMAGES_STORE)
        analysis_count = len(LOCAL_ANALYSIS_STORE)
        
        if image_count == 0 and analysis_count == 0:
            print("📋 本地存储中没有找到需要清理的数据")
            return True
        
        print(f"📊 即将清理:")
        print(f"  - 本地图片记录: {image_count} 条")
        print(f"  - 本地分析记录: {analysis_count} 条")
        
        # 获取用户确认
        confirm = input("\n⚠️  确定要清理本地存储吗? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return False
        
        # 清理本地存储
        LOCAL_IMAGES_STORE.clear()
        LOCAL_ANALYSIS_STORE.clear()
        
        print("✅ 本地存储清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 本地存储清理失败: {e}")
        return False

def main():
    """主函数"""
    print("🔭 OBSCURA No.7 - Gallery 图片清理工具")
    print("=" * 80)
    
    print("请选择清理选项:")
    print("1. 清理数据库中的所有图片数据")
    print("2. 清理Cloudinary中的所有图片文件")
    print("3. 清理本地存储中的图片数据")
    print("4. 全部清理（数据库 + Cloudinary + 本地存储）")
    print("5. 退出")
    
    choice = input("\n请输入选项 (1-5): ")
    
    if choice == '1':
        clear_database_images()
    elif choice == '2':
        clear_cloudinary_images()
    elif choice == '3':
        clear_local_storage()
    elif choice == '4':
        print("🔄 开始全面清理...")
        print("\n" + "=" * 40)
        print("第1步: 清理数据库")
        clear_database_images()
        print("\n" + "=" * 40)
        print("第2步: 清理Cloudinary")
        clear_cloudinary_images()
        print("\n" + "=" * 40)
        print("第3步: 清理本地存储")
        clear_local_storage()
        print("\n" + "=" * 40)
        print("✅ 全面清理完成!")
    elif choice == '5':
        print("👋 退出清理工具")
        return
    else:
        print("❌ 无效的选项")
        return

if __name__ == "__main__":
    main() 