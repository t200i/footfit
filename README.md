# AMD Ryzen AI 模型部署之路

## 📋 摘要

本專案專門為 AMD Ryzen AI 系列處理器提供 **LLM 推論加速引擎**，基於 [AMD Software: Adrenalin Edition 26.2.2](https://www.amd.com/en/developer/resources/ryzen-ai-software.html) 及 [Ryzen AI Software 1.7.1](https://www.amd.com/en/developer/resources/ryzen-ai-software.html) 開發，支援HuggingFace 上開源及AMD 官方 Collections 中的模型。若使用其他版本，部分功能與模型相容性可能需要依照官方Release Notes調整。

---

## 📰 Ryzen AI 最新進展

- [於 COMPUTEX 2024 推出 50 TOPS NPU，宣布與微軟Copilot+PC合作](https://www.amd.com/zh-tw/newsroom/press-releases/2024-6-2-amd-extends-ai-and-high-performance-leadership-in-.html)

### RDNA (GPU)

- [2026年3月釋出ROCm 7.2.1 版，支援Windows 11安裝PyTorch + ROCm (限定Ryzen AI 365以上型號)](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/index.html)

### XDNA (NPU)

- [2025年3月發布首款能在原生 NPU 上推理 Google Gemma-3](https://www.amd.com/en/developer/resources/technical-articles/introducing-amd-support-for-new-gemma-3-models-from-google.html?utm_source=copilot.com) - 展示 NPU 與影像、語音等模態的相容性
- [微軟ONNX Runtime 自 1.23.3 新增 Vitis AI EP 以支援 NPU Delegate](https://onnxruntime.ai/docs/execution-providers/Vitis-AI-ExecutionProvider.html)
- [透過 MXFP4 低位元量化技術提供HuggingFace](https://arxiv.org/pdf/2509.23202) - Ryzen AI 1.7 NPU LLM Collection [V1](https://huggingface.co/collections/ryzen-ai-17-npu-llm) 與 [V2](https://huggingface.co/collections/ryzen-ai-17-npu-llm-v2) - A涵蓋更多不同地區與語言的生成式 AI模型。

---

## 📥 安裝指南

### 1. 安裝 AMD Software: Adrenalin Edition 26.2.2
依照 [installation instructions](https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-26-2-2.html)下載並安裝**whql-amd-software-adrenalin-edition-26.2.2-win11-c.exe** 。

### 2. 建立Conda虛擬環境

建立Python 3.12虛擬環境，並依照 [https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installryz/windows/install-pytorch.html](https://www.amd.com/en/resources/support-articles/release-notes/RN-RAD-WIN-26-2-2.html) 安裝ROCm+PyTorch

```
conda create -name rocm-pytorch python=3.12
```
```
# install ROCm for Python
pip install --no-cache-dir `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_core-7.2.1-py3-none-win_amd64.whl `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_devel-7.2.1-py3-none-win_amd64.whl `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_libraries_custom-7.2.1-py3-none-win_amd64.whl `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm-7.2.1.tar.gz
```
```
# install PyTorch with ROCm
pip install --no-cache-dir `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torch-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torchaudio-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl `
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torchvision-0.24.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl
```



### 1. 安裝 AMD Ryzen AI Software 1.7.1
依照 [installation instructions](https://ryzenai.docs.amd.com/en/latest/inst.html)下載並安裝**NPU driver 32.0.203.280**+**ryzen-ai-lt 1.7.1** 。

### 2. 設定系統環境變數

將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數（以匯入 1.7.1版 新增的 Vitis AI Execution Provider 執行庫）。

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

| HuggingFace Repository | Size |  |
|------------------------|------|--------------|
| `Gemma-3-4b-it-mm-onnx-ryzenai-npu` | 6.2 GB | Vision LM |

> 這些模型多數採用 **AWQ 量化技術**預先編譯，權重壓縮為 `UINT4` 格式，推論時使用 `BFP16` 處理激活值。

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
