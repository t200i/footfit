# AMD Ryzen AI Model Downloader
# Usage: powershell -ExecutionPolicy Bypass -File download_models.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AMD Ryzen AI Model Downloader" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if hf command is available
try {
    $null = Get-Command hf -ErrorAction Stop
} catch {
    Write-Host "ERROR: hf command not found" -ForegroundColor Red
    Write-Host "Please install HuggingFace CLI first:" -ForegroundColor Yellow
    Write-Host "pip install huggingface-hub[cli]" -ForegroundColor Yellow
    exit 1
}

# Model catalog
$models = @{
    "Entry Level (2-2.5GB)" = @(
        @{name="Qwen2-1.5B"; repo="amd/Qwen2-1.5B-onnx-ryzenai-npu"; size="2.5GB"; desc="Fast response"}
        @{name="Llama-3.2-1B"; repo="amd/Llama-3.2-1B-Instruct-onnx-ryzenai-npu"; size="2.0GB"; desc="Lightweight (may have compatibility issues)"}
    )
    "Balanced (4-4.5GB) - Recommended" = @(
        @{name="Qwen2.5-3B"; repo="amd/Qwen2.5-3B-Instruct-onnx-ryzenai-npu"; size="4GB"; desc="Writing, translation, chat"}
        @{name="Phi-3-mini"; repo="amd/Phi-3-mini-4k-instruct-onnx-ryzenai-npu"; size="4GB"; desc="Professional QA"}
        @{name="Phi-3.5-mini"; repo="amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu"; size="4GB"; desc="Improved Phi-3"}
    )
    "Advanced (7-9GB)" = @(
        @{name="Qwen2.5-7B"; repo="amd/Qwen2.5-7B-Instruct-onnx-ryzenai-npu"; size="8GB"; desc="High quality chat"}
        @{name="Qwen2.5-Coder-7B"; repo="amd/Qwen2.5-Coder-7B-Instruct-onnx-ryzenai-npu"; size="8GB"; desc="Code generation"}
        @{name="Llama-3.1-8B"; repo="amd/Meta-Llama-3.1-8B-Instruct-onnx-ryzenai-npu"; size="9GB"; desc="Creative writing"}
        @{name="Mistral-7B-v0.3"; repo="amd/Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu"; size="8GB"; desc="High quality output"}
    )
    "Special Features" = @(
        @{name="Gemma-3-4b-mm"; repo="amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu"; size="6.2GB"; desc="Image understanding (VLM)"}
        @{name="ChatGLM3-6B"; repo="amd/ChatGLM3-6B-onnx-ryzenai-npu"; size="7GB"; desc="Chinese optimized"}
    )
}

# Display menu
Write-Host "Select model package to download:" -ForegroundColor Green
Write-Host ""
Write-Host "[1] Quick Start Pack (Recommended for beginners)" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB) - Balanced Chinese model" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB) - Image understanding" -ForegroundColor Gray
Write-Host "    Total: ~10GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[2] Complete Balanced Pack" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB)" -ForegroundColor Gray
Write-Host "    - Phi-3-mini (4GB)" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB)" -ForegroundColor Gray
Write-Host "    Total: ~14GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[3] Professional Development Pack" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B (4GB)" -ForegroundColor Gray
Write-Host "    - Qwen2.5-Coder-7B (8GB)" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm (6.2GB)" -ForegroundColor Gray
Write-Host "    Total: ~18GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[4] Full Feature Pack (Requires large disk)" -ForegroundColor Yellow
Write-Host "    - Qwen2.5-3B, Qwen2.5-7B, Qwen2.5-Coder-7B" -ForegroundColor Gray
Write-Host "    - Llama-3.1-8B, Phi-3-mini" -ForegroundColor Gray
Write-Host "    - Gemma-3-4b-mm, ChatGLM3-6B" -ForegroundColor Gray
Write-Host "    Total: ~45GB" -ForegroundColor Gray
Write-Host ""

Write-Host "[5] Custom Selection (Show full list)" -ForegroundColor Yellow
Write-Host "[0] Cancel" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "Enter option (0-5)"

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
        Write-Host "Full Model List:" -ForegroundColor Cyan
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
        
        Write-Host "Enter model numbers to download (comma separated, e.g.: 1,3,5):" -ForegroundColor Green
        $selections = Read-Host "Numbers"
        
        if ($selections -match '^\d+(,\d+)*$') {
            $indices = $selections.Split(',') | ForEach-Object { [int]$_.Trim() - 1 }
            foreach ($idx in $indices) {
                if ($idx -ge 0 -and $idx -lt $allModels.Count) {
                    $downloadList += $allModels[$idx]
                }
            }
        } else {
            Write-Host "ERROR: Invalid input format" -ForegroundColor Red
            exit 1
        }
    }
    "0" {
        Write-Host "Download cancelled" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "ERROR: Invalid option" -ForegroundColor Red
        exit 1
    }
}

if ($downloadList.Count -eq 0) {
    Write-Host "ERROR: No models selected" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting download of $($downloadList.Count) models" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($repo in $downloadList) {
    $modelName = $repo -replace '^.*/',''
    
    Write-Host "[$($successCount + $failCount + 1)/$($downloadList.Count)] Downloading: $modelName" -ForegroundColor Green
    Write-Host "Repository: $repo" -ForegroundColor Gray
    
    try {
        hf download $repo --local-dir "./$modelName"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS: $modelName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "FAILED: $modelName (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "FAILED: $modelName - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Download Complete" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "SUCCESS: $successCount" -ForegroundColor Green
Write-Host "FAILED: $failCount" -ForegroundColor Red
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "You can now start using the models!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Example commands:" -ForegroundColor Yellow
    Write-Host "  python llm.py --model ./<model_dir> --interactive" -ForegroundColor Gray
    Write-Host "  python vlm.py --model ./Gemma-3-4b-it-mm-onnx-ryzenai-npu --image test.jpg --prompt 'Describe'" -ForegroundColor Gray
}
