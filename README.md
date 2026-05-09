# AMD Ryzen AI 模型部署之路

## 📋 摘要

本專案專門為 AMD Ryzen AI 系列處理器提供 **推論加速引擎**，支援 HuggingFace 及 [AMD Collections](https://huggingface.co/amd) 開源的語言模型。若非使用本專案指定的軟體堆疊版本，部分功能與模型相容性可能會失效。

---

## 📰 Ryzen AI 最新進展

### NPU (XDNA)

- 2025年3月發布首款能在原生 NPU 上推理 Google Gemma-3，展示 NPU 與影像、語音等模態的相容性。[[1]](https://www.amd.com/en/developer/resources/technical-articles/introducing-amd-support-for-new-gemma-3-models-from-google.html?utm_source=copilot.com)
- 與微軟Copilot+PC合作，於ONNX Runtime 1.24.0 起新增 Vitis AI EP 以支援 GPU/NPU Hybrid Delegate。[[2]](https://onnxruntime.ai/docs/execution-providers/Vitis-AI-ExecutionProvider.html)
- 採用 MXFP4 低位元量化技術，於HuggingFace開源 NPU Offload 模型。
    - [Ryzen AI 1.7 NPU LLM Collection V1](https://huggingface.co/collections/ryzen-ai-17-npu-llm)
    - [Ryzen AI 1.7 NPU LLM Collection V2](https://huggingface.co/collections/ryzen-ai-17-npu-llm-v2)

### iGPU (RDNA)

- 部分Ryzen™ APUs 型號開始支援Windows及Linux使用ROCm7.2.1+PyTorch 2.9.1。[[3]](https://www.amd.com/zh-tw/newsroom/press-releases/2026-1-5-amd-expands-ai-leadership-across-client-graphics-.html)
    - [Use ROCm on Radeon and Ryzen](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/index.html) 
    - [Windows support matrices by ROCm version](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityryz/windows/windows_compatibility.html)

---

## 📥 安裝指南

#### 1. 安裝 AMD Ryzen AI Software 1.7.1
依照 [installation instructions](https://ryzenai.docs.amd.com/en/latest/inst.html)下載並安裝**NPU driver 32.0.203.280**+**ryzen-ai-lt 1.7.1**，此步驟會自動於Conda 建立 ONNX Runtime 環境 (`ryzen-ai-1.7.1`)。

#### 2. 設定系統環境變數

將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數（以匯入新版的 Vitis AI EP）。

### GPU Only (限 AI Max 300, AI 465 及 AI 365 系列以上以上型號)

#### 1. 安裝 AMD Software: Adrenalin Edition 26.2.2

依照 [Release Note](https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-26-2-2.html)下載並安裝**whql-amd-software-adrenalin-edition-26.2.2-win11-c** 。

####  2. 建立Conda虛擬環境

建立Python 3.12執行環境，並按照 [PyTorch via PIP installation](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installryz/windows/install-pytorch.html) 安裝ROCm+PyTorch及HuggingFace SDK。

```bash
conda create -n rocm-pytorch python=3.12
# pip install --no-cache-dir <rocm-dependencies>
# pip install --no-cache-dir <pytorch-dependencies>
```
```bash
# HuggingFace SDKs
pip install -r requirements.txt
```

---

## 📦 AMD Ryzen AI NPU 模型列表

AMD 官方在 HuggingFace 上釋出的多個 NPU 模型 Collections：

* [Ryzen AI 1.7.1 — NPU LFM2 Models](https://huggingface.co/collections/amd/ryzen-ai-171-npu-lfm2-models) (3+個)
* [Ryzen AI 1.7.1 — NPU 16K](https://huggingface.co/collections/amd/ryzen-ai-171-npu-16k) (27+個)
* [Ryzen AI 1.7.1 — NPU 4K](https://huggingface.co/collections/amd/ryzen-ai-171-npu-4k) (35+個)
* [Ryzen-AI-1.7-NPU-LLM_V2](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm-v2) (4+個)
* [Ryzen-AI-1.7-NPU-LLM](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm) (30+個)
* [Ryzen AI 1.7 Whisper NPU Optimized ONNX models](https://huggingface.co/collections/amd/ryzen-ai-17-whisper-npu-optimized-onnx-models) (7+個)
* [Ryzen-AI-1.7-NPU-creativity-models](https://huggingface.co/collections/amd/ryzen-ai-17-npu-creativity-models) (9+個)

### 經實測 適用於PN54 (Ryzen AI 350)的模型

| HuggingFace Repository | Size | Type | Offload |
|------------------------|------|--------------|--------------|
| `amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu` | 6.2 GB | Vision LM | NPU |

> NPU 模型多使用 **AWQ 量化技術**編譯。權重壓縮為 `UINT4` 格式，推論時使用 `BFP16` 處理激活值。

### 經實測 適用於Vivobook S 15/16 (Ryzen AI 9 HX 370)的模型

| HuggingFace Repository | Size | Type | Offload |
|------------------------|------|--------------|--------------|
| `google/gemma-4-E2B-it` | 6.2 GB | Vision LM | iGPU |
| `google/gemma-4-E4B-it` | 6.2 GB | Vision LM | iGPU |

> ROCm在 iGPU 上執行某些 LLM 工作負載（例如 Llama 1B/3B）時，可能會出現效能低於預期的情況。

### 快速開始

> 專案架構說明請參閱 [blueprint/ARCHITECTURE.md](blueprint/ARCHITECTURE.md)。

#### 步驟一：根據硬體啟動環境（擇一）

```powershell
# Vivobook S 15/16 (iGPU / ROCm)
conda activate rocm-pytorch

# PN54 (NPU) — 需先 git clone 模型到本地
conda activate ryzen-ai-1.7.1
```

設定後，以下所有指令對兩種硬體完全相同。

---

#### 文字對話

```powershell
# CLI 互動
python cli.py --model gemma3-npu

# CLI 單次（加 --stream 啟用逐 token 輸出）
python cli.py --model gemma3-npu --prompt "解釋量子計算" --stream

# 啟動 API server
python api.py --model gemma3-npu
```

```python
# Python OpenAI SDK
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")

for chunk in client.chat.completions.create(
    model="gemma3-npu",
    messages=[{"role": "user", "content": "解釋量子計算"}],
    stream=True,
):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

---

#### 圖文對話（Vision LM）

```powershell
# CLI
python cli.py --model gemma3-npu --image cat.jpg --prompt "描述這張圖片"

# API server（同文字，無需額外參數）
python api.py --model gemma3-npu
```

```python
# Python OpenAI SDK — multimodal content
import base64
image_b64 = base64.b64encode(open("cat.jpg", "rb").read()).decode()

for chunk in client.chat.completions.create(
    model="gemma3-npu",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        {"type": "text", "text": "描述這張圖片"},
    ]}],
    stream=True,
):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

> 圖片輸入僅適用於 Vision LM（表格中 Type 欄為 `Vision LM` 的模型）。

---

#### ComfyUI

```powershell
$env:RYZEN_AI_PROJECT_ROOT = "C:\path\to\amd-ryzen-ai-benchmark"
$env:MODEL_ID = "<model-id>"
cp interfaces\comfyui.py C:\path\to\ComfyUI\custom_nodes\ryzen_ai_llm.py
```

重啟 ComfyUI 後，在節點選單 **Ryzen AI / LLM** 分類下找到 **Ryzen AI LLM** 節點。支援 Vision LM 的模型會自動顯示圖片輸入端口。




