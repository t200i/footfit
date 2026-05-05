#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查所有模型的文件完整性
"""

import sys
from pathlib import Path

def check_model_files(model_path):
    """檢查模型必要文件"""
    required_files = [
        'fusion.onnx',
        'genai_config.json',
        'tokenizer.json',
    ]
    
    # 對於大模型，通常需要 fusion.onnx.data
    data_file = model_path / 'fusion.onnx.data'
    onnx_file = model_path / 'fusion.onnx'
    
    missing = []
    for file_name in required_files:
        if not (model_path / file_name).exists():
            missing.append(file_name)
    
    # 檢查 ONNX 文件大小，如果很小(<10MB)，通常需要 .data 文件
    if onnx_file.exists():
        onnx_size = onnx_file.stat().st_size / (1024 * 1024)  # MB
        if onnx_size < 10 and not data_file.exists():
            missing.append('fusion.onnx.data (權重文件)')
    
    return missing

def main():
    base_dir = Path(__file__).parent
    
    llm_models = [
        "Llama-3.2-1B-Instruct-onnx-ryzenai-npu",
        "Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-7B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
    ]
    
    vlm_models = [
        "Gemma-3-4b-it-mm-onnx-ryzenai-npu",
    ]
    
    print("="*80)
    print("檢查模型文件完整性")
    print("="*80)
    
    all_complete = True
    
    print("\nLLM 模型:")
    for model_name in llm_models:
        model_path = base_dir / model_name
        if not model_path.exists():
            print(f"⏭️  {model_name}: 目錄不存在")
            continue
        
        missing = check_model_files(model_path)
        if missing:
            print(f"❌ {model_name}: 缺少 {', '.join(missing)}")
            all_complete = False
        else:
            print(f"✅ {model_name}: 完整")
    
    print("\nVLM 模型:")
    for model_name in vlm_models:
        model_path = base_dir / model_name
        if not model_path.exists():
            print(f"⏭️  {model_name}: 目錄不存在")
            continue
        
        # VLM 特殊文件
        vlm_files = model_path / 'gemma-3-vision-npu.onnx'
        if vlm_files.exists():
            print(f"✅ {model_name}: 完整 (VLM)")
        else:
            print(f"❌ {model_name}: 缺少 VLM 特定文件")
            all_complete = False
    
    print("\n" + "="*80)
    if all_complete:
        print("✅ 所有模型文件完整")
        return 0
    else:
        print("❌ 部分模型文件不完整，請重新下載")
        return 1

if __name__ == "__main__":
    sys.exit(main())
