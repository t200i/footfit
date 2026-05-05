# 模型補丁文件夾

此目錄包含 AMD 官方模型包中**缺失或不完整**的必要文件。

## 為什麼需要補丁？

部分 AMD 官方發布的模型包存在以下問題：
- 缺少 `chat_template.jinja` 文件（對話格式定義）
- 其他配置文件不完整

這些缺失會導致模型無法正常運行，出現類似 `RuntimeError: Empty chat template` 的錯誤。

## 補丁列表

### SmolLM2-135M-Instruct_rai_1.7.1_npu_4K
- **缺失文件**: `chat_template.jinja`
- **格式**: ChatML (使用 `<|im_start|>` 和 `<|im_end|>`)
- **症狀**: `RuntimeError: Empty chat template`
- **修復**: 複製 `patches/SmolLM2-135M-Instruct/chat_template.jinja` 到模型目錄

## 使用方法

### 手動應用補丁

```powershell
# 複製補丁文件到對應的模型目錄
Copy-Item ".\patches\SmolLM2-135M-Instruct\chat_template.jinja" `
          ".\SmolLM2-135M-Instruct_rai_1.7.1_npu_4K\"
```

### 自動應用所有補丁

```powershell
python patches\apply_patches.py
```

## 新增補丁

如果發現其他模型也缺少必要文件：

1. 在 `patches/` 下創建對應模型的文件夾
2. 將補丁文件放入該文件夾
3. 更新本 README.md 的補丁列表
4. 更新 `apply_patches.py` 腳本

## 注意事項

- 補丁文件基於 AMD 官方模型規範創建
- 僅用於修復官方發布的不完整模型包
- 如果 AMD 更新模型包，這些補丁可能不再需要
