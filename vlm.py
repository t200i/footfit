#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMD Ryzen AI NPU - 通用視覺語言模型 (VLM) 推論介面
支援所有多模態模型（Gemma-3 等）

使用方式:
    python run_vlm.py --model <模型目錄> --image <圖像路徑> --prompt "描述這張圖片"
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def get_ryzen_ai_path():
    """取得 Ryzen AI 安裝路徑"""
    path = os.environ.get('RYZEN_AI_INSTALLATION_PATH')
    if not path:
        path = r'C:\Program Files\RyzenAI\1.7.1'
    return Path(path)


def setup_environment():
    """設置 NPU 執行環境"""
    ryzen_ai_path = get_ryzen_ai_path()
    deployment_path = ryzen_ai_path / 'deployment'
    
    if deployment_path.exists():
        current_path = os.environ.get('PATH', '')
        if str(deployment_path) not in current_path:
            os.environ['PATH'] = f"{deployment_path};{current_path}"
            print(f"✅ DLL 路徑已設置: {deployment_path}")
    else:
        print(f"⚠️  警告: 找不到 deployment 目錄: {deployment_path}")
    
    os.environ['RYZEN_AI_INSTALLATION_PATH'] = str(ryzen_ai_path)
    return ryzen_ai_path


def run_vlm_inference(model_dir, image_path, prompt, max_tokens=256, verbose=False):
    """
    執行 VLM 推論
    
    使用 '.' 作為模型路徑避免路徑重複問題
    """
    # 設置環境
    ryzen_ai_path = setup_environment()
    vlm_script = ryzen_ai_path / 'LLM' / 'example' / 'vlm' / 'vlm_run.py'
    
    if not vlm_script.exists():
        print(f"❌ 錯誤: 找不到官方 VLM 腳本: {vlm_script}")
        print(f"   請確認已安裝 AMD Ryzen AI Software 1.7.1")
        return False
    
    # 驗證模型目錄
    model_dir = Path(model_dir).resolve()
    if not model_dir.exists():
        print(f"❌ 錯誤: 模型目錄不存在: {model_dir}")
        return False
    
    # 驗證圖像
    image_path = Path(image_path).resolve()
    if not image_path.exists():
        print(f"❌ 錯誤: 圖像文件不存在: {image_path}")
        return False
    
    # 計算相對路徑（從模型目錄到圖像）
    try:
        rel_image_path = os.path.relpath(image_path, model_dir)
    except ValueError:
        # 不同磁碟機，使用絕對路徑
        rel_image_path = str(image_path)
    
    if verbose:
        print(f"\n📋 執行資訊:")
        print(f"  VLM 腳本: {vlm_script}")
        print(f"  模型目錄: {model_dir}")
        print(f"  圖像路徑: {image_path}")
        print(f"  相對路徑: {rel_image_path}")
        print(f"  提示詞: {prompt}")
        print(f"  最大 tokens: {max_tokens}\n")
    
    # 構建命令 - 使用 '.' 作為模型路徑
    cmd = [
        'python',
        str(vlm_script),
        '-m', '.',  # 關鍵: 使用當前目錄避免路徑重複
        '-i', rel_image_path,
        '-p', prompt,
        '--max_tokens', str(max_tokens)
    ]
    
    print(f"🚀 開始 VLM 推論...")
    print(f"   模型: {model_dir.name}")
    print(f"   圖像: {image_path.name}")
    
    # 切換到模型目錄執行
    original_dir = os.getcwd()
    try:
        os.chdir(model_dir)
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False
    finally:
        os.chdir(original_dir)


def main():
    parser = argparse.ArgumentParser(
        description="AMD Ryzen AI NPU - 通用 VLM 推論介面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本用法
  python run_vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image cat.jpg --prompt "這是什麼動物？"
  
  # 長回應
  python run_vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image scene.jpg --prompt "詳細描述場景" --max-tokens 512
  
  # 詳細模式
  python run_vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image test.jpg --prompt "分析圖片" --verbose

支援的模型:
  - Gemma-3-4b-it-mm (多模態)
  - 未來的其他 VLM 模型
        """
    )
    
    parser.add_argument('--model', '-m', required=True,
                        help='VLM 模型目錄路徑')
    parser.add_argument('--image', '-i', required=True,
                        help='輸入圖像路徑')
    parser.add_argument('--prompt', '-p', required=True,
                        help='文本提示詞')
    parser.add_argument('--max-tokens', '-t', type=int, default=256,
                        help='最大生成 tokens (default: 256)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='顯示詳細資訊')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🎨 AMD Ryzen AI NPU - VLM 通用推論介面")
    print("📦 ONNX Runtime GenAI 0.11.2")
    print("=" * 80)
    
    success = run_vlm_inference(
        args.model,
        args.image,
        args.prompt,
        args.max_tokens,
        args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
