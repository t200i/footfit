# AMD Ryzen AI NPU 故障排除指南

本指南提供常見問題的診斷和解決方案。

---

## 📋 目錄

1. [安裝問題](#安裝問題)
2. [模型載入問題](#模型載入問題)
3. [推論執行問題](#推論執行問題)
4. [效能問題](#效能問題)
5. [環境問題](#環境問題)

---

## 🔧 安裝問題

### 問題 1: 找不到 NPU 裝置

**症狀**:
```
裝置管理員中沒有顯示 AMD IPU Device
```

**診斷步驟**:
```powershell
# 檢查處理器
wmic cpu get name

# 檢查 PnP 裝置
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*IPU*"}
```

**解決方案**:

1. **確認硬體支援**
   - 確保處理器是 AMD Ryzen AI 系列
   - 支援的型號: Ryzen AI 9 HX 370/365, Ryzen AI 7 350, Ryzen AI 5 340 等

2. **更新 BIOS**
   - 訪問主機板製造商網站
   - 下載最新 BIOS 版本
   - 依照說明更新

3. **安裝 AMD Ryzen AI Software**
   - 下載最新版本: https://www.amd.com/ryzen-ai
   - 完整安裝後重啟

4. **檢查 Windows 更新**
   ```powershell
   # 檢查更新
   Start-Process ms-settings:windowsupdate
   ```

---

### 問題 2: onnxruntime-genai 安裝失敗

**症狀**:
```
ERROR: Could not find a version that satisfies the requirement onnxruntime-genai
```

**解決方案**:

#### 方案 A: 升級 pip

```bash
python -m pip install --upgrade pip setuptools wheel
pip install onnxruntime-genai
```

#### 方案 B: 指定版本

```bash
pip install onnxruntime-genai==0.11.2
```

#### 方案 C: 從 Azure DevOps 安裝

```bash
pip install onnxruntime-genai --find-links https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-genai/pypi/simple/
```

#### 方案 D: 檢查 Python 版本

```bash
# 確認 Python 版本 (需要 3.8-3.12)
python --version

# 如果版本不符，創建新環境
conda create -n ryzen-ai python=3.12
conda activate ryzen-ai
pip install onnxruntime-genai
```

---

### 問題 3: huggingface_hub 下載失敗

**症狀**:
```
ConnectionError: Failed to download model
```

**解決方案**:

#### 方案 A: 檢查網路連線

```bash
# 測試連線
ping huggingface.co
```

#### 方案 B: 使用鏡像站（中國大陸用戶）

```bash
# Linux/macOS
export HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"

# 然後下載
python scripts/download_model.py --download qwen2-1.5b
```

#### 方案 C: 使用代理

```bash
# Linux/macOS
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# Windows PowerShell
$env:HTTP_PROXY="http://your-proxy:port"
$env:HTTPS_PROXY="http://your-proxy:port"
```

#### 方案 D: 手動下載

```bash
# 使用 git lfs
git lfs install
git clone https://huggingface.co/amd/Qwen2-1.5B-onnx-ryzenai-npu
```

---

## 📦 模型載入問題

### 問題 4: 模型目錄找不到

**症狀**:
```
❌ 錯誤：找不到模型目錄 'Qwen2-1.5B-onnx-ryzenai-npu'
```

**診斷**:
```powershell
# 列出當前目錄
ls

# 檢查模型目錄是否存在
Test-Path "Qwen2-1.5B-onnx-ryzenai-npu"
```

**解決方案**:

1. **確認目錄名稱**
   ```bash
   # 列出所有模型目錄
   ls -d *-onnx-ryzenai-npu
   ```

2. **使用絕對路徑**
   ```bash
   python run_npu_inference.py \
       --model "C:\Users\YourName\models\Qwen2-1.5B-onnx-ryzenai-npu" \
       --prompt "Hello"
   ```

3. **重新下載模型**
   ```bash
   python scripts/download_model.py --download qwen2-1.5b
   ```

---

### 問題 5: 模型載入錯誤

**症狀**:
```
Exception: Failed to load model
```

**診斷**:
```bash
# 檢查模型文件完整性
ls Qwen2-1.5B-onnx-ryzenai-npu/

# 應包含:
# - model.onnx 或 gemma-3-vision-npu.onnx 等
# - genai_config.json
# - tokenizer.json
# - processor_config.json (某些模型)
```

**解決方案**:

1. **檢查檔案完整性**
   ```powershell
   # 檢查關鍵檔案
   Test-Path "Qwen2-1.5B-onnx-ryzenai-npu\model.onnx"
   Test-Path "Qwen2-1.5B-onnx-ryzenai-npu\genai_config.json"
   ```

2. **重新下載模型**
   ```bash
   # 刪除損壞的模型
   rm -rf Qwen2-1.5B-onnx-ryzenai-npu
   
   # 重新下載
   python scripts/download_model.py --download qwen2-1.5b
   ```

3. **檢查磁碟空間**
   ```powershell
   Get-PSDrive C | Select-Object Used,Free
   ```

---

## ⚡ 推論執行問題

### 問題 6: 生成失敗或輸出為空

**症狀**:
```
❌ 生成失敗: ...
或
模型輸出為空
```

**解決方案**:

#### 方案 A: 檢查 Prompt 格式

```python
# ✅ 正確：使用適當的 chat template
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --prompt "Hello" \
    --template qwen

# ❌ 錯誤：template 不匹配
python run_npu_inference.py \
    --model Qwen2-1.5B-onnx-ryzenai-npu \
    --prompt "Hello" \
    --template llama2  # 錯誤的 template
```

#### 方案 B: 增加 max_length

```bash
# 可能 max_length 太小
python run_npu_inference.py \
    --model <model> \
    --prompt "寫一篇文章" \
    --max-length 1024  # 增加長度
```

#### 方案 C: 檢查記憶體

```powershell
# 檢查可用記憶體
Get-Counter '\Memory\Available MBytes'

# 如果記憶體不足，使用較小的模型
python scripts/download_model.py --download qwen2-1.5b  # 2.5GB
```

---

### 問題 7: 中文顯示亂碼

**症狀**:
```
��������  (顯示為亂碼)
```

**解決方案**:

#### 方案 A: 設定終端編碼 (Windows)

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 或在腳本中
chcp 65001
```

#### 方案 B: 使用 Python UTF-8 包裝器

已在 `download_model.py` 中實作：
```python
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

#### 方案 C: 使用 Windows Terminal

- 安裝 Windows Terminal (從 Microsoft Store)
- Windows Terminal 預設支援 UTF-8

---

### 問題 8: 互動模式卡住

**症狀**:
```
互動模式啟動後無回應
```

**解決方案**:

1. **檢查是否在等待輸入**
   - 確認看到 `You:` 提示符
   - 嘗試輸入簡單的問題

2. **重啟並使用詳細模式**
   ```bash
   python run_npu_inference.py \
       --model <model> \
       --prompt "Test" \
       --verbose  # 查看詳細信息
   ```

3. **檢查模型載入狀態**
   - 觀察載入時間
   - 確認出現 "✅ 模型載入完成"

---

## 🚀 效能問題

### 問題 9: 推論速度過慢

**症狀**:
```
速度: 2.5 tokens/s  (預期應該 6-8 tokens/s)
```

**診斷**:
```powershell
# 檢查 CPU 使用率
Get-Counter '\Processor(_Total)\% Processor Time'

# 檢查記憶體使用
Get-Counter '\Memory\Available MBytes'

# 檢查 NPU 裝置狀態
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*IPU*"}
```

**解決方案**:

#### 方案 A: 確認使用 NPU (不是 CPU)

檢查 `genai_config.json`:
```json
{
  "model": {
    "type": "ryzenai",  // 應該是 ryzenai，不是 cpu
    ...
  }
}
```

#### 方案 B: 關閉其他應用程式

```powershell
# 查看占用資源的程序
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

#### 方案 C: 使用較小的模型

```bash
# 1.5B-3B 參數的模型速度更快
python scripts/download_model.py --download qwen2-1.5b
```

#### 方案 D: 調整生成參數

```python
# 減少 max_length
params.set_search_options(max_length=256)  # 原本 512

# 使用 greedy decoding
params.set_search_options(do_sample=False, temperature=0.0)
```

---

### 問題 10: 記憶體不足

**症狀**:
```
MemoryError: Unable to allocate memory
```

**解決方案**:

#### 方案 A: 使用較小的模型

| 記憶體大小 | 推薦模型大小 |
|-----------|------------|
| 8GB RAM   | 1.5B       |
| 16GB RAM  | 1.5B-3B    |
| 32GB RAM  | 7B-8B      |
| 64GB+ RAM | 20B+       |

```bash
# 小型模型
python scripts/download_model.py --download qwen2-1.5b  # ~2.5GB
python scripts/download_model.py --download llama-3.2-1b  # ~2.0GB
```

#### 方案 B: 關閉其他程式

```powershell
# 關閉不必要的應用程式
Stop-Process -Name chrome, firefox  # 示例
```

#### 方案 C: 增加虛擬記憶體 (分頁檔)

Windows 設定:
1. 系統 > 進階系統設定
2. 效能 > 設定
3. 進階 > 虛擬記憶體 > 變更
4. 自訂大小: 初始 16384 MB, 最大 32768 MB

---

## 🔧 環境問題

### 問題 11: Python 版本不符

**症狀**:
```
Python 3.7 不支援
```

**解決方案**:

```bash
# 使用 conda 創建正確版本環境
conda create -n ryzen-ai python=3.12
conda activate ryzen-ai

# 或使用 pyenv
pyenv install 3.12.0
pyenv local 3.12.0
```

---

### 問題 12: 套件衝突

**症狀**:
```
ERROR: Package conflicts detected
```

**解決方案**:

```bash
# 創建全新的乾淨環境
conda create -n ryzen-ai-clean python=3.12
conda activate ryzen-ai-clean

# 按順序安裝
pip install onnxruntime-genai
pip install huggingface_hub
pip install pyyaml
```

---

### 問題 13: PowerShell 執行政策錯誤

**症狀**:
```
無法載入檔案，因為這個系統上已停用指令碼執行
```

**解決方案**:

```powershell
# 選項 1: 修改執行政策（當前使用者）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 選項 2: 僅針對當前 session
Set-ExecutionPolicy Bypass -Scope Process

# 選項 3: 直接執行 Python 腳本
python scripts/download_model.py --list
```

---

## 🔍 診斷工具

### 環境檢查腳本

創建 `diagnose.py`:

```python
#!/usr/bin/env python3
"""環境診斷腳本"""

import sys
import os
from pathlib import Path

print("="*80)
print("AMD Ryzen AI NPU 環境診斷")
print("="*80)

# Python 版本
print(f"\n1. Python 版本: {sys.version}")
if sys.version_info < (3, 8) or sys.version_info >= (3, 13):
    print("   ⚠️  警告: 建議使用 Python 3.8-3.12")
else:
    print("   ✅ 版本正確")

# 檢查套件
print("\n2. 必要套件:")
packages = {
    'onnxruntime_genai': 'onnxruntime-genai',
    'huggingface_hub': 'huggingface_hub',
    'yaml': 'pyyaml'
}

for module, package in packages.items():
    try:
        __import__(module)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} - 執行: pip install {package}")

# 檢查模型
print("\n3. 已下載的模型:")
model_dirs = list(Path('.').glob('*-onnx-ryzenai-npu'))
if model_dirs:
    for model_dir in model_dirs:
        print(f"   ✅ {model_dir.name}")
else:
    print("   ⚠️  未找到模型")
    print("   執行: python scripts/download_model.py --download qwen2-1.5b")

# 檢查配置文件
print("\n4. 專案檔案:")
files_to_check = [
    'configs/models.yaml',
    'scripts/download_model.py',
    'run_npu_inference.py'
]

for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ {file_path}")

print("\n" + "="*80)
print("診斷完成")
print("="*80)
```

執行:
```bash
python diagnose.py
```

---

## 📞 獲取協助

### 收集診斷信息

在尋求幫助時，請提供：

1. **系統信息**
   ```powershell
   # CPU
   wmic cpu get name
   
   # OS
   wmic os get caption,version
   
   # Python 版本
   python --version
   ```

2. **套件版本**
   ```bash
   pip list | grep onnx
   pip list | grep huggingface
   ```

3. **錯誤訊息**
   - 完整的錯誤堆疊
   - 執行的命令
   - 預期行為 vs 實際行為

### 相關資源

- [AMD Community Forums](https://community.amd.com/)
- [ONNX Runtime Issues](https://github.com/microsoft/onnxruntime/issues)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- 專案 Issues: (您的 GitHub repo)

---

## 📚 下一步

- 📖 [安裝指南](INSTALLATION.md)
- 🎯 [使用指南](USAGE.md)
- 💻 [程式開發指南](PROGRAMMING.md)
- 📋 [快速參考](../QUICK_REFERENCE.md)
