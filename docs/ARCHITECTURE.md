# 系統架構文件

本文件說明 AMD Ryzen AI NPU 通用模型部署系統的架構設計。

---

## 🏗️ 整體架構

```
┌─────────────────────────────────────────────────────────────┐
│                     使用者介面層                              │
│  CLI (run_npu_inference.py, download_model.py)              │
│  APIs (Flask/FastAPI 整合)                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     抽象與配置層                              │
│  • models.yaml (30+ 模型配置)                                │
│  • Chat Template 管理                                        │
│  • 模型元數據管理                                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     推論引擎層                                │
│  • ONNX Runtime GenAI                                        │
│  • Model, Tokenizer, Generator                              │
│  • 參數管理 (GeneratorParams)                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     執行提供者層                              │
│  • Vitis AI Execution Provider                              │
│  • Ryzen AI Provider                                         │
│  • NPU 驅動介面                                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     硬體層                                    │
│  AMD Ryzen AI NPU (XDNA Architecture)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 核心組件

### 1. configs/models.yaml

**功能**: 集中式模型配置管理

**內容**:
- 30+ 模型定義（ID、名稱、Repository、大小、類型）
- 7 種 Chat Template 定義
- 推薦模型分類（初學者、一般、程式碼、進階）

**優勢**:
- ✅ 單一真實來源 (Single Source of Truth)
- ✅ 新增模型只需修改 YAML
- ✅ 易於維護與版本控制

### 2. scripts/download_model.py

**功能**: 通用模型下載工具

**核心功能**:
- 從 models.yaml 讀取配置
- 使用 `huggingface_hub` 下載模型
- 生成 `model_info.json` 記錄模型元數據
- 提供列表、推薦、下載等功能

**工作流程**:
```
使用者指令 → 載入 models.yaml → 查找模型 → 下載到本地 → 生成 model_info.json
```

### 3. run_npu_inference.py

**功能**: 通用推論引擎

**核心功能**:
- 載入任意 ONNX 模型
- 自動偵測 Chat Template
- 支援單次推論與互動模式
- 串流生成輸出

**推論流程**:
```
載入模型 → 偵測 Chat Template → 格式化 Prompt → 編碼 → 生成 → 解碼 → 輸出
```

---

## 🔄 資料流程

### 模型下載流程

```
python scripts/download_model.py --download qwen2-1.5b
    ↓
載入 configs/models.yaml
    ↓
找到 model_id='qwen2-1.5b' 的配置
    ↓
取得 repo='amd/Qwen2-1.5B-onnx-ryzenai-npu'
    ↓
呼叫 huggingface_hub.snapshot_download()
    ↓
下載到 Qwen2-1.5B-onnx-ryzenai-npu/
    ↓
創建 model_info.json
```

### 推論執行流程

```
python run_npu_inference.py --model <dir> --prompt "Hello"
    ↓
載入模型 (og.Model)
    ↓
創建 Tokenizer (og.Tokenizer)
    ↓
讀取 model_info.json (如果存在)
    ↓
偵測/設定 Chat Template
    ↓
格式化 Prompt (應用 template)
    ↓
編碼為 tokens (tokenizer.encode)
    ↓
設定生成參數 (GeneratorParams)
    ↓
創建生成器 (og.Generator)
    ↓
逐 token 生成 (compute_logits, generate_next_token)
    ↓
解碼輸出 (tokenizer.decode)
    ↓
顯示結果
```

---

## 🧩 Chat Template 系統

### 為什麼需要 Chat Template？

不同的模型訓練時使用不同的對話格式。例如：

**Qwen 格式**:
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
```

**Llama 3 格式**:
```
<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Hello<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

如果使用錯誤的格式，模型可能：
- 無法正確理解輸入
- 生成品質下降
- 輸出格式混亂

### Template 自動偵測

`run_npu_inference.py` 的自動偵測邏輯：

1. **優先從 model_info.json 讀取**
   ```python
   if Path(model_dir / "model_info.json").exists():
       template = info['chat_template']
   ```

2. **從目錄名稱推斷**
   ```python
   if 'qwen' in model_name.lower():
       return 'qwen'
   elif 'llama-3' in model_name.lower():
       return 'llama3'
   ...
   ```

3. **使用通用格式**
   ```python
   return 'auto'  # 不添加特殊標記
   ```

---

## 🔌 擴展性設計

### 新增模型

只需在 `configs/models.yaml` 中添加：

```yaml
- id: new-model
  name: New Model Name
  repo: amd/new-model-onnx-ryzenai-npu
  size: ~5.0 GB
  type: text-generation
  description: Description
  chat_template: qwen  # 使用現有 template
```

### 新增 Chat Template

在 `run_npu_inference.py` 的 `CHAT_TEMPLATES` 字典中添加：

```python
CHAT_TEMPLATES = {
    # 現有 templates...
    'new_template': """<special_format>
    {prompt}
    <end_format>"""
}
```

### 整合到 Web 應用

參考 [程式開發指南](PROGRAMMING.md) 中的 Flask/FastAPI 範例。

---

## 🎯 設計原則

### 1. 配置與程式碼分離
- 所有模型配置在 `models.yaml`
- 程式碼不包含硬編碼的模型資訊

### 2. 通用性優先
- 一個推論引擎支援所有模型
- 避免為每個模型寫專用代碼

### 3. 自動化
- 自動偵測 Chat Template
- 自動生成 model_info.json

### 4. 擴展性
- 易於新增模型
- 易於新增功能

### 5. 使用者友好
- 簡單的 CLI 介面
- 詳細的錯誤訊息
- 完整的文檔

---

## 🔧 技術選型

| 組件 | 技術 | 理由 |
|------|------|------|
| 配置管理 | YAML | 人類可讀，易於編輯 |
| 模型格式 | ONNX | 跨平台，標準化 |
| 推論引擎 | ONNX Runtime GenAI | 官方支援，效能優秀 |
| 模型託管 | HuggingFace | 業界標準，生態完善 |
| 下載工具 | huggingface_hub | 官方 SDK，穩定可靠 |
| CLI | argparse | Python 標準庫，功能完整 |

---

## 📚 參考

- [ONNX Runtime Architecture](https://onnxruntime.ai/docs/reference/high-level-design.html)
- [Execution Providers](https://onnxruntime.ai/docs/execution-providers/)
- [ONNX Format](https://onnx.ai/)
