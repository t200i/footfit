# AMD Ryzen AI 模型部署之路

## 📋 摘要

本專案專門為 AMD Ryzen AI 系列處理器提供 **推論加速引擎**，支援HuggingFace 上開源及AMD 官方 Collections 中的 語言模型。若非使用指定的軟體版本，部分功能與模型相容性可能會失效。

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
依照 [installation instructions](https://ryzenai.docs.amd.com/en/latest/inst.html)下載並安裝**NPU driver 32.0.203.280**+**ryzen-ai-lt 1.7.1**，此步驟會自動建立Conda for ONNX Runtime環境 (`ryzen-ai-1.7.1`)。

#### 2. 設定系統環境變數

將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數（以匯入 1.7.1版 新增的 Vitis AI Execution Provider）。

### GPU Only (限 AI Max 300, AI 465 及 AI 365 系列以上以上型號)

#### 1. 安裝 AMD Software: Adrenalin Edition 26.2.2

依照 [Release Note](https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-26-2-2.html)下載並安裝**whql-amd-software-adrenalin-edition-26.2.2-win11-c** 。

####  2. 建立Conda虛擬環境

建立Python 3.12執行環境，並按照 [PyTorch via PIP installation](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installryz/windows/install-pytorch.html) 安裝ROCm+PyTorch及HuggingFace SDK。

```
conda create -name rocm-pytorch python=3.12
# pip install --no-cache-dir <rocm-dependencies>
# pip install --no-cache-dir <pytorch-dependencies>
```
```
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

> NPU Offload的模型多數採用 **AWQ 量化技術**預先編譯，權重壓縮為 `UINT4` 格式，推論時使用 `BFP16` 處理激活值。

### 經實測 適用於Vivobook S 15/16 (Ryzen AI 9 HX 370)的模型

| HuggingFace Repository | Size | Type | Offload |
|------------------------|------|--------------|--------------|
| `google/gemma-4-E4B-it` | 6.2 GB | Vision LM | iGPU |



> 在 AMD Ryzen™ AI處理器上執行某些 LLM 工作負載（例如 Llama 31B/3B）時，可能會出現效能低於預期的情況。

### 快速開始

#### 啟動環境（每次使用前執行）

```powershell
conda activate ryzen-ai-1.7.1      # 該環境是由Ryzen AI Software自動安裝
```

#### 下載模型

使用 Git 下載模型列表中的模型(如：`Gemma-3-4b-it-mm-onnx-ryzenai-npu`)。

```powershell
git clone https://huggingface.co/amd/<模型名稱>
```

#### 執行推論

```powershell
# for Language LM 推論
python llm.py --model ./<模型名稱> --prompt "解釋量子計算" --max-length 512

# for Vision LM 推論
python vlm.py --model ./<模型名稱> --image cat.jpg --prompt "詳細描述這個場景" --max-tokens 512
```
