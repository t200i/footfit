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
