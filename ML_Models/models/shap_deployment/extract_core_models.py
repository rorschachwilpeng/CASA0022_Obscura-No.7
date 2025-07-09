#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型核心提取器 - 从复杂SHAP模型中提取纯scikit-learn核心

解决云端部署时的依赖问题
"""

import os
import sys
import json
import joblib
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

def extract_core_models():
    """从复杂模型中提取纯scikit-learn核心"""
    
    models_dir = Path(__file__).parent
    cities = ['london', 'manchester', 'edinburgh']
    
    print("🔧 开始提取模型核心...")
    print("="*50)
    
    extraction_report = {
        'extraction_timestamp': datetime.now().isoformat(),
        'extracted_models': {},
        'summary': {}
    }
    
    for city in cities:
        city_dir = models_dir / city
        if not city_dir.exists():
            continue
            
        print(f"\n🏙️ 处理 {city.title()} 模型...")
        
        city_models = {}
        
        # 处理Climate Model
        climate_file = city_dir / f"{city.title()}_climate_model.joblib"
        if climate_file.exists():
            try:
                print(f"   📊 加载 {city.title()} Climate Model...")
                complex_model = joblib.load(climate_file)
                
                # 提取核心scikit-learn模型
                if isinstance(complex_model, dict) and 'model' in complex_model:
                    core_model = complex_model['model']
                    feature_names = complex_model.get('feature_names', [])
                    
                    # 保存简化版本
                    simple_model = {
                        'model': core_model,
                        'feature_names': feature_names,
                        'model_type': 'climate',
                        'city': city.title(),
                        'extraction_timestamp': datetime.now().isoformat()
                    }
                    
                    simple_file = city_dir / f"{city.title()}_climate_model_simple.joblib"
                    joblib.dump(simple_model, simple_file)
                    
                    city_models['climate'] = {
                        'original_file': str(climate_file),
                        'simple_file': str(simple_file),
                        'status': 'success',
                        'feature_count': len(feature_names) if feature_names else 'unknown'
                    }
                    
                    print(f"   ✅ Climate Model 核心提取成功")
                    
                else:
                    print(f"   ⚠️ Climate Model 结构不符合预期")
                    city_models['climate'] = {'status': 'unexpected_structure'}
                    
            except Exception as e:
                print(f"   ❌ Climate Model 提取失败: {e}")
                city_models['climate'] = {'status': 'failed', 'error': str(e)}
        
        # 处理Geographic Model
        geo_file = city_dir / f"{city.title()}_geographic_model.joblib"
        if geo_file.exists():
            try:
                print(f"   🌍 加载 {city.title()} Geographic Model...")
                complex_model = joblib.load(geo_file)
                
                # 提取核心scikit-learn模型
                if isinstance(complex_model, dict) and 'model' in complex_model:
                    core_model = complex_model['model']
                    feature_names = complex_model.get('feature_names', [])
                    
                    # 保存简化版本
                    simple_model = {
                        'model': core_model,
                        'feature_names': feature_names,
                        'model_type': 'geographic',
                        'city': city.title(),
                        'extraction_timestamp': datetime.now().isoformat()
                    }
                    
                    simple_file = city_dir / f"{city.title()}_geographic_model_simple.joblib"
                    joblib.dump(simple_model, simple_file)
                    
                    city_models['geographic'] = {
                        'original_file': str(geo_file),
                        'simple_file': str(simple_file),
                        'status': 'success',
                        'feature_count': len(feature_names) if feature_names else 'unknown'
                    }
                    
                    print(f"   ✅ Geographic Model 核心提取成功")
                    
                else:
                    print(f"   ⚠️ Geographic Model 结构不符合预期")
                    city_models['geographic'] = {'status': 'unexpected_structure'}
                    
            except Exception as e:
                print(f"   ❌ Geographic Model 提取失败: {e}")
                city_models['geographic'] = {'status': 'failed', 'error': str(e)}
        
        extraction_report['extracted_models'][city] = city_models
    
    # 更新部署清单，指向简化模型
    print(f"\n📝 更新部署清单...")
    
    manifest_file = models_dir / 'deployment_manifest.json'
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # 更新模型路径为简化版本
        for city in cities:
            if city.title() in manifest['models']:
                city_config = manifest['models'][city.title()]
                city_config['climate_model'] = f'{city}/{city.title()}_climate_model_simple.joblib'
                city_config['geographic_model'] = f'{city}/{city.title()}_geographic_model_simple.joblib'
        
        # 保存更新的清单
        simple_manifest_file = models_dir / 'deployment_manifest_simple.json'
        with open(simple_manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        extraction_report['manifest_updated'] = str(simple_manifest_file)
        print(f"   ✅ 部署清单已更新: {simple_manifest_file}")
    
    # 保存提取报告
    report_file = models_dir / 'extraction_report.json'
    with open(report_file, 'w') as f:
        json.dump(extraction_report, f, indent=2)
    
    # 统计结果
    total_models = 0
    successful_models = 0
    
    for city_data in extraction_report['extracted_models'].values():
        for model_data in city_data.values():
            total_models += 1
            if model_data.get('status') == 'success':
                successful_models += 1
    
    extraction_report['summary'] = {
        'total_models': total_models,
        'successful_extractions': successful_models,
        'success_rate': f"{(successful_models/total_models*100):.1f}%" if total_models > 0 else "0%"
    }
    
    print(f"\n" + "="*50)
    print(f"🎉 模型核心提取完成！")
    print(f"✅ 成功提取: {successful_models}/{total_models} 个模型")
    print(f"📊 成功率: {extraction_report['summary']['success_rate']}")
    print(f"📁 提取报告: {report_file}")
    
    return extraction_report

if __name__ == '__main__':
    try:
        report = extract_core_models()
        print(f"\n🎯 下一步：将简化模型部署到云端")
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc() 