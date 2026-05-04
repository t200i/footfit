# 快速下載推薦模型（無互動選單）
# 使用方式：powershell -ExecutionPolicy Bypass -File download_recommended.ps1

Write-Host "正在下載推薦模型..." -ForegroundColor Cyan

$models = @(
    "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",           # 4GB - 平衡型
    "amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",     # 8GB - 程式碼
    "amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu",    # 9GB - 高品質
    "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"               # 6.2GB - 圖片理解
)

Write-Host "將下載 $($models.Count) 個模型，總計約 27GB" -ForegroundColor Yellow
Write-Host ""

foreach ($repo in $models) {
    $dirName = $repo -replace '^.*/',''
    Write-Host "下載: $dirName" -ForegroundColor Green
    hf download $repo --local-dir "./$dirName"
    Write-Host ""
}

Write-Host "✅ 下載完成！" -ForegroundColor Green
