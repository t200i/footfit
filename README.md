# AMD Ryzen AI NPU 通用模型的部署之路

## 📋 執行摘要

本專案提供**通用推論引擎**，支援 [Ryzen AI Software](https://www.amd.com/en/developer/resources/ryzen-ai-software.html) 官方釋出的的 30+ 個模型。使用原生 HuggingFace CLI 下載模型，搭配 VLM 與 LLM 兩種推論模式，快速部署各種 LLM（Qwen、Llama、Phi、Mistral、DeepSeek、Gemma、ChatGLM 等基礎模型）。

---

## 📰 Ryzen AI 最新發展

- [AMD XDNA NPU 基本架構](https://www.amd.com/en/technologies/xdna.html) - 打造第三代 AI 引擎，提供更高效能的 NPU 設計。
- [LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load](https://arxiv.org/html/2603.23640v1) - 比較 NPU 與 GPU 在邊緣設備上執行 LLM 推理的效能、能耗與熱管理。
- [AMD 在 COMPUTEX 2024 推出 XDNA 2 NPU (50 TOPS)，並宣布與微軟合作 Copilot+ PC](https://www.amd.com/zh-tw/newsroom/press-releases/2024-6-2-amd-extends-ai-and-high-performance-leadership-in-.html) - 確立 Ryzen AI NPU 作為 Windows PC 上的 AI 推理硬體
- [AMD 發布首款能在原生 NPU 上推理 Google Gemma-3](https://www.amd.com/en/developer/resources/technical-articles/introducing-amd-support-for-new-gemma-3-models-from-google.html?utm_source=copilot.com) - 展示 NPU 不只支援文字 LLM，也能處理影像、語音等多模態 AI
- [ONNX Runtime 1.23.3 起新增 Vitis AI Execution Provider，支援 AMD NPU 加速](https://onnxruntime.ai/docs/execution-providers/Vitis-AI-ExecutionProvider.html) - 讓 Hugging Face 與 ONNX 模型能直接在 Ryzen AI NPU 上推理
- [微軟推出 ONNX Runtime GenAI，提供 Chat、Embedding、Tokenizer 等高階 API](https://onnxruntime.ai/docs/genai/) - 整合 Hugging Face 模型到 Copilot+ PC
- [Bridging the Gap Between Promise and Performance for Microscaling FP4 Quantization](https://arxiv.org/pdf/2509.23202) - 探討 MXFP4 低位元量化技術，提升邊緣 AI 推理效率
- [2026 年 2 月，AMD 推出 Ryzen AI 1.7 NPU LLM Collection V1](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm) - 建立第一套 NPU 模型集合，讓開發者能快速驗證 Ryzen AI 的推理性能。
- [2026 年 3 月，AMD 發布 Ryzen AI 1.7 NPU LLM Collection V2](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm-v2) - A涵蓋不同地區與語言的生成式 AI，展現生態成熟度。

---

## 💡 專案背景與研究動機

### AI 推論典範轉移

過去十年，AI 推論主要在雲端資料中心執行。隨著隱私保護、即時性需求與網路成本考量，**端側 AI (On-Device AI)** 成為新趨勢。AMD Ryzen AI NPU 作為專用神經網路處理器，在能耗與效能間取得平衡，使筆記型電腦與桌機能直接執行大型語言模型。

### 技術碎片化挑戰

雖然 AMD 在 HuggingFace 上提供了 30+ 個優化模型，但每個模型都需要：
- 手動查找 Repository
- 編寫專用下載腳本
- 理解不同的 Chat Template 格式
- 調整推論參數

這導致開發者需花費大量時間在重複性工作上，降低了開發效率。

### 本專案的解決方案

本專案提供**通用推論引擎**，透過：
1. **HuggingFace CLI** - 使用官方工具下載模型
2. **統一推論模式** - VLM 模式（vlm.py）與 LLM 模式（llm.py）
3. **自動適配** - 自動處理路徑、DLL、模板等問題

實現**「兩種推論模式，適用所有模型」**的目標。

---

## 🔬 AMD Ryzen AI NPU Collections 深度解析

### 組織架構與貢獻者

AMD 在 HuggingFace 上的 [官方組織](https://huggingface.co/amd) 由 **425+ AI/ML 工程師**組成，包括：
- **AMD Ryzen AI 團隊**: 負責 NPU 硬體加速器與軟體棧開發
- **AMD Research**: 研究先進量化技術（AWQ, MXFP4）與模型優化
- **AMD ROCm 團隊**: 提供底層運算庫與驅動支援

協作夥伴：
- **Microsoft ONNX Runtime 團隊**: 共同開發 Vitis AI Execution Provider
- **HuggingFace**: 模型託管與 Optimum 整合
- **原始模型作者**: Qwen (Alibaba), Llama (Meta), Phi (Microsoft), Mistral, DeepSeek, ChatGLM (智譜) 等

### 技術願景與發展路線

AMD 的技術願景是 **"Together we advance_AI"**，致力於將 AI 從資料中心延伸到邊緣裝置，實現 AI 的民主化。

#### Collection 發展歷程

| 時期 | 里程碑 | 模型數量 | 代表性模型 |
|------|--------|---------|-----------|
| **2024 Q4** | Ryzen AI 1.7.1 平台發布 | 10+ | Qwen2-1.5B, Llama-2-7b, Phi-3-mini |
| **2025 Q1-Q2** | Collection V1 正式發布 | 20+ | Llama-3.1-8B, Mistral-7B-v0.3, Qwen2.5 系列 |
| **2025 Q3-Q4** | 深度優化與擴展 | 25+ | 16K/4K 版本, MXFP4 量化版本 |
| **2026 Q1** | Collection V2 發布 | 30+ | DeepSeek-R1-Distill, Phi-4, ChatGLM3, Gemma-3 (多模態) |

#### 技術棧與生態系統

- **模型格式**: ONNX (Open Neural Network Exchange)
- **推論框架**: ONNX Runtime GenAI
- **量化技術**: AWQ, MXFP4, BFP16
- **硬體抽象**: AMD ROCm + Vitis AI
- **開發工具**: HuggingFace Optimum, AMD Model Converter

#### 模型覆蓋範圍

**按大小分類**:
- 1-2B: 6 個模型（快速原型開發）
- 3-4B: 6 個模型（平衡性能與速度）
- 7-8B: 15 個模型（高品質輸出）
- 20B+: 1 個模型（企業級應用）

**按類型分類**:
- 文本生成: 25 個
- 程式碼生成: 3 個
- 多模態 (圖像+文本): 1 個

**按語言支援**:
- 英文為主: Llama, Mistral, Phi, CodeLlama
- 中文優化: Qwen, ChatGLM
- 多語言: Qwen2.5 (支援 29+ 語言)

---

## 🚀 系統需求

| 類別 | 最低需求 | 建議配置 |
|------|---------|---------|
| **處理器** | AMD Ryzen AI 系列（含 NPU） | Ryzen AI 9 HX 370/365 |
| **記憶體** | 8GB RAM | 16GB+ RAM |
| **作業系統** | Windows 11 (22H2+) | Windows 11 最新版 |
| **Python** | 3.8 - 3.12 | Python 3.12 |
| **軟體** | Ryzen AI Software 1.7.1+ | Ryzen AI Software 最新版 |
| **硬碟空間** | 至少 30GB | 50GB+ (用於多個模型) |

**效能參考**:
- 小型模型 (1.5B-3B): 6-8 tokens/s
- 中型模型 (7B-8B): 5-6 tokens/s
- 大型模型 (20B+): 3-4 tokens/s

---

## 📥 安裝指南

### 1. 安裝 AMD Ryzen AI Software
下載並安裝 [AMD Ryzen AI Software](https://www.amd.com/ryzen-ai) 1.7.1 或更新版本。

### 2. 啟動AMD Ryzen AI原生 Python 環境
```bash
# 須通過AMD Ryzen AI Software自動安裝
conda activate ryzen-ai-1.7.1
```

### 3. 安裝 HuggingFace CLI
```powershell
# 安裝 HuggingFace Hub（包含 hf 命令）
pip install huggingface-hub[cli]

# 驗證安裝
hf --help
```

詳細安裝說明請參考 [安裝指南](docs/INSTALLATION.md)。

---

## 📦 AMD Ryzen AI NPU 模型列表

完整列表：[Collection V1](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm) | [Collection V2](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm-v2)

| HuggingFace Repository | 大小 | Collection | 推論模式 | 用途 |
|------------------------|------|-----------|---------|------|
| `amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu` | 2.0 GB | V2 | 通用 | 輕量/入門 ⭐ |
| `amd/Llama-3.2-1B-onnx-ryzenai-npu` | 2.0 GB | V2 | 通用 | 輕量 |
| `amd/Qwen2-1.5B-onnx-ryzenai-npu` | 2.5 GB | V1 | 通用 | 輕量 ⭐ |
| `amd/Qwen-2.5_1.5B_Instruct-onnx-ryzenai-npu` | 2.5 GB | V2 | 通用 | 輕量 |
| `amd/Qwen2.5-Coder-1.5B-Instruct-onnx-ryzenai-npu` | 2.5 GB | V2 | 通用 | 程式碼 |
| `amd/DeepSeek-R1-Distill-Qwen-1.5B-onnx-ryzenai-npu` | 2.5 GB | V2 | 通用 | 推理 |
| `amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu` | 4.0 GB | V1 | 通用 | 平衡 ⭐ |
| `amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu` | 4.0 GB | V1 | 通用 | 平衡 |
| `amd/Phi-3-mini-128k-instruct-onnx-ryzenai-npu` | 4.0 GB | V1 | 通用 | 長文本 |
| `amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu` | 4.0 GB | V1 | 通用 | 平衡 |
| `amd/Phi-4-mini-instruct-onnx-ryzenai-npu` | 4.5 GB | V2 | 通用 | 平衡 ⭐ |
| `amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu` | 6.2 GB | V2 | 多模態 | 圖像+文本 🎨 |
| `amd/ChatGLM3-6B-onnx-ryzenai-npu` | 7.0 GB | V2 | 通用 | 中文 🇨🇳 |
| `amd/Qwen2-7B-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 |
| `amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 ⭐ |
| `amd/Qwen1.5-7B-Chat-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 |
| `amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 程式碼 ⭐ |
| `amd/CodeLlama-7b-Instruct-hf-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 程式碼 |
| `amd/DeepSeek-R1-Distill-Qwen-7B-onnx-ryzenai-npu` | 8.0 GB | V2 | 通用 | 推理 |
| `amd/Llama-2-7b-hf-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 通用 |
| `amd/Llama-2-7b-chat-hf-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 對話 |
| `amd/Mistral-7B-Instruct-v0.1-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 |
| `amd/Mistral-7B-Instruct-v0.2-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 |
| `amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu` | 8.0 GB | V1 | 通用 | 高品質 ⭐ |
| `amd/Meta-Llama-3-8B-onnx-ryzenai-npu` | 9.0 GB | V1 | 通用 | 高品質 |
| `amd/Llama-3.1-8B-onnx-ryzenai-npu` | 9.0 GB | V1 | 通用 | 高品質 |
| `amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu` | 9.0 GB | V1 | 通用 | 高品質 ⭐ |
| `amd/DeepSeek-R1-Distill-Llama-8B-onnx-ryzenai-npu` | 9.0 GB | V2 | 通用 | 推理 |
| `amd/gpt-oss-20b-onnx-ryzenai-npu` | 20.0 GB | V2 | 通用 | 超大型 💪 |

**圖示**: ⭐ 推薦 | 🎨 多模態 | 🇨🇳 中文優化 | 💪 超大型

---

## 🎯 標準化使用流程

### 關於模型與推論模式

上方模型列表中的 HuggingFace Repository 路徑（如 `amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu`）是用來從 HuggingFace 下載模型到本機的識別碼。下載後的模型目錄將包含完整的 ONNX 格式模型文件、配置文件與 tokenizer。

本專案提供兩種推論模式：
- **VLM 模式**（多模態）：處理圖像與文本的結合輸入，如圖像描述、視覺問答等任務
- **LLM 模式**（純文本）：僅處理文本輸入輸出，如對話、翻譯、程式碼生成等任務

---

### 前置準備：環境設置

**步驟 1: 設定系統環境變數**

NPU 推論需要特定的 DLL 文件（`onnx_custom_ops.dll`、`onnxruntime.dll` 等），需將 `C:\Program Files\RyzenAI\1.7.1\deployment` 加入系統 PATH 環境變數。

設定方式：
1. 開啟「系統設定」→「進階系統設定」→「環境變數」
2. 在「系統變數」區塊中找到 `Path`，點選「編輯」
3. 點選「新增」，輸入 `C:\Program Files\RyzenAI\1.7.1\deployment`
4. 點選「確定」儲存

**步驟 2: 啟動 Conda 環境**（每次使用前執行）

```powershell
conda activate ryzen-ai-1.7.1
```

---

### 快速開始

#### 步驟 1: 下載模型

從模型列表選擇模型，使用 HuggingFace CLI 下載：

```powershell
hf download amd/<模型名稱> --local-dir ./<模型名稱>
```

---

#### 步驟 2: 執行推論

本專案提供兩種推論模式：

##### A. **VLM 推論模式** （圖像 + 文本）

使用 `vlm.py` - 支援所有視覺語言模型：

```powershell
# 基本用法
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image cat.jpg --prompt "這是什麼動物？"

# 長回應
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image scene.jpg --prompt "詳細描述這個場景" --max-tokens 512
```

**技術說明**: 腳本會自動處理 VLM 的路徑重複問題（使用 `.` 作為模型路徑）。

##### B. **LLM 推論模式** （僅文本）

使用 `llm.py` - 支援所有文本語言模型：

```powershell
# 單次推論
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "什麼是 AI？"

# 長回應
python llm.py --model ./Llama-3.2-1B-Instruct-onnx-ryzenai-npu --prompt "解釋量子計算" --max-length 512

# 互動對話模式
python llm.py --model ./Phi-4-mini-instruct-onnx-ryzenai-npu --interactive
```

**注意**: 部分模型可能有固件兼容性問題（如 Llama-3.2 的 "flat version" 錯誤）。如遇到問題，請嘗試其他模型。

---

### 常見問題與解決方案

#### 問題 1: "找不到指定的模組" 或 DLL 錯誤

**原因**: NPU DLL 文件不在系統 PATH 中

**解決方案**:
```powershell
$env:Path = "C:\Program Files\RyzenAI\1.7.1\deployment;$env:Path"
```

#### 問題 2: "flat version is not supported for matmulbias"

**原因**: NPU 固件版本與模型編譯版本不兼容（常見於 Llama-3.2）

**解決方案**: 
- 嘗試其他模型（如 Qwen2.5, Phi-4）
- 關注 AMD 官方模型更新

#### 問題 3: VLM 路徑重複錯誤

**症狀**: `Cannot read header from model-name\model-name\file.pb.bin`

**解決方案**: `vlm.py` 已自動處理此問題（使用 `.` 作為模型路徑）

---

### 進階選項

#### 詳細模式（查看執行細節）

```powershell
# VLM 模式
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image test.jpg --prompt "分析" --verbose

# LLM 模式
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "你好" --verbose
```

#### 調整輸出長度

```powershell
# VLM 模式: 使用 --max-tokens
python vlm.py --model <模型> --image <圖像> --prompt "詳細描述" --max-tokens 512

# LLM 模式: 使用 --max-length
python llm.py --model <模型> --prompt "長文回應" --max-length 1024
```

### 批次下載腳本

創建 `download_recommended.ps1`：

```powershell
# 推薦模型列表
$models = @(
    "amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu",
    "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
    "amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
    "amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu"
)

foreach ($repo in $models) {
    $dirName = $repo -replace '^.*/',''
    hf download $repo --local-dir "./$dirName"
}
```

執行：`powershell -ExecutionPolicy Bypass -File download_recommended.ps1`

---

## 🤖 Chat Template 自動偵測

推論引擎會從模型目錄名稱自動偵測 Chat Template：

| Template | 適用模型 | 偵測關鍵字 |
|----------|---------|----------|
| `qwen` | Qwen、DeepSeek-R1-Distill-Qwen | `qwen` |
| `llama2` | Llama-2、CodeLlama | `llama-2` |
| `llama3` | Llama-3.x、DeepSeek-R1-Distill-Llama | `llama-3` |
| `mistral` | Mistral | `mistral` |
| `phi3` | Phi-3.x、Phi-4 | `phi` |
| `gemma3` | Gemma-3 | `gemma` |
| `chatglm3` | ChatGLM3 | `chatglm` |
| `gpt` | GPT-OSS | `gpt` |

---

## 📂 專案目錄結構

```
FY115-BCI-Agent/
├── vlm.py                          # 🎨 VLM 推論模式（多模態：圖像+文本）
├── llm.py                          # 💬 LLM 推論模式（純文本）
├── setup_env.ps1                   # 🔧 環境檢查腳本
├── gemma3.ps1                      # 📜 Gemma-3 便利腳本（可選）
├── QUICKSTART_V2.md                # 🚀 快速開始指南（推薦）
├── STANDARDIZATION.md              # 📰 標準化指南
├── SUMMARY.md                      # 📊 技術總結與測試結果
├── README.md                       # 📖 本文件（主要文檔）
├── docs/
│   ├── INSTALLATION.md             # 詳細安裝指南
│   ├── USAGE.md                    # 使用教學
│   ├── PROGRAMMING.md              # API 參考
│   ├── TROUBLESHOOTING.md          # 故障排除
│   └── ARCHITECTURE.md             # 系統架構
└── <模型目錄>/                     # 下載的模型（自行創建）
    ├── Gemma-3-4b-it-mm-onnx-ryzenai-npu/
    ├── Qwen2.5-3B-Instruct-onnx-ryzenai-npu/
    └── ...
```

**核心檔案說明**:
- **`vlm.py`**: VLM 推論模式 - 所有視覺語言模型的統一介面
- **`llm.py`**: LLM 推論模式 - 所有純文本模型的統一介面
- **`setup_env.ps1`**: 環境診斷工具
- **`.ps1` 腳本**: PowerShell 便利腳本（可選）

---

## � 文檔與資源

**本專案文檔**：
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 常用命令速查表
- [docs/INSTALLATION.md](docs/INSTALLATION.md) - 安裝指南
- [docs/USAGE.md](docs/USAGE.md) - 使用教學
- [docs/PROGRAMMING.md](docs/PROGRAMMING.md) - API 參考
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 架構說明

**AMD 官方資源**：
- [AMD Ryzen AI 官網](https://www.amd.com/ryzen-ai)
- [Ryzen AI 開發者文檔](https://ryzenai.docs.amd.com/)
- [HuggingFace AMD Organization](https://huggingface.co/amd)

**技術框架**：
- [ONNX Runtime GenAI](https://github.com/microsoft/onnxruntime-genai)
- [HuggingFace Hub](https://huggingface.co/)

---

**版本**: 1.0.0 | **最後更新**: 2026/05/04 | **授權**: MIT

> 💡 第一次使用建議從小型模型（Llama-3.2-1B-Instruct 或 Qwen2-1.5B）開始。
