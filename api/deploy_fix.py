#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署修复脚本 - 解决pandas依赖问题
"""

import sys
import os

def check_dependencies():
    """检查关键依赖是否可用"""
    deps_status = {}
    
    # 检查pandas
    try:
        import pandas as pd
        deps_status['pandas'] = True
        print("✅ pandas可用")
    except ImportError:
        deps_status['pandas'] = False
        print("❌ pandas不可用")
    
    # 检查numpy
    try:
        import numpy as np
        deps_status['numpy'] = True
        print("✅ numpy可用")
    except ImportError:
        deps_status['numpy'] = False
        print("❌ numpy不可用")
    
    # 检查shap
    try:
        import shap
        deps_status['shap'] = True
        print("✅ shap可用")
    except ImportError:
        deps_status['shap'] = False
        print("❌ shap不可用")
    
    # 检查scikit-learn
    try:
        import sklearn
        deps_status['sklearn'] = True
        print("✅ scikit-learn可用")
    except ImportError:
        deps_status['sklearn'] = False
        print("❌ scikit-learn不可用")
    
    return deps_status

def create_minimal_app():
    """创建最小化Flask应用，绕过SHAP依赖"""
    from flask import Flask, jsonify, render_template
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return render_template('home.html', 
            openweather_status=False,
            openai_status=False,
            google_maps_status=False,
            cloudinary_status=False,
            database_status=False,
            workflow_status=False
        )
    
    @app.route('/api/v1/shap/predict', methods=['POST'])
    def shap_predict():
        return jsonify({
            "success": False,
            "error": "SHAP服务正在部署中，暂时不可用",
            "code": 503,
            "error_type": "service_unavailable"
        }), 503
    
    @app.route('/health')
    def health():
        return jsonify({"status": "basic", "shap_available": False})
    
    return app

if __name__ == '__main__':
    print("🔧 检查部署环境...")
    deps = check_dependencies()
    
    if deps.get('pandas', False):
        print("✅ 依赖检查通过，启动完整应用")
        # 导入完整应用
        from app import create_app
        app = create_app()
    else:
        print("⚠️ 依赖缺失，启动最小化应用")
        app = create_minimal_app()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 