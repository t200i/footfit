# AMD Ryzen AI - 在你的電腦上運行 AI 模型

> 讓你的筆記型電腦像 ChatGPT 一樣聰明，完全離線、隱私安全

---

## 這是什麼？

這個工具讓你在 **AMD Ryzen AI 電腦** 上直接運行 AI 模型，就像在電腦上安裝 Office 或 Photoshop 一樣簡單。

**你可以做到**：
- 💬 離線對話 - 像 ChatGPT 一樣聊天，但完全在本地運行
- 🖼️ 圖片理解 - 上傳照片，讓 AI 描述內容或回答問題
- 💻 程式碼助手 - 生成程式碼、解釋錯誤、寫文檔
- 📝 文字處理 - 翻譯、摘要、寫作、潤稿
- 🔒 完全隱私 - 資料不上傳雲端，沒有網路也能用

**支援 30+ 種 AI 模型**，從輕量到強大，任你選擇。

---

## 為什麼選擇本地 AI？

| 雲端 AI（如 ChatGPT） | 本地 AI（本工具） |
|---------------------|------------------|
| ❌ 需要網路連線 | ✅ 完全離線工作 |
| ❌ 資料傳到伺服器 | ✅ 資料保留在電腦 |
| ❌ 每月訂閱費用 | ✅ 免費無限使用 |
| ❌ 回應速度受網速影響 | ✅ 快速回應（6-8 字/秒）|
| ❌ 需遵守服務條款 | ✅ 無使用限制 |

**適合你的場景**：
- 🏥 醫療、法律等需要保密的專業工作
- ✈️ 飛機上、戶外等無網路環境
- 💰 想省錢，不想付訂閱費
- 🎓 學習 AI、做研究實驗

---

## 快速開始（3 步驟）

### 前提條件
- ✅ AMD Ryzen AI 系列電腦（帶 NPU 晶片）
- ✅ Windows 11
- ✅ 至少 30GB 硬碟空間

### 步驟 1：安裝 AMD 軟體（一次性設定）

1. **下載並安裝** [AMD Ryzen AI Software](https://www.amd.com/ryzen-ai)（版本 1.7.1 或更新）
2. **設定環境變數**（讓系統找到 AI 引擎）：
   - 開啟「設定」→「系統」→「關於」→「進階系統設定」
   - 點選「環境變數」
   - 在「系統變數」中找到 `Path`，點「編輯」
   - 點「新增」，輸入：`C:\Program Files\RyzenAI\1.7.1\deployment`
   - 按「確定」儲存

3. **開啟 AMD 環境**（每次使用前執行一次）：
   ```powershell
   conda activate ryzen-ai-1.7.1
   ```

4. **安裝下載工具**：
   ```powershell
   pip install huggingface-hub[cli]
   ```

✅ **完成！** 你現在可以下載和運行 AI 模型了。

---

### 步驟 2：下載 AI 模型

**新手推薦**（從這三個選一個）：
```powershell
# 選項 1：輕量級中文模型（2.5GB，適合對話）
hf download amd/Qwen2-1.5B-onnx-ryzenai-npu --local-dir ./Qwen2-1.5B-onnx-ryzenai-npu

# 選項 2：平衡型中文模型（4GB，更聰明）
hf download amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu --local-dir ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu

# 選項 3：圖片理解模型（6.2GB，可以看圖）
hf download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./Gemma-3-4b-it-mm-onnx-ryzenai-npu
```

> 💡 **下載時間**：視網速而定，2.5GB 約需 10-30 分鐘

---

### 步驟 3：開始使用

#### 💬 對話模式（純文字 AI）

```powershell
# 單次提問
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "什麼是人工智慧？"

# 互動對話（像聊天一樣）
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --interactive
```

**實際例子**：
```
你: 幫我寫一封請假信
AI: 當然！請問是什麼原因請假？需要請幾天？我可以幫你撰寫...

你: 因為家庭因素，請 3 天
AI: 好的，以下是請假信範例：

敬啟者：
  因家庭因素需處理私人事務，懇請准予 2026 年 5 月 6 日至 5 月 8 日...
```

---

#### 🖼️ 圖片理解模式（看圖說話）

```powershell
# 分析圖片
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image 照片.jpg --prompt "描述這張圖片"

# 圖片問答
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image 菜單.jpg --prompt "這份菜單有哪些素食選項？"
```

**實際例子**：
- 📸 分析旅遊照片：「這是哪個城市？」
- 📊 讀取圖表：「這張圖表顯示什麼趨勢？」
- 🏠 室內設計：「這個房間的裝潢風格是什麼？」

---

## 選擇適合你的 AI 模型

### 🏃 入門級（快速、輕量）
| 模型名稱 | 大小 | 適合做什麼 | 下載指令 |
|---------|------|----------|---------|
| Qwen2-1.5B | 2.5GB | 日常對話、簡單問答 | `hf download amd/Qwen2-1.5B-onnx-ryzenai-npu --local-dir ./Qwen2-1.5B-onnx-ryzenai-npu` |
| Llama-3.2-1B | 2.0GB | 快速回應、基礎任務 | `hf download amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu --local-dir ./Llama-3.2-1B-Instruct-onnx-ryzenai-npu` |

### ⚖️ 平衡級（推薦）
| 模型名稱 | 大小 | 適合做什麼 | 下載指令 |
|---------|------|----------|---------|
| Qwen2.5-3B | 4GB | 寫作、翻譯、複雜對話 | `hf download amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu --local-dir ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu` |
| Phi-3-mini | 4GB | 專業問答、知識查詢 | `hf download amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu --local-dir ./Phi-3-mini-4k-instruct-onnx-ryzenai-npu` |

### 🚀 進階級（強大、專業）
| 模型名稱 | 大小 | 適合做什麼 | 下載指令 |
|---------|------|----------|---------|
| Qwen2.5-7B | 8GB | 深度分析、專業寫作 | `hf download amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu --local-dir ./Qwen2.5-7B-Instruct-onnx-ryzenai-npu` |
| Qwen2.5-Coder-7B | 8GB | 程式設計、程式碼生成 | `hf download amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu --local-dir ./Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu` |
| Llama-3.1-8B | 9GB | 高品質對話、創意寫作 | `hf download amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu --local-dir ./Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu` |

### 🎨 特殊功能
| 模型名稱 | 大小 | 特殊能力 | 下載指令 |
|---------|------|---------|---------|
| Gemma-3-4b-mm | 6.2GB | **看圖說話** - 理解圖片內容 | `hf download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./Gemma-3-4b-it-mm-onnx-ryzenai-npu` |
| ChatGLM3-6B | 7GB | **中文優化** - 更自然的中文對話 | `hf download amd/ChatGLM3-6B-onnx-ryzenai-npu --local-dir ./ChatGLM3-6B-onnx-ryzenai-npu` |

> 💡 **如何選擇**：
> - 第一次使用 → 選「平衡級」的 Qwen2.5-3B
> - 需要看圖 → 選 Gemma-3-4b-mm
> - 寫程式 → 選 Qwen2.5-Coder-7B
> - 電腦硬碟不夠 → 選「入門級」

---

## 實際應用案例

### 📝 寫作助手
```powershell
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "幫我寫一篇 500 字的產品介紹：智慧手錶" --max-length 512
```

### 🌐 翻譯工具
```powershell
python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --prompt "將以下英文翻譯成中文：Artificial intelligence is transforming..."
```

### 💻 程式碼助手
```powershell
python llm.py --model ./Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu --prompt "用 Python 寫一個計算費氏數列的函數"
```

### 📊 資料分析
```powershell
python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image 銷售圖表.png --prompt "分析這張銷售圖表，告訴我主要趨勢"
```

### 🎓 學習夥伴
```powershell
python llm.py --model ./Phi-3-mini-4k-instruct-onnx-ryzenai-npu --interactive
# 然後問：「解釋什麼是光合作用，用簡單的方式」
```

---

## 遇到問題？

### ❌ 錯誤：「找不到指定的模組」

**解決方法**：每次使用前執行
```powershell
conda activate ryzen-ai-1.7.1
$env:Path = "C:\Program Files\RyzenAI\1.7.1\deployment;$env:Path"
```

---

### ❌ 錯誤：「flat version is not supported」

**原因**：某些新模型（如 Llama-3.2）需要更新的系統固件

**解決方法**：改用其他模型
- ✅ 推薦：Qwen2.5 系列、Phi-3/4 系列、Mistral 系列
- ❌ 暫時避免：Llama-3.2、部分 V2 Collection 模型

---

### ❌ 模型回應太慢或太短

**調整輸出長度**：
```powershell
# 產生更長的回應
python llm.py --model <模型> --prompt "你的問題" --max-length 1024

# 圖片模式
python vlm.py --model <模型> --image 圖片.jpg --prompt "詳細描述" --max-tokens 512
```

---

### ❌ 中文回應出現亂碼

**解決方法**：確保 PowerShell 使用 UTF-8 編碼
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

### 📖 更多幫助

- [詳細安裝指南](docs/INSTALLATION.md)
- [使用教學](docs/USAGE.md)
- [完整故障排除](docs/TROUBLESHOOTING.md)
- [AMD 官方文檔](https://ryzenai.docs.amd.com/)

---

## 進階功能（選用）

### 🔧 查看詳細執行過程
```powershell
python llm.py --model <模型> --prompt "你的問題" --verbose
```

### 📦 批次下載多個模型
建立檔案 `download_models.ps1`：
```powershell
$models = @(
    "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
    "amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu",
    "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"
)

foreach ($model in $models) {
    $name = $model -replace '^.*/',''
    hf download $model --local-dir "./$name"
}
```

執行：
```powershell
powershell -ExecutionPolicy Bypass -File download_models.ps1
```

---

## 系統需求

| 項目 | 最低需求 | 建議配置 |
|------|---------|---------|
| 處理器 | AMD Ryzen AI（含 NPU） | Ryzen AI 9 HX 370/365 |
| 記憶體 | 8GB | 16GB 以上 |
| 硬碟 | 30GB 可用空間 | 50GB 以上 |
| 作業系統 | Windows 11 | Windows 11（最新版） |

**效能參考**：
- 小型模型（1-3GB）：每秒 6-8 個字
- 中型模型（4-8GB）：每秒 5-6 個字
- 大型模型（9GB+）：每秒 3-4 個字

> 💡 **比較**：ChatGPT 在良好網路下約 10-15 字/秒，但本地 AI 完全離線且無使用限制

---

## 完整模型列表

📋 [查看所有 30+ 可用模型](https://huggingface.co/collections/amd/ryzen-ai-17-npu-llm)

**按用途分類**：
- 💬 通用對話：Qwen 系列、Llama 系列、Phi 系列、Mistral 系列
- 💻 程式設計：Qwen2.5-Coder、CodeLlama
- 🇨🇳 中文優化：Qwen 系列、ChatGLM3
- 🖼️ 圖片理解：Gemma-3-4b-mm
- 🧠 推理分析：DeepSeek-R1-Distill 系列

---

## 關於本專案

**開發目標**：讓每個人都能輕鬆使用本地 AI，不需要是工程師

**技術支援**：
- AMD Ryzen AI Software 1.7.1
- ONNX Runtime GenAI 0.11.2
- HuggingFace 模型庫

**授權**：MIT License（免費使用、修改、分享）

**版本**：1.0.0 | **更新日期**：2026 年 5 月 4 日

---

## 常見問題 FAQ

**Q: 這個工具免費嗎？**  
A: 完全免費，沒有任何訂閱費用。只需要一次性設定。

**Q: 需要網路嗎？**  
A: 只有下載模型時需要網路。下載完成後可以完全離線使用。

**Q: 我的資料會被上傳嗎？**  
A: 不會。所有處理都在你的電腦上進行，資料不會離開你的設備。

**Q: 和 ChatGPT 比如何？**  
A: 小型模型（1-3B）適合日常任務，大型模型（7-8B）接近 GPT-3.5 水準。最大優勢是完全離線和隱私保護。

**Q: 可以同時運行多個模型嗎？**  
A: 可以下載多個模型，但一次只能運行一個。

**Q: 我的電腦是 AMD Ryzen AI 嗎？**  
A: 查看「裝置管理器」→「神經處理器」，如果看到「AMD IPU Device」就是支援的。

**Q: 支援 Mac 或 Linux 嗎？**  
A: 目前只支援 Windows 11 + AMD Ryzen AI 處理器。

**Q: 模型可以刪除嗎？**  
A: 可以。直接刪除模型資料夾即可，不影響系統。

---

**🎉 開始你的 AI 之旅！**

第一次使用建議：
1. 下載 `Qwen2.5-3B-Instruct`（平衡型）
2. 執行互動模式：`python llm.py --model ./Qwen2.5-3B-Instruct-onnx-ryzenai-npu --interactive`
3. 試著問：「你能做什麼？」

有問題歡迎查看 [docs/](docs/) 資料夾中的詳細文檔！
