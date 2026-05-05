#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動應用模型補丁腳本

此腳本會自動檢測當前目錄中的模型，並為缺失必要文件的模型應用對應補丁。
"""

import os
import shutil
from pathlib import Path

# 補丁映射：模型名稱模式 -> 補丁目錄
PATCH_MAPPINGS = {
    'SmolLM2-135M-Instruct': 'SmolLM2-135M-Instruct',
    'SmolLM-135M-Instruct': 'SmolLM2-135M-Instruct',  # 同樣的補丁
}

def find_models(base_dir='.'):
    """
    在當前目錄中尋找已下載的模型
    """
    models = []
    base_path = Path(base_dir)
    
    for item in base_path.iterdir():
        if item.is_dir() and 'onnx-ryzenai-npu' in item.name.lower():
            models.append(item)
        elif item.is_dir() and any(pattern in item.name for pattern in PATCH_MAPPINGS.keys()):
            models.append(item)
    
    return models

def apply_patch(model_dir, patch_name):
    """
    將補丁應用到指定模型目錄
    """
    patch_dir = Path('patches') / patch_name
    
    if not patch_dir.exists():
        print(f"  ⚠️  補丁目錄不存在: {patch_dir}")
        return False
    
    applied = False
    for patch_file in patch_dir.iterdir():
        if patch_file.is_file():
            target_file = model_dir / patch_file.name
            
            # 如果目標文件已存在，跳過
            if target_file.exists():
                print(f"  ⏭️  已存在，跳過: {patch_file.name}")
                continue
            
            # 複製補丁文件
            shutil.copy2(patch_file, target_file)
            print(f"  ✅ 已應用: {patch_file.name}")
            applied = True
    
    return applied

def main():
    """
    主函數
    """
    print("=" * 70)
    print("AMD Ryzen AI NPU - 模型補丁自動應用工具")
    print("=" * 70)
    print()
    
    # 確認 patches 目錄存在
    patches_dir = Path('patches')
    if not patches_dir.exists():
        print("❌ 錯誤: 找不到 patches 目錄")
        print("   請確認在專案根目錄執行此腳本")
        return
    
    # 尋找模型
    print("🔍 正在掃描模型目錄...")
    models = find_models()
    
    if not models:
        print("   未找到任何模型目錄")
        return
    
    print(f"   找到 {len(models)} 個模型\n")
    
    # 為每個模型檢查並應用補丁
    total_applied = 0
    for model_dir in models:
        model_name = model_dir.name
        print(f"📦 檢查: {model_name}")
        
        # 檢查是否需要補丁
        patch_name = None
        for pattern, patch_dir_name in PATCH_MAPPINGS.items():
            if pattern in model_name:
                patch_name = patch_dir_name
                break
        
        if not patch_name:
            print(f"  ℹ️  此模型不需要補丁")
            print()
            continue
        
        # 應用補丁
        if apply_patch(model_dir, patch_name):
            total_applied += 1
        
        print()
    
    # 總結
    print("=" * 70)
    if total_applied > 0:
        print(f"✅ 完成! 已為 {total_applied} 個模型應用補丁")
    else:
        print("✅ 所有模型都已完整，無需應用補丁")
    print("=" * 70)

if __name__ == '__main__':
    main()
