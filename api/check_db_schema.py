#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def check_database_schema():
    """检查数据库架构和外键关系"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL 环境变量未设置")
            return

        print(f"🔗 连接到数据库...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # 1. 检查所有表
        print("\n📋 检查所有表:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            print(f"  - {table[0]}")

        # 2. 检查外键约束
        print("\n🔗 检查外键约束:")
        cursor.execute("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        foreign_keys = cursor.fetchall()
        for fk in foreign_keys:
            print(f"  {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]} (约束: {fk[4]})")

        # 3. 检查主要表的结构
        main_tables = ['images', 'predictions', 'environmental_data', 'image_analysis']
        
        for table_name in main_tables:
            print(f"\n📊 检查表 '{table_name}' 的结构:")
            try:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                if columns:
                    print(f"  表 '{table_name}' 存在，包含以下列:")
                    for col in columns:
                        nullable = "可空" if col[2] == "YES" else "不可空"
                        default = f"默认值: {col[3]}" if col[3] else "无默认值"
                        print(f"    - {col[0]} ({col[1]}) - {nullable}, {default}")
                else:
                    print(f"  ❌ 表 '{table_name}' 不存在")
                    
            except Exception as e:
                print(f"  ❌ 检查表 '{table_name}' 时出错: {e}")

        # 4. 检查数据量
        print(f"\n📈 检查数据量:")
        for table_name in main_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} 条记录")
            except Exception as e:
                print(f"  {table_name}: 表不存在或查询失败 - {e}")

        cursor.close()
        conn.close()
        
        print("\n✅ 数据库架构检查完成!")
        
    except Exception as e:
        print(f"❌ 数据库连接或查询失败: {e}")

if __name__ == "__main__":
    check_database_schema() 