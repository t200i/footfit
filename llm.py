#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMD Ryzen AI NPU - 通用文本語言模型 (LLM) 推論介面
支援所有純文本模型（Llama, Qwen, Phi, Mistral 等）

使用方式:
    python run_llm.py --model <模型目錄> --prompt "你的問題"
    python run_llm.py --model <模型目錄> --interactive  # 互動模式
"""

import argparse
import os
import sys
import subprocess
import tempfile
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


def run_llm_inference(model_dir, prompt=None, max_length=256, interactive=False, verbose=False):
    """
    執行 LLM 推論
    """
    # 設置環境
    ryzen_ai_path = setup_environment()
    
    # 優先使用 model_chat.py（支援 chat template）
    llm_script = ryzen_ai_path / 'LLM' / 'example' / 'model_chat.py'
    if not llm_script.exists():
        # 降級到 run_model.py
        llm_script = ryzen_ai_path / 'LLM' / 'example' / 'run_model.py'
    
    if not llm_script.exists():
        print(f"❌ 錯誤: 找不到官方 LLM 腳本")
        print(f"   請確認已安裝 AMD Ryzen AI Software 1.7.1")
        return False
    
    # 驗證模型目錄
    model_dir = Path(model_dir).resolve()
    if not model_dir.exists():
        print(f"❌ 錯誤: 模型目錄不存在: {model_dir}")
        return False
    
    if verbose:
        print(f"\n📋 執行資訊:")
        print(f"  LLM 腳本: {llm_script}")
        print(f"  模型目錄: {model_dir}")
        if prompt:
            print(f"  提示詞: {prompt}")
        print(f"  最大長度: {max_length}")
        print(f"  互動模式: {interactive}\n")
    
    # 構建命令
    cmd = [
        'python',
        str(llm_script),
        '-m', str(model_dir)
    ]
    
    # 根據腳本類型添加參數
    if 'model_chat.py' in str(llm_script):
        # model_chat.py 的參數
        if interactive:
            # 互動模式不需要 -pr 參數
            pass
        elif prompt:
            # 創建臨時 prompt 文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            cmd.extend(['-pr', prompt_file])
        
        if max_length:
            cmd.extend(['-mpt', str(max_length)])
    else:
        # run_model.py 的參數
        if max_length:
            cmd.extend(['-l', str(max_length)])
    
    print(f"🚀 開始 LLM 推論...")
    print(f"   模型: {model_dir.name}")
    if interactive:
        print(f"   模式: 互動對話")
    elif prompt:
        print(f"   提示: {prompt}")
    
    # 執行
    try:
        if interactive or not prompt:
            # 互動模式 - 直接執行
            result = subprocess.run(cmd, check=False)
        else:
            # 單次推論
            result = subprocess.run(cmd, check=False)
            # 清理臨時文件
            if 'prompt_file' in locals():
                try:
                    os.unlink(prompt_file)
                except:
                    pass
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="AMD Ryzen AI NPU - 通用 LLM 推論介面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 單次推論
  python run_llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "什麼是 AI？"
  
  # 長回應
  python run_llm.py --model ./Llama-3.2-1B-Instruct-onnx-ryzenai-npu --prompt "解釋量子計算" --max-length 512
  
  # 互動模式
  python run_llm.py --model ./Phi-4-mini-instruct-onnx-ryzenai-npu --interactive
  
  # 詳細模式
  python run_llm.py --model ./Qwen2.5-7B-Instruct-onnx-ryzenai-npu --prompt "你好" --verbose

支援的模型:
  - Llama-3.2-1B-Instruct, Llama-3.1-8B-Instruct
  - Qwen2-1.5B, Qwen2.5-3B-Instruct, Qwen2.5-7B-Instruct
  - Phi-3-mini, Phi-3.5-mini, Phi-4-mini
  - Mistral-7B-Instruct-v0.3
  - DeepSeek-R1-Distill 系列
  - ChatGLM3-6B
  - CodeLlama-7b-Instruct

注意:
  - 部分模型可能有固件兼容性問題（如 Llama-3.2 的 "flat version" 錯誤）
  - 如遇到問題，請嘗試其他模型或參考 TROUBLESHOOTING.md
        """
    )
    
    parser.add_argument('--model', '-m', required=True,
                        help='LLM 模型目錄路徑')
    parser.add_argument('--prompt', '-p',
                        help='文本提示詞（單次推論模式）')
    parser.add_argument('--max-length', '-l', type=int, default=256,
                        help='最大生成長度 (default: 256)')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='啟動互動對話模式')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='顯示詳細資訊')
    
    args = parser.parse_args()
    
    # 驗證參數
    if not args.interactive and not args.prompt:
        parser.error("請提供 --prompt 或使用 --interactive 模式")
    
    print("=" * 80)
    print("💬 AMD Ryzen AI NPU - LLM 通用推論介面")
    print("📦 ONNX Runtime GenAI 0.11.2")
    print("=" * 80)
    
    success = run_llm_inference(
        args.model,
        args.prompt,
        args.max_length,
        args.interactive,
        args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
