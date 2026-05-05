# AMD Ryzen AI NPU 通用模型的部署之路

## 📋 執行摘要

本專案專門為AMD Ryzen AI 系列處理器提供**LLM 推論引擎**，支援 [Ryzen AI Software](https://www.amd.com/en/developer/resources/ryzen-ai-software.html) 官方釋出的的 30+ 個模型。使用原生 HuggingFace CLI 下載模型，搭配 VLM 與 LLM 兩種推論模式，快速部署各種 LLM（Qwen、Llama、Phi、Mistral、DeepSeek、Gemma、ChatGLM 等基礎模型）。

---

## 📰 Ryzen AI 最新發展

- [XDNA NPU 基本架構](https://www.amd.com/en/technologies/xdna.html) - 打造第三代 AI 引擎，提供更高效能的 NPU 設計。
- [On-Device AI: NPU vs GPU Performance](https://arxiv.org/html/2603.23640v1) - 比較 NPU 與 GPU 執行 LLM 推理的效能、能耗與熱管理。
- [於 COMPUTEX 2024 推出 50 TOPS NPU，並宣布與微軟合作](https://www.amd.com/zh-tw/newsroom/press-releases/2024-6-2-amd-extends-ai-and-high-performance-leadership-in-.html) - 將 Ryzen AI NPU 作為 Copilot+ PC 的 AI 硬體
- [發布首款能在原生 NPU 上推理 Google Gemma-3](https://www.amd.com/en/developer/resources/technical-articles/introducing-amd-support-for-new-gemma-3-models-from-google.html?utm_source=copilot.com) - 展示 NPU 與影像、語音等模態的相容性
- [ONNX Runtime 1.23.3 新增 Vitis AI Execution Provider](https://onnxruntime.ai/docs/execution-providers/Vitis-AI-ExecutionProvider.html) - Hugging Face 與 ONNX 模型的 NPU 支援
- [微軟推出 ONNX Runtime GenAI，提供多項Chat API](https://onnxruntime.ai/docs/genai/) - 整合 Hugging Face 模型到 Copilot+ PC
- [MXFP4 Quantization for Edge AI](https://arxiv.org/pdf/2509.23202) - 探討 MXFP4 低位元量化技術，提升邊緣 AI 推理效率
- [2026 年 2 月，推出 Ryzen AI 1.7 NPU LLM Collection V1](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm) - 第一套讓開發者能驗證 Ryzen AI 性能的集合。
- [2026 年 3 月，發布 Ryzen AI 1.7 NPU LLM Collection V2](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm-v2) - A涵蓋更多不同地區與語言的生成式 AI模型。

---

## 📥 安裝指南

### 1. 安裝 AMD Ryzen AI Software

在取得原裝的Ryzen AI PC後，請依照 [installation instructions](https://ryzenai.docs.amd.com/en/latest/inst.html)下載並安裝**NPU driver 32.0.203.280**+**ryzen-ai-lt 1.7.1** 或更新版本。


### 2. 設定系統環境變數

將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數（包含 AMD 自訂的 Vitis AI Execution Provider 執行庫）。

### 3. 安裝 HuggingFace CLI

```bash
conda activate ryzen-ai-1.7.1 # 該環境會由Ryzen AI Software自動安裝
```
```powershell
pip install huggingface-hub[cli]
```

---

## 📦 AMD Ryzen AI NPU 模型列表

這些模型皆採用 **AWQ 量化技術**，將原始模型的權重壓縮至 `UINT4`（4-bit unsigned integer）格式，並在推論時使用 `BFP16`（Brain Float 16）處理激活值。下表列出所有可以使用的模型：

| HuggingFace Repository | 大小 | 支援精度 | 推論模式 |
|------------------------|------|---------|---------|
| `amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu` | 2.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Llama-3.2-1B-onnx-ryzenai-npu` | 2.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2-1.5B-onnx-ryzenai-npu` | 2.5 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen-2.5_1.5B_Instruct-onnx-ryzenai-npu` | 2.5 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2.5-Coder-1.5B-Instruct-onnx-ryzenai-npu` | 2.5 GB | `UINT4`, `BFP16` | LLM |
| `amd/DeepSeek-R1-Distill-Qwen-1.5B-onnx-ryzenai-npu` | 2.5 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu` | 4.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu` | 4.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Phi-3-mini-128k-instruct-onnx-ryzenai-npu` | 4.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu` | 4.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Phi-4-mini-instruct-onnx-ryzenai-npu` | 4.5 GB | `UINT4`, `BFP16` | LLM |
| `amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu` | 6.2 GB | `UINT4`, `BFP16` | VLM |
| `amd/ChatGLM3-6B-onnx-ryzenai-npu` | 7.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2-7B-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen1.5-7B-Chat-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/CodeLlama-7b-Instruct-hf-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/DeepSeek-R1-Distill-Qwen-7B-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Llama-2-7b-hf-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Llama-2-7b-chat-hf-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Mistral-7B-Instruct-v0.1-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Mistral-7B-Instruct-v0.2-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu` | 8.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Meta-Llama-3-8B-onnx-ryzenai-npu` | 9.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Llama-3.1-8B-onnx-ryzenai-npu` | 9.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu` | 9.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/DeepSeek-R1-Distill-Llama-8B-onnx-ryzenai-npu` | 9.0 GB | `UINT4`, `BFP16` | LLM |
| `amd/gpt-oss-20b-onnx-ryzenai-npu` | 20.0 GB | `UINT4`, `BFP16` | LLM |

> `LLM` 表示該模型的輸入類型為純粹的文字。\n
> `VLM` 表示該模型的輸入類型可同時包含圖像與文字。
---

### 快速開始


#### 步驟 1: 啟動 Conda 環境**（每次使用前執行）

```powershell
conda activate ryzen-ai-1.7.1
```

#### 步驟 2: 下載模型

使用 HuggingFace CLI 下載模型列表中的模型(如：`amd/Llama-3.2-1B-onnx-ryzenai-npu`)。

```powershell
hf download amd/<模型名稱> --local-dir ./<模型名稱>
```

#### 步驟 3: 執行推論

```powershell
# LLM 推論模式
python llm.py --model ./Llama-3.2-1B-Instruct-onnx-ryzenai-npu --prompt "解釋量子計算" --max-length 512

# VLM 推論模式
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image cat.jpg --prompt "詳細描述這個場景" --max-tokens 512
```