# 下載所有可用的 AMD Ryzen AI NPU 模型
# ⚠️ 警告：總大小超過 150GB，需要大量時間和硬碟空間
# 使用方式：powershell -ExecutionPolicy Bypass -File download_all_models.ps1

Write-Host "================================" -ForegroundColor Red
Write-Host "警告：即將下載所有模型" -ForegroundColor Red
Write-Host "================================" -ForegroundColor Red
Write-Host "總大小: ~150GB" -ForegroundColor Yellow
Write-Host "預估時間: 數小時" -ForegroundColor Yellow
Write-Host ""
Write-Host "建議只下載需要的模型，使用 download_models.ps1 進行選擇性下載" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "確定要繼續嗎？(yes/no)"
if ($confirm -ne "yes") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# Collection V1 模型（完全兼容）
$v1Models = @(
    "amd/Qwen2-1.5B-onnx-ryzenai-npu",
    "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
    "amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu",
    "amd/Phi-3-mini-128k-instruct-onnx-ryzenai-npu",
    "amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu",
    "amd/Qwen2-7B-onnx-ryzenai-npu",
    "amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu",
    "amd/Qwen1.5-7B-Chat-onnx-ryzenai-npu",
    "amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
    "amd/CodeLlama-7b-Instruct-hf-onnx-ryzenai-npu",
    "amd/Llama-2-7b-hf-onnx-ryzenai-npu",
    "amd/Llama-2-7b-chat-hf-onnx-ryzenai-npu",
    "amd/Mistral-7B-Instruct-v0.1-onnx-ryzenai-npu",
    "amd/Mistral-7B-Instruct-v0.2-onnx-ryzenai-npu",
    "amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu",
    "amd/Meta-Llama-3-8B-onnx-ryzenai-npu",
    "amd/Llama-3.1-8B-onnx-ryzenai-npu",
    "amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu"
)

# Collection V2 模型（部分可能有兼容性問題）
$v2Models = @(
    "amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu",
    "amd/Llama-3.2-1B-onnx-ryzenai-npu",
    "amd/Qwen-2.5_1.5B_Instruct-onnx-ryzenai-npu",
    "amd/Qwen2.5-Coder-1.5B-Instruct-onnx-ryzenai-npu",
    "amd/DeepSeek-R1-Distill-Qwen-1.5B-onnx-ryzenai-npu",
    "amd/Phi-4-mini-instruct-onnx-ryzenai-npu",
    "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu",
    "amd/ChatGLM3-6B-onnx-ryzenai-npu",
    "amd/DeepSeek-R1-Distill-Qwen-7B-onnx-ryzenai-npu",
    "amd/DeepSeek-R1-Distill-Llama-8B-onnx-ryzenai-npu",
    "amd/gpt-oss-20b-onnx-ryzenai-npu"
)

Write-Host ""
Write-Host "開始下載 Collection V1 模型（$($v1Models.Count) 個）..." -ForegroundColor Green
Write-Host ""

$count = 0
foreach ($repo in $v1Models) {
    $count++
    $dirName = $repo -replace '^.*/',''
    Write-Host "[$count/$($v1Models.Count)] V1: $dirName" -ForegroundColor Cyan
    hf download $repo --local-dir "./$dirName"
    Write-Host ""
}

Write-Host ""
Write-Host "開始下載 Collection V2 模型（$($v2Models.Count) 個）..." -ForegroundColor Yellow
Write-Host "⚠️ 注意：部分 V2 模型可能與當前固件不兼容" -ForegroundColor Yellow
Write-Host ""

$count = 0
foreach ($repo in $v2Models) {
    $count++
    $dirName = $repo -replace '^.*/',''
    Write-Host "[$count/$($v2Models.Count)] V2: $dirName" -ForegroundColor Cyan
    hf download $repo --local-dir "./$dirName"
    Write-Host ""
}

Write-Host ""
Write-Host "✅ 所有模型下載完成！" -ForegroundColor Green
Write-Host ""
Write-Host "已下載模型總數: $($v1Models.Count + $v2Models.Count)" -ForegroundColor Cyan
Write-Host "  - Collection V1: $($v1Models.Count) 個（完全兼容）" -ForegroundColor Green
Write-Host "  - Collection V2: $($v2Models.Count) 個（部分可能不兼容）" -ForegroundColor Yellow
