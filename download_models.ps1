# AMD Ryzen AI 模型批次下載工具
# 使用方式：powershell -ExecutionPolicy Bypass -File download_models.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AMD Ryzen AI 模型下載工具" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 hf 命令是否可用
try {
    $null = Get-Command hf -ErrorAction Stop
} catch {
    Write-Host "❌ 錯誤：找不到 hf 命令" -ForegroundColor Red
    Write-Host "請先安裝 HuggingFace CLI：" -ForegroundColor Yellow
    Write-Host "pip install huggingface-hub[cli]" -ForegroundColor Yellow
    exit 1
}

# 模型分類
$models = @{
    "入門級 (2-2.5GB)" = @(
        @{name="Qwen2-1.5B"; repo="amd/Qwen2-1.5B-onnx-ryzenai-npu"; size="2.5GB"; desc="中文對話、快速回應"}
        @{name="Llama-3.2-1B"; repo="amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu"; size="2.0GB"; desc="輕量級模型（⚠️ 可能有兼容性問題）"}
    )
    "平衡級 (4-4.5GB) - 推薦" = @(
        @{name="Qwen2.5-3B"; repo="amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu"; size="4GB"; desc="寫作、翻譯、對話"}
        @{name="Phi-3-mini"; repo="amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu"; size="4GB"; desc="專業問答"}
        @{name="Phi-3.5-mini"; repo="amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu"; size="4GB"; desc="升級版 Phi-3"}
    )
    "進階級 (7-9GB)" = @(
        @{name="Qwen2.5-7B"; repo="amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu"; size="8GB"; desc="高品質對話"}
        @{name="Qwen2.5-Coder-7B"; repo="amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu"; size="8GB"; desc="程式碼生成"}
        @{name="Llama-3.1-8B"; repo="amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu"; size="9GB"; desc="創意寫作"}
        @{name="Mistral-7B-v0.3"; repo="amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu"; size="8GB"; desc="高品質輸出"}
    )
    "特殊功能" = @(
        @{name="Gemma-3-4b-mm"; repo="amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"; size="6.2GB"; desc="🎨 圖片理解（VLM）"}
        @{name="ChatGLM3-6B"; repo="amd/ChatGLM3-6B-onnx-ryzenai-npu"; size="7GB"; desc="🇨🇳 中文優化"}
    )
}

# 顯示模型選單
Write-Host "請選擇要下載的模型組合：" -ForegroundColor Green
Write-Host ""
Write-Host "[1] 快速入門包（推薦新手）" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB) - 平衡型中文模型" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB) - 圖片理解模型" -ForegroundColor Gray
Write-Host "    總計: ~10GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[2] 完整平衡包" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB)" -ForegroundColor Gray
Write-Host "    - Phi-3-mini (4GB)" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB)" -ForegroundColor Gray
Write-Host "    總計: ~14GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[3] 專業開發包" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB)" -ForegroundColor Gray
Write-Host "    - Qwen2.5-Coder-7B (8GB)" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB)" -ForegroundColor Gray
Write-Host "    總計: ~18GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[4] 全功能包（需要大硬碟）" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B, Qwen2.5-7B, Qwen2.5-Coder-7B" -ForegroundColor Gray
Write-Host "    - Llama-3.1-8B, Phi-3-mini" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm, ChatGLM3-6B" -ForegroundColor Gray
Write-Host "    總計: ~45GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[5] 自訂選擇（顯示完整列表）" -ForegroundColor Yellow
Write-Host "[0] 取消" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "請輸入選項 (0-5)"

$downloadList = @()

switch ($choice) {
    "1" {
        $downloadList = @(
            "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
            "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"
        )
    }
    "2" {
        $downloadList = @(
            "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
            "amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu",
            "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"
        )
    }
    "3" {
        $downloadList = @(
            "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
            "amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
            "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"
        )
    }
    "4" {
        $downloadList = @(
            "amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu",
            "amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu",
            "amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu",
            "amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu",
            "amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu",
            "amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu",
            "amd/ChatGLM3-6B-onnx-ryzenai-npu"
        )
    }
    "5" {
        Write-Host ""
        Write-Host "完整模型列表：" -ForegroundColor Cyan
        Write-Host ""
        
        $index = 1
        $allModels = @()
        foreach ($category in $models.Keys) {
            Write-Host "--- $category ---" -ForegroundColor Yellow
            foreach ($model in $models[$category]) {
                Write-Host "[$index] $($model.name) - $($model.size) - $($model.desc)" -ForegroundColor Gray
                $allModels += $model.repo
                $index++
            }
            Write-Host ""
        }
        
        Write-Host "請輸入要下載的模型編號（用逗號分隔，例如: 1,3,5）：" -ForegroundColor Green
        $selections = Read-Host "編號"
        
        if ($selections -match '^\d+(,\d+)*$') {
            $indices = $selections.Split(',') | ForEach-Object { [int]$_.Trim() - 1 }
            foreach ($idx in $indices) {
                if ($idx -ge 0 -and $idx -lt $allModels.Count) {
                    $downloadList += $allModels[$idx]
                }
            }
        } else {
            Write-Host "❌ 輸入格式錯誤" -ForegroundColor Red
            exit 1
        }
    }
    "0" {
        Write-Host "已取消下載" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "❌ 無效的選項" -ForegroundColor Red
        exit 1
    }
}

if ($downloadList.Count -eq 0) {
    Write-Host "❌ 沒有選擇任何模型" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "開始下載 $($downloadList.Count) 個模型" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($repo in $downloadList) {
    $modelName = $repo -replace '^.*/',''
    
    Write-Host "[$($successCount + $failCount + 1)/$($downloadList.Count)] 下載: $modelName" -ForegroundColor Green
    Write-Host "Repository: $repo" -ForegroundColor Gray
    
    try {
        hf download $repo --local-dir "./$modelName"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 完成: $modelName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "❌ 失敗: $modelName (錯誤碼: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "❌ 失敗: $modelName - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "下載完成" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ 成功: $successCount" -ForegroundColor Green
Write-Host "❌ 失敗: $failCount" -ForegroundColor Red
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "🎉 你可以開始使用模型了！" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "範例指令：" -ForegroundColor Yellow
    Write-Host "  python llm.py --model ./<模型目錄> --interactive" -ForegroundColor Gray
    Write-Host "  python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image test.jpg --prompt '描述圖片'" -ForegroundColor Gray
}
