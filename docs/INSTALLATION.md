# AMD Ryzen AI NPU 安裝指南

本指南將協助您在 Windows 11 系統上安裝 AMD Ryzen AI NPU 開發環境。

---

## 📋 系統需求

### 硬體需求
- **處理器**: AMD Ryzen AI 系列處理器（含 NPU）
  - 例如: Ryzen AI 9 HX 370, Ryzen AI 9 HX 365, Ryzen AI 5 340, Ryzen AI 7 350 等
- **記憶體**: 建議 16GB 以上
- **硬碟空間**: 至少 50GB 可用空間（用於模型儲存）

### 軟體需求
- **作業系統**: Windows 11 (22H2 或更新版本)
- **Python**: Python 3.8 - 3.12（建議 3.11 或 3.12）
- **驅動程式**: AMD Ryzen AI Software 1.7.1 或更新版本

---

## 🔧 安裝步驟

### 步驟 1: 檢查硬體支援

1. **確認處理器型號**
   ```powershell
   wmic cpu get name
   ```
   輸出應包含 "Ryzen AI" 字樣

2. **檢查 NPU 裝置**
   ```powershell
   Get-PnpDevice | Where-Object {$_.FriendlyName -like "*NPU*"}
   ```
   應該看到類似 "AMD IPU Device" 的裝置

3. **查看 NPU 詳細信息**
   ```powershell
   Get-PnpDevice | Where-Object {$_.FriendlyName -like "*IPU*"} | Select-Object Status, Class, FriendlyName, InstanceId
   ```

### 步驟 2: 安裝 AMD Ryzen AI Software

1. **下載 AMD Ryzen AI Software**
   - 訪問 [AMD 官方網站](https://www.amd.com/ryzen-ai)
   - 下載最新版 Ryzen AI Software (建議 1.7.1 或更新)

2. **安裝軟體**
   - 執行下載的安裝程式
   - 按照安裝精靈指示完成安裝
   - 安裝後重新啟動電腦

3. **驗證安裝**
   ```powershell
   # 檢查安裝路徑
   Test-Path "C:\Program Files\AMD\RyzenAI"
   ```

### 步驟 3: 設定 Python 環境

#### 選項 A: 使用 Conda（推薦）

1. **安裝 Miniconda**
   - 下載: https://docs.conda.io/en/latest/miniconda.html
   - 安裝後重啟終端機

2. **創建專用環境**
   ```bash
   # 創建 Python 3.12 環境
   conda create -n ryzen-ai python=3.12 -y
   
   # 啟用環境
   conda activate ryzen-ai
   ```

3. **驗證 Python 版本**
   ```bash
   python --version
   # 輸出應為: Python 3.12.x
   ```

#### 選項 B: 使用 venv

1. **創建虛擬環境**
   ```powershell
   # 創建環境
   python -m venv ryzen-ai-env
   
   # 啟用環境
   .\ryzen-ai-env\Scripts\Activate.ps1
   ```

2. **升級 pip**
   ```bash
   python -m pip install --upgrade pip
   ```

### 步驟 4: 安裝必要套件

1. **安裝核心套件**
   ```bash
   pip install onnxruntime-genai
   pip install huggingface_hub
   pip install pyyaml
   ```

2. **安裝 AMD 特定套件**（如果需要）
   ```bash
   pip install onnxruntime-vitisai
   pip install onnxruntime_providers_ryzenai
   ```

3. **驗證安裝**
   ```python
   # 測試 onnxruntime-genai
   python -c "import onnxruntime_genai as og; print('✅ onnxruntime-genai 安裝成功')"
   
   # 測試 huggingface_hub
   python -c "import huggingface_hub; print('✅ huggingface_hub 安裝成功')"
   ```

### 步驟 5: 下載並測試模型

1. **克隆本專案**
   ```bash
   git clone <your-repo-url>
   cd FY115-BCI-Agent
   ```

2. **下載測試模型**
   ```bash
   # 下載小型測試模型（約 2.5 GB）
   python scripts/download_model.py --download qwen2-1.5b
   ```

3. **執行測試推論**
   ```bash
   # 測試模型
   python run_npu_inference.py --model Qwen2-1.5B-onnx-ryzenai-npu --prompt "Hello, AI!"
   ```

4. **預期輸出**
   ```
   載入模型: Qwen2-1.5B-onnx-ryzenai-npu
   ✅ 模型載入完成 (耗時: X.XXs)
   
   編碼輸入...
   開始生成...
   
   ================================================================================
   模型輸出:
   ================================================================================
   Hello! How can I assist you today?
   ================================================================================
   
   ✅ 生成完成
   生成 tokens: XX
   耗時: X.XXs
   速度: X.XX tokens/s
   ================================================================================
   ```

---

## 🔍 驗證安裝

### 檢查清單

- [ ] AMD Ryzen AI 處理器已識別
- [ ] NPU 裝置在裝置管理員中顯示正常
- [ ] AMD Ryzen AI Software 已安裝
- [ ] Python 環境已設定（3.8-3.12）
- [ ] `onnxruntime-genai` 已安裝
- [ ] `huggingface_hub` 已安裝
- [ ] 至少一個模型已下載
- [ ] 測試推論成功執行

### 環境檢查腳本

創建 `check_environment.py`:

```python
#!/usr/bin/env python3
"""環境檢查腳本"""

import sys

print("=" * 80)
print("AMD Ryzen AI NPU 環境檢查")
print("=" * 80)

# 檢查 Python 版本
print(f"\n✓ Python 版本: {sys.version}")

# 檢查必要套件
packages = {
    'onnxruntime_genai': 'onnxruntime-genai',
    'huggingface_hub': 'huggingface_hub',
    'yaml': 'pyyaml'
}

for module, package in packages.items():
    try:
        __import__(module)
        print(f"✓ {package} 已安裝")
    except ImportError:
        print(f"✗ {package} 未安裝 - 執行: pip install {package}")

print("\n" + "=" * 80)
print("檢查完成！")
print("=" * 80)
```

執行:
```bash
python check_environment.py
```

---

## ⚠️ 常見問題

### 問題 1: 找不到 NPU 裝置

**症狀**: 裝置管理員中沒有 NPU/IPU 相關裝置

**解決方案**:
1. 確認處理器確實支援 NPU（Ryzen AI 系列）
2. 更新 BIOS 到最新版本
3. 安裝或更新 AMD Ryzen AI Software
4. 檢查 Windows 更新

### 問題 2: onnxruntime-genai 安裝失敗

**症狀**: `pip install onnxruntime-genai` 報錯

**解決方案**:
```bash
# 確保使用正確的 Python 版本
python --version

# 升級 pip
python -m pip install --upgrade pip

# 嘗試指定版本安裝
pip install onnxruntime-genai==0.11.2

# 或從 wheel 安裝
pip install onnxruntime-genai --find-links https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-genai/pypi/simple/
```

### 問題 3: 模型下載緩慢或失敗

**症狀**: 從 HuggingFace 下載模型很慢或中斷

**解決方案**:
```bash
# 設定 HuggingFace 鏡像（中國大陸用戶）
export HF_ENDPOINT=https://hf-mirror.com

# 或使用代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 續傳下載
python scripts/download_model.py --download <model-id>
```

### 問題 4: 權限錯誤

**症狀**: PowerShell 無法執行腳本

**解決方案**:
```powershell
# 允許執行腳本（以管理員身份）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或僅針對當前 session
Set-ExecutionPolicy Bypass -Scope Process
```

### 問題 5: 記憶體不足

**症狀**: 載入大型模型時記憶體不足

**解決方案**:
- 選擇較小的模型（1.5B-3B 參數）
- 關閉其他應用程式
- 增加系統記憶體
- 使用模型量化版本

---

## 📚 下一步

安裝完成後，您可以：

1. 📖 閱讀 [使用指南](USAGE.md) 學習基本操作
2. 💻 查看 [程式開發指南](PROGRAMMING.md) 整合到您的專案
3. 🚀 探索 [模型部署指南](MODEL_DEPLOYMENT_GUIDE.md) 部署其他模型
4. 🔧 參考 [故障排除](TROUBLESHOOTING.md) 解決問題

---

## 🔗 相關資源

- [AMD Ryzen AI 官方文件](https://www.amd.com/ryzen-ai)
- [ONNX Runtime GenAI GitHub](https://github.com/microsoft/onnxruntime-genai)
- [HuggingFace AMD Collections](https://huggingface.co/amd)
- [AMD Community Forums](https://community.amd.com/)
