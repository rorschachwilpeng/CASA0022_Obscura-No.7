#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型下载工具
支持从云存储下载大型模型文件到Render服务器
"""

import os
import sys
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger(__name__)

class ModelDownloader:
    """模型文件下载器"""
    
    def __init__(self):
        self.model_urls = {
            # 如果模型文件太大，可以上传到云存储并从这里下载
            "shap_london_climate": "https://your-cloud-storage.com/models/london_climate.joblib",
            "shap_london_geographic": "https://your-cloud-storage.com/models/london_geographic.joblib",
            "shap_manchester_climate": "https://your-cloud-storage.com/models/manchester_climate.joblib",
            "shap_manchester_geographic": "https://your-cloud-storage.com/models/manchester_geographic.joblib",
            "shap_edinburgh_climate": "https://your-cloud-storage.com/models/edinburgh_climate.joblib",
            "shap_edinburgh_geographic": "https://your-cloud-storage.com/models/edinburgh_geographic.joblib",
        }
        
        # 模型文件的MD5校验值
        self.model_checksums = {
            "shap_london_climate": "expected_md5_hash_here",
            # ... 其他模型的校验值
        }
    
    def download_model(self, model_name: str, target_path: str, 
                      verify_checksum: bool = True) -> bool:
        """
        下载指定模型文件
        
        Args:
            model_name: 模型名称
            target_path: 本地保存路径
            verify_checksum: 是否验证文件完整性
            
        Returns:
            bool: 下载是否成功
        """
        try:
            if model_name not in self.model_urls:
                logger.error(f"未知模型: {model_name}")
                return False
            
            url = self.model_urls[model_name]
            target_file = Path(target_path)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查文件是否已存在且有效
            if target_file.exists() and verify_checksum:
                if self._verify_file_checksum(target_file, model_name):
                    logger.info(f"✅ 模型文件已存在且有效: {model_name}")
                    return True
            
            logger.info(f"🔄 开始下载模型: {model_name}")
            
            # 下载文件
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(target_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 简单进度显示
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # 每MB显示一次
                                logger.info(f"下载进度: {progress:.1f}%")
            
            # 验证文件完整性
            if verify_checksum and not self._verify_file_checksum(target_file, model_name):
                logger.error(f"❌ 文件校验失败: {model_name}")
                target_file.unlink()  # 删除损坏文件
                return False
            
            logger.info(f"✅ 模型下载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型下载失败 {model_name}: {str(e)}")
            return False
    
    def _verify_file_checksum(self, file_path: Path, model_name: str) -> bool:
        """验证文件MD5校验值"""
        try:
            if model_name not in self.model_checksums:
                return True  # 如果没有校验值，跳过验证
            
            expected_md5 = self.model_checksums[model_name]
            
            # 计算文件MD5
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            
            actual_md5 = md5_hash.hexdigest()
            
            if actual_md5 == expected_md5:
                return True
            else:
                logger.error(f"MD5校验失败: 期望 {expected_md5}, 实际 {actual_md5}")
                return False
                
        except Exception as e:
            logger.error(f"校验文件时出错: {str(e)}")
            return False
    
    def download_all_models(self, models_dir: str) -> Dict[str, bool]:
        """
        下载所有模型文件
        
        Args:
            models_dir: 模型存储目录
            
        Returns:
            Dict[str, bool]: 各模型下载结果
        """
        results = {}
        
        for model_name in self.model_urls.keys():
            target_path = os.path.join(models_dir, f"{model_name}.joblib")
            results[model_name] = self.download_model(model_name, target_path)
        
        return results

def ensure_models_available(models_dir: str = "ML_Models/models") -> bool:
    """
    确保模型文件可用
    如果本地没有，尝试下载
    """
    try:
        models_path = Path(models_dir)
        
        # 检查基础模型是否存在
        basic_model = models_path / "simple_environmental_model.pkl"
        if basic_model.exists():
            logger.info("✅ 基础模型文件已存在")
            return True
        
        # 如果启用了模型下载
        if os.getenv("ENABLE_MODEL_DOWNLOAD", "false").lower() == "true":
            logger.info("🔄 启动模型下载...")
            downloader = ModelDownloader()
            results = downloader.download_all_models(str(models_path))
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            logger.info(f"模型下载完成: {success_count}/{total_count}")
            return success_count > 0
        
        return True
        
    except Exception as e:
        logger.error(f"确保模型可用时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试模型下载
    logging.basicConfig(level=logging.INFO)
    downloader = ModelDownloader()
    
    # 示例：下载伦敦气候模型
    success = downloader.download_model(
        "shap_london_climate", 
        "models/london_climate.joblib"
    )
    
    print(f"下载结果: {'成功' if success else '失败'}") 