# AMD Ryzen AI NPU 使用指南

本指南提供詳細的使用說明，幫助您充分利用 AMD Ryzen AI NPU 進行 AI 推論。

---

## 📚 目錄

1. [基礎使用](#基礎使用)
2. [模型管理](#模型管理)
3. [推論執行](#推論執行)
4. [進階功能](#進階功能)
5. [最佳實踐](#最佳實踐)

---

## 🚀 基礎使用

### 查看可用模型

列出所有支援的模型：

```bash
python scripts/download_model.py --list
```

輸出示例：
```
================================================================================
AMD Ryzen AI NPU 支援的模型
================================================================================

小型模型 (1-2B):
--------------------------------------------------------------------------------
  [qwen2-1.5b]
    名稱: Qwen2-1.5B
    大小: ~2.5 GB
    類型: text-generation
    說明: 輕量級高效模型，適合快速推論 [推薦]
  
  [llama-3.2-1b-instruct]
    名稱: Llama-3.2-1B-Instruct
    大小: ~2.0 GB
    類型: text-generation
    說明: Meta 的指令微調輕量級模型 [推薦]
...
```

### 查看推薦模型

```bash
python scripts/download_model.py --recommendations
```

---

## 📦 模型管理

### 下載模型

#### 基本下載

```bash
# 下載推薦的小型模型
python scripts/download_model.py --download qwen2-1.5b

# 下載會自動創建目錄：Qwen2-1.5B-onnx-ryzenai-npu/
```

#### 自訂輸出目錄

```bash
python scripts/download_model.py --download qwen2-1.5b --output my-models/qwen
```

#### 使用 PowerShell 腳本 (Windows)

```powershell
# 列出模型
.\scripts\download_model_windows.ps1 -List

# 下載模型
.\scripts\download_model_windows.ps1 -ModelId qwen2-1.5b

# 下載到指定目錄
.\scripts\download_model_windows.ps1 -ModelId llama-3.2-1b-instruct -OutputDir my-llama
```

#### 使用 Bash 腳本 (Linux/macOS)

```bash
# 給予執行權限
chmod +x scripts/download_model_linux.sh

# 列出模型
./scripts/download_model_linux.sh --list

# 下載模型
./scripts/download_model_linux.sh --download qwen2-1.5b
```

### 管理已下載的模型

查看已下載的模型：

```bash
# 列出當前目錄中的模型
ls -d *-onnx-ryzenai-npu/

# Windows PowerShell
Get-ChildItem -Directory -Filter "*-onnx-ryzenai-npu"
```

查看模型信息：

```bash
# 每個模型目錄中都有 model_info.json
cat Qwen2-1.5B-onnx-ryzenai-npu/model_info.json
```

---

## 🎯 推論執行

### 單次推論

最簡單的使用方式：

```bash
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --prompt "什麼是人工智慧？"
```

輸出示例：
```
載入模型: Qwen2-1.5B-onnx-ryzenai-npu
✅ 模型載入完成 (耗時: 2.34s)

編碼輸入...
開始生成...

================================================================================
模型輸出:
================================================================================
人工智慧（Artificial Intelligence, AI）是指由機器展現出來的智慧能力，
包括學習、推理、問題解決、感知和語言理解等。AI 系統能夠模擬人類的
認知功能，並在特定任務中達到或超越人類的表現...
================================================================================

✅ 生成完成
生成 tokens: 156
耗時: 22.15s
速度: 7.04 tokens/s
================================================================================
```

### 指定最大生成長度

```bash
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --prompt "寫一篇關於 AI 的短文" \
    --max-length 1024
```

### 互動模式（對話模式）

啟動互動式對話：

```bash
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --interactive
```

使用方式：
```
================================================================================
互動模式 (輸入 'exit' 或 'quit' 離開)
================================================================================

載入模型: Qwen2-1.5B-onnx-ryzenai-npu
✅ 模型載入完成
使用 Chat Template: qwen

👤 你: 你好！

🤖 AI: 你好！很高興見到你。有什麼我可以幫助你的嗎？

👤 你: 什麼是 NPU？

🤖 AI: NPU (Neural Processing Unit) 是專門為神經網路運算設計的處理器...

👤 你: exit

👋 再見！
```

### 指定 Chat Template

某些模型可能需要特定的 chat template：

```bash
# 自動偵測（預設）
python run_npu_inference.py --model <model-dir> --prompt "Hello"

# 手動指定
python run_npu_inference.py \
    --model <model-dir> \
    --prompt "Hello" \
    --template llama3

# 支援的 templates: qwen, llama2, llama3, mistral, phi3, gemma3, chatglm3, gpt, auto
```

### 詳細模式

查看詳細的推論信息（包含格式化後的 prompt）：

```bash
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --prompt "Test" \
    --verbose
```

輸出會包含：
- 使用的 chat template
- 格式化後的完整 prompt
- 生成過程的詳細信息

---

## 🔬 進階功能

### 1. 批次推論

創建批次推論腳本 `batch_inference.py`:

```python
import sys
from pathlib import Path

# 假設 run_npu_inference.py 中的功能可重用
# 這裡展示概念

prompts = [
    "什麼是 AI？",
    "解釋深度學習",
    "NPU 的優勢是什麼？"
]

model_dir = "Qwen2-1.5B-onnx-ryzenai-npu"

for i, prompt in enumerate(prompts, 1):
    print(f"\n{'='*80}")
    print(f"處理 Prompt {i}/{len(prompts)}")
    print(f"{'='*80}")
    # 呼叫推論函數
    # result = run_inference(model_dir, prompt)
```

### 2. 比較不同模型

```bash
# 下載多個模型
python scripts/download_model.py --download qwen2-1.5b
python scripts/download_model.py --download llama-3.2-1b-instruct
python scripts/download_model.py --download phi-3-mini-4k

# 依序測試
for model in Qwen2-1.5B-* Llama-3.2-1B-* Phi-3-mini-*; do
    echo "Testing $model"
    python run_npu_inference.py --model $model --prompt "什麼是 AI？"
done
```

### 3. 程式碼生成

使用程式碼專用模型：

```bash
# 下載 Qwen2.5-Coder
python scripts/download_model.py --download qwen2.5-coder-1.5b

# 生成程式碼
python run_npu_inference.py \
    --model Qwen2.5-Coder-1.5B-Instruct-onnx-ryzenai-npu \
    --prompt "用 Python 寫一個快速排序函數" \
    --max-length 512
```

### 4. 長文本處理

使用長上下文模型：

```bash
# Phi-3-mini-128k 支援 128K token 上下文
python scripts/download_model.py --download phi-3-mini-128k

python run_npu_inference.py \
    --model Phi-3-mini-128k-instruct-onnx-ryzenai-npu \
    --prompt "總結以下文章：[很長的文本]" \
    --max-length 1024
```

---

## 💡 最佳實踐

### 選擇合適的模型

| 使用場景 | 推薦模型 | 原因 |
|---------|---------|------|
| 快速原型開發 | qwen2-1.5b, llama-3.2-1b | 小巧快速，載入時間短 |
| 一般對話 | qwen2.5-3b-instruct | 平衡性能與速度 |
| 程式碼生成 | qwen2.5-coder-7b | 專門優化 |
| 高品質輸出 | qwen2.5-7b-instruct, llama-3.1-8b | 參數更多，輸出品質更好 |
| 長文本處理 | phi-3-mini-128k | 支援超長上下文 |
| 多模態（圖+文）| gemma-3-4b-mm | 唯一支援圖像的模型 |

### 效能優化建議

1. **模型大小與記憶體**
   - 16GB RAM: 建議使用 1-3B 模型
   - 32GB RAM: 可使用 7-8B 模型
   - 64GB+ RAM: 可使用 20B+ 模型

2. **批次大小調整**
   - 單一推論: 使用預設設定
   - 批次處理: 載入模型一次，重複使用

3. **快取策略**
   - 避免重複載入相同模型
   - 在互動模式中保持模型載入狀態

### 提示詞工程 (Prompt Engineering)

**好的 Prompt 範例**：
```bash
# 具體明確
python run_npu_inference.py --model <model> \
    --prompt "請用 Python 寫一個函數，計算斐波那契數列的第 n 項，要求：
    1. 使用遞迴實現
    2. 加上註解
    3. 包含使用範例"

# 結構化
python run_npu_inference.py --model <model> \
    --prompt "角色：你是一個 Python 專家
    任務：解釋裝飾器的概念
    要求：用簡單的例子說明，適合初學者理解"
```

**避免的 Prompt 範例**：
```bash
# 太籠統
"寫程式"

# 太複雜（一次要求太多）
"寫一個完整的電商網站，包含前端、後端、資料庫..."
```

### 錯誤處理

在您的腳本中加入錯誤處理：

```python
import sys
from pathlib import Path

def safe_inference(model_dir, prompt):
    """安全的推論函數"""
    # 檢查模型目錄
    if not Path(model_dir).exists():
        print(f"錯誤：找不到模型目錄 {model_dir}")
        return None
    
    try:
        # 執行推論
        result = run_inference(model_dir, prompt)
        return result
    except Exception as e:
        print(f"推論失敗: {e}")
        return None
```

---

## 📊 效能測試

測試不同模型的效能：

```bash
# 創建測試腳本
cat > test_performance.sh << 'EOF'
#!/bin/bash

PROMPT="什麼是人工智慧？請簡短回答。"

echo "模型效能測試"
echo "=============="

for MODEL in Qwen2-1.5B-* Llama-3.2-1B-* Phi-3-mini-4k-*; do
    echo ""
    echo "測試模型: $MODEL"
    echo "---"
    python run_npu_inference.py --model $MODEL --prompt "$PROMPT" 2>&1 | grep "速度:"
done
EOF

chmod +x test_performance.sh
./test_performance.sh
```

---

## 🔗 下一步

- 💻 [程式開發指南](PROGRAMMING.md) - 整合到您的應用程式
- 🚀 [模型部署指南](MODEL_DEPLOYMENT_GUIDE.md) - 部署更多模型
- 🔧 [故障排除](TROUBLESHOOTING.md) - 解決常見問題
- 📖 [快速參考](../QUICK_REFERENCE.md) - 常用命令速查

---

## 📚 參考資源

- [AMD Ryzen AI 文件](https://www.amd.com/ryzen-ai)
- [ONNX Runtime GenAI](https://github.com/microsoft/onnxruntime-genai)
- [HuggingFace AMD Models](https://huggingface.co/amd)
- [模型配置檔](../configs/models.yaml)
