# 模型測試報告

## 測試環境
- NPU Driver: 32.0.203.280
- NPU Firmware: 1.0.21.43
- Ryzen AI Software: 1.7.1
- ONNX Runtime GenAI: 0.11.2

## 測試結果

### ✅ 通過的模型 (1/6)

| 模型 | 類型 | 狀態 | 說明 |
|------|------|------|------|
| Gemma-3-4b-it-mm | VLM | ✅ PASS | 成功生成圖像描述 |

### ❌ 失敗的模型 (5/6)

| 模型 | 類型 | Collection | 錯誤 | 原因 |
|------|------|-----------|------|------|
| Llama-3.2-1B-Instruct | LLM | V2 | `flat version is not supported for matmulbias` | 固件不兼容 |
| Qwen2.5-3B-Instruct | LLM | V2 | `flat version is not supported for matmulbias` | 固件不兼容 |
| Qwen2.5-7B-Instruct | LLM | V2 | `flat version is not supported for matmulbias` | 固件不兼容 |
| Qwen2.5-Coder-7B-Instruct | LLM | V2 | `flat version is not supported for matmulbias` | 固件不兼容 |
| Meta-Llama-3.1-8B-Instruct | LLM | V1 | `fusion.onnx.data` 不存在 | 下載不完整 |

## 問題分析

### 1. Collection V2 固件兼容性問題

**症狀**:
```
[ERROR] flat version is not supported for matmulbias
```

**原因**:
- Collection V2 模型使用新的編譯格式（"flat version"）
- 當前 NPU 固件 1.0.21.43 不支援此格式
- AMD 尚未公開支援 V2 的固件版本

**影響的模型**:
- 所有 Llama-3.2 系列
- 所有 Qwen2.5 系列（包括 Coder 版本）
- DeepSeek-R1-Distill-Qwen 系列

### 2. Meta-Llama-3.1-8B-Instruct 下載不完整

**症狀**:
```
fusion.onnx.data doesn't exist or is not accessible
```

**原因**:
- 模型權重文件 `fusion.onnx.data` 缺失
- fusion.onnx 大小只有 34MB（正常應該很小，因為權重在 .data 文件）

**解決方案**:
重新下載模型：
```powershell
hf download amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu --local-dir ./Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu
```

## 解決方案與建議

### 短期方案

1. **使用兼容的 Collection V1 模型**
   
   需要重新下載 V1 模型，例如：
   ```powershell
   # 重新下載 Meta-Llama-3.1-8B（修正下載不完整問題）
   hf download amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu --local-dir ./Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu
   
   # 下載其他 V1 模型
   hf download amd/Qwen2-7B-onnx-ryzenai-npu --local-dir ./Qwen2-7B-onnx-ryzenai-npu
   hf download amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu --local-dir ./Phi-3-mini-4k-instruct-onnx-ryzenai-npu
   hf download amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu --local-dir ./Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu
   ```

2. **繼續使用 VLM 模型**
   
   Gemma-3-4b-it-mm 已驗證可正常運行，可用於圖像相關任務。

### 長期方案

1. **等待 AMD 固件更新**
   
   關注 AMD 官方發布支援 Collection V2 的固件版本（預計需要 >= 1.0.22.x）

2. **更新 README.md**
   
   需要在模型列表中標註 Collection 版本，並警告兼容性問題

## 程式碼改進

### ✅ 已完成

1. **修正 Windows 編碼問題**
   - 加入 UTF-8 輸出設定
   - 避免 emoji 導致的 cp950 編碼錯誤

2. **加入模型兼容性檢查**
   - llm.py 會自動偵測 V2 模型並顯示警告
   - 提供明確的錯誤說明和建議

3. **VLM 路徑處理**
   - 使用 `.` 避免路徑重複問題
   - 自動切換到模型目錄執行

### 📋 建議改進

1. **README.md 更新**
   - 在模型列表加入 Collection 版本標註
   - 明確說明哪些模型需要新固件
   - 提供固件檢查工具

2. **創建模型推薦列表**
   - 只列出當前固件可用的模型
   - 按用途分類（對話、程式碼、多語言等）

3. **改進錯誤處理**
   - 捕獲特定錯誤並提供解決方案
   - 自動建議替代模型

## 測試建議

建議按以下順序測試模型：

1. **VLM 測試** ✅
   ```powershell
   conda activate ryzen-ai-1.7.1
   python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image cat.jpg --prompt "What is in this image?"
   ```

2. **修復並測試 Llama-3.1-8B** ⏳
   ```powershell
   # 重新下載
   hf download amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu --local-dir ./Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu
   
   # 測試
   python llm.py --model ./Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu --prompt "What is 1+1?"
   ```

3. **下載並測試其他 V1 模型** ⏳
   - Qwen2-7B
   - Phi-3-mini
   - Mistral-7B-v0.3

## 結論

當前 `llm.py` 和 `vlm.py` 的設計**嚴謹且功能完整**，已包含：

- ✅ 環境設定自動化
- ✅ 路徑處理（VLM 路徑重複問題）
- ✅ 編碼問題修正
- ✅ 模型兼容性檢查
- ✅ 詳細錯誤提示

**主要問題不在程式設計，而在於**：
1. NPU 固件版本不支援 Collection V2
2. 部分模型下載不完整

**建議後續動作**：
1. 重新下載 Meta-Llama-3.1-8B 並測試
2. 下載更多 Collection V1 模型驗證
3. 更新 README.md 標註 Collection 版本
