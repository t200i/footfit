# AMD Ryzen AI NPU 模型部署之路

## 📋 摘要

本專案專門為 AMD Ryzen AI 系列處理器提供 **LLM 推論引擎**，基於 [Ryzen AI Software 1.7.1](https://www.amd.com/en/developer/resources/ryzen-ai-software.html) 開發，支援官方 Collections 中能完整 Offload 至 NPU 的模型。若使用其他版本的 Ryzen AI Software，部分功能與模型兼容性可能需要依照官方Release Notes調整。

---

## 📰 Ryzen AI 最新發展

- [XDNA NPU 基本架構](https://www.amd.com/en/technologies/xdna.html) - 打造第三代 AI 引擎，提供更高效能的 NPU 設計。
- [On-Device AI: NPU vs GPU Performance](https://arxiv.org/html/2603.23640v1) - 比較 NPU 與 GPU 執行 LLM 推理的效能、能耗與熱管理。
- [於 COMPUTEX 2024 推出 50 TOPS NPU，並宣布與微軟合作](https://www.amd.com/zh-tw/newsroom/press-releases/2024-6-2-amd-extends-ai-and-high-performance-leadership-in-.html) - 將 Ryzen AI NPU 作為 Copilot+ PC 的 AI 硬體
- [發布首款能在原生 NPU 上推理 Google Gemma-3](https://www.amd.com/en/developer/resources/technical-articles/introducing-amd-support-for-new-gemma-3-models-from-google.html?utm_source=copilot.com) - 展示 NPU 與影像、語音等模態的相容性
- [ONNX Runtime 1.23.3 新增 Vitis AI Execution Provider](https://onnxruntime.ai/docs/execution-providers/Vitis-AI-ExecutionProvider.html) - Hugging Face 與 ONNX 模型的 NPU 支援
- [微軟推出 ONNX Runtime GenAI，提供多項Chat API](https://onnxruntime.ai/docs/genai/) - 整合 Hugging Face 模型到 Copilot+ PC
- [MXFP4 Quantization for Edge AI](https://arxiv.org/pdf/2509.23202) - 探討 MXFP4 低位元量化技術，提升邊緣 AI 推理效率
- [2026 年 2 月，推出 Ryzen AI 1.7 NPU LLM Collection V1](https://huggingface.co/collections/ryzen-ai-17-npu-llm) - 第一套讓開發者能驗證 Ryzen AI 性能的集合。
- [2026 年 3 月，發布 Ryzen AI 1.7 NPU LLM Collection V2](https://huggingface.co/collections/ryzen-ai-17-npu-llm-v2) - A涵蓋更多不同地區與語言的生成式 AI模型。

---

## 📥 安裝指南

### 1. 安裝 AMD Ryzen AI Software 1.7.1

依照 [installation instructions](https://ryzenai.docs.amd.com/en/latest/inst.html)下載並安裝**NPU driver 32.0.203.280**+**ryzen-ai-lt 1.7.1** 。


### 2. 設定系統環境變數

將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數（以匯入 1.7.1版 新增的 Vitis AI Execution Provider 執行庫）。

---

## 📦 AMD Ryzen AI NPU 模型列表

AMD 官方在 HuggingFace 上釋出多個 NPU 模型 Collections，這些模型多數採用 **AWQ 量化技術**預先編譯，權重壓縮為 `UINT4` 格式，推論時使用 `BFP16` 處理激活值。以下為 AMD 官方提供的模型 Collections：

* [Ryzen AI 1.7.1 — NPU LFM2 Models](https://huggingface.co/collections/amd/ryzen-ai-171-npu-lfm2-models) (3+)
* [Ryzen AI 1.7.1 — NPU 16K](https://huggingface.co/collections/amd/ryzen-ai-171-npu-16k) (27+)
* [Ryzen AI 1.7.1 — NPU 4K](https://huggingface.co/collections/amd/ryzen-ai-171-npu-4k) (35+)
* [Ryzen-AI-1.7-NPU-LLM_V2](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm-v2) (4+)
* [Ryzen-AI-1.7-NPU-LLM](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm) (30+)
* [Ryzen AI 1.7 Whisper NPU Optimized ONNX models](https://huggingface.co/collections/amd/ryzen-ai-17-whisper-npu-optimized-onnx-models) (7+)
* [Ryzen-AI-1.7-NPU-creativity-models](https://huggingface.co/collections/amd/ryzen-ai-17-npu-creativity-models) (9+)

### 經實測通過的模型 (Ryzen AI 350)

| HuggingFace Repository | Size |  |
|------------------------|------|--------------|
| `Gemma-3-4b-it-mm-onnx-ryzenai-npu` | 6.2 GB | Vision LM |

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
