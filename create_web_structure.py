#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Structure Generator for Obscura No.7
生成蒸汽朋克风格前端的文件夹结构和空文件
"""

import os
import sys

def create_frontend_structure():
    """创建前端项目的文件夹结构和空文件"""
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(script_dir, 'api')
    
    # 定义需要创建的目录结构
    directories = [
        'api/static',
        'api/static/css',
        'api/static/js',
        'api/static/images',
        'api/templates',
        'api/routes'
    ]
    
    # 定义需要创建的空文件
    files = {
        # CSS文件
        'api/static/css/main.css': '/* Obscura No.7 - Steampunk Main Styles */\n',
        'api/static/css/gallery.css': '/* Gallery-specific Steampunk Styles */\n',
        
        # JavaScript文件
        'api/static/js/main.js': '// Obscura No.7 - Main JavaScript\n',
        'api/static/js/gallery.js': '// Gallery functionality\n',
        
        # HTML模板文件
        'api/templates/base.html': '<!-- Base template for Obscura No.7 -->\n',
        'api/templates/home.html': '<!-- Home page template -->\n',
        'api/templates/gallery.html': '<!-- Gallery page template -->\n',
        
        # 路由文件
        'api/routes/frontend.py': '# Frontend routes for Obscura No.7\n'
    }
    
    print("🔧 Creating Obscura No.7 Frontend Structure...")
    print("=" * 50)
    
    # 创建目录
    for directory in directories:
        dir_path = os.path.join(script_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")
    
    print()
    
    # 创建文件
    for file_path, initial_content in files.items():
        full_path = os.path.join(script_dir, file_path)
        
        if not os.path.exists(full_path):
            # 创建文件并写入初始内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(initial_content)
            print(f"✅ Created file: {file_path}")
        else:
            print(f"📄 File already exists: {file_path}")
    
    print()
    print("🎯 Frontend Structure Summary:")
    print("=" * 50)
    print("📂 Directories:")
    for directory in directories:
        print(f"   - {directory}")
    
    print("\n📄 Files:")
    for file_path in files.keys():
        print(f"   - {file_path}")
    
    print("\n🚀 Next Steps:")
    print("1. Run this script to create the structure")
    print("2. Implement CSS files (main.css, gallery.css)")
    print("3. Implement JavaScript files (main.js, gallery.js)")
    print("4. Implement HTML templates (base.html, home.html, gallery.html)")
    print("5. Implement frontend routes (frontend.py)")
    print("6. Update main app.py to use templates")
    
    print("\n⚙️ Steampunk Theme Elements to Include:")
    print("- Brass and copper color palette")
    print("- Mechanical gear animations")
    print("- Victorian-era typography")
    print("- Steam and metal textures")
    print("- Vintage telescope imagery")
    
    return True

def check_structure():
    """检查当前的项目结构"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(script_dir, 'api')
    
    print("🔍 Current Project Structure:")
    print("=" * 50)
    
    if os.path.exists(api_dir):
        for root, dirs, files in os.walk(api_dir):
            level = root.replace(script_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("❌ api/ directory not found")
    
    print()

def main():
    """主函数"""
    print("🔭 Obscura No.7 - Frontend Structure Generator")
    print("=" * 60)
    
    # 检查当前结构
    check_structure()
    
    # 询问是否创建结构
    response = input("Do you want to create/update the frontend structure? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        success = create_frontend_structure()
        if success:
            print("\n✅ Frontend structure created successfully!")
            print("📝 You can now proceed to implement the individual files.")
        else:
            print("\n❌ Failed to create frontend structure.")
    else:
        print("Operation cancelled.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()