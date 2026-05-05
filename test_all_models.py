#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試所有模型的推論功能
"""

import subprocess
import sys
from pathlib import Path

def test_llm_model(model_path, prompt="Hello"):
    """測試單個 LLM 模型"""
    print(f"\n{'='*80}")
    print(f"測試 LLM: {model_path.name}")
    print(f"{'='*80}")
    
    cmd = [
        sys.executable,
        "llm.py",
        "--model", str(model_path),
        "--prompt", prompt,
        "--max-length", "50"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 分鐘超時
        )
        
        print(f"返回碼: {result.returncode}")
        if result.returncode != 0:
            print(f"STDERR:\n{result.stderr}")
            return False
        print("✅ 成功")
        return True
    except subprocess.TimeoutExpired:
        print("❌ 超時")
        return False
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


def test_vlm_model(model_path, image_path, prompt="Describe this image"):
    """測試單個 VLM 模型"""
    print(f"\n{'='*80}")
    print(f"測試 VLM: {model_path.name}")
    print(f"{'='*80}")
    
    cmd = [
        sys.executable,
        "vlm.py",
        "--model", str(model_path),
        "--image", str(image_path),
        "--prompt", prompt,
        "--max-tokens", "50"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 分鐘超時
        )
        
        print(f"返回碼: {result.returncode}")
        if result.returncode != 0:
            print(f"STDERR:\n{result.stderr}")
            return False
        print("✅ 成功")
        return True
    except subprocess.TimeoutExpired:
        print("❌ 超時")
        return False
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


def main():
    base_dir = Path(__file__).parent
    
    # LLM 模型
    llm_models = [
        "Llama-3.2-1B-Instruct-onnx-ryzenai-npu",
        "Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-7B-Instruct-onnx-ryzenai-npu",
        "Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
    ]
    
    # VLM 模型
    vlm_models = [
        "Gemma-3-4b-it-mm-onnx-ryzenai-npu",
    ]
    
    results = {}
    
    # 測試 LLM
    print("\n" + "="*80)
    print("開始測試 LLM 模型")
    print("="*80)
    
    for model_name in llm_models:
        model_path = base_dir / model_name
        if model_path.exists():
            results[model_name] = test_llm_model(model_path, "What is AI?")
        else:
            print(f"\n跳過: {model_name} (目錄不存在)")
            results[model_name] = None
    
    # 測試 VLM
    print("\n" + "="*80)
    print("開始測試 VLM 模型")
    print("="*80)
    
    image_path = base_dir / "cat.jpg"
    if not image_path.exists():
        print(f"⚠️  警告: 找不到測試圖片 {image_path}")
    
    for model_name in vlm_models:
        model_path = base_dir / model_name
        if model_path.exists() and image_path.exists():
            results[model_name] = test_vlm_model(model_path, image_path, "What is in this image?")
        else:
            print(f"\n跳過: {model_name} (目錄或圖片不存在)")
            results[model_name] = None
    
    # 統計結果
    print("\n" + "="*80)
    print("測試結果摘要")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for model_name, result in results.items():
        status = "✅ PASS" if result is True else ("❌ FAIL" if result is False else "⏭️  SKIP")
        print(f"{status} - {model_name}")
    
    print(f"\n總計: {passed} 通過, {failed} 失敗, {skipped} 跳過")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
