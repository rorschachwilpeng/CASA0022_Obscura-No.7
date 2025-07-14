#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库架构修复脚本 - 修复predictions表中缺少的字段
"""

import os
import psycopg2
from datetime import datetime

def fix_predictions_table():
    """修复predictions表，添加缺少的字段"""
    
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL环境变量未设置")
            return False
        
        print("🔗 正在连接数据库...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 检查predictions表的现有结构
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'predictions'
            ORDER BY ordinal_position
        """)
        
        current_columns = cur.fetchall()
        print("📋 当前predictions表结构:")
        for col in current_columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        # 检查是否需要添加字段
        existing_column_names = [col[0] for col in current_columns]
        
        columns_to_add = []
        
        # 检查并添加缺少的字段
        required_columns = [
            ('temperature', 'FLOAT'),
            ('humidity', 'FLOAT'),
            ('pressure', 'FLOAT'),
            ('wind_speed', 'FLOAT'),
            ('predicted_pressure', 'FLOAT'),
            ('predicted_wind_speed', 'FLOAT')
        ]
        
        for col_name, col_type in required_columns:
            if col_name not in existing_column_names:
                columns_to_add.append((col_name, col_type))
        
        if not columns_to_add:
            print("✅ 所有必需字段都已存在，无需修改")
            return True
        
        print(f"🔧 需要添加的字段: {[col[0] for col in columns_to_add]}")
        
        # 添加缺少的字段
        for col_name, col_type in columns_to_add:
            print(f"📝 添加字段: {col_name} ({col_type})")
            cur.execute(f"ALTER TABLE predictions ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        
        # 提交更改
        conn.commit()
        
        print("✅ 数据库架构修复完成!")
        
        # 重新检查表结构
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'predictions'
            ORDER BY ordinal_position
        """)
        
        updated_columns = cur.fetchall()
        print("📋 修复后的predictions表结构:")
        for col in updated_columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库架构修复失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 数据库架构修复工具")
    print("=" * 50)
    
    success = fix_predictions_table()
    
    if success:
        print("\n🎉 数据库架构修复成功!")
        print("现在可以重新测试图片上传API了")
    else:
        print("\n❌ 数据库架构修复失败")
        print("请检查数据库连接和权限")

if __name__ == "__main__":
    main() 