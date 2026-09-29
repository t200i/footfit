@echo off
rem ============================================================================
rem  啟動本地 API（api.py）與 Open WebUI
rem
rem  用法：scripts\webui.bat [model-id]        預設 model-id = gemma4-2b-gpu
rem
rem  可用環境變數覆寫：
rem    API_PORT    API 埠（預設 8000）
rem    WEBUI_PORT  Open WebUI 埠（預設 3000）
rem    ROCM_VENV   api.py 使用的 venv（預設 %USERPROFILE%\.venvs\rocm-pytorch）
rem    WEBUI_VENV  Open WebUI 的 venv（預設 %USERPROFILE%\.venvs\open-webui）
rem    DATA_DIR    Open WebUI 資料夾（預設 %USERPROFILE%\.open-webui-data）
rem
rem  若 API_PORT 上已有 API 在執行，會直接沿用，不另外啟動。
rem  API 在另一個視窗執行；關閉 Open WebUI（Ctrl+C，詢問時回答 N）後會一併關閉。
rem ============================================================================
setlocal
chcp 65001 >nul

set "ROOT=%~dp0.."
set "MODEL=%~1"
if "%MODEL%"=="" set "MODEL=gemma4-2b-gpu"
if not defined API_PORT set "API_PORT=8000"
if not defined WEBUI_PORT set "WEBUI_PORT=3000"
if not defined ROCM_VENV set "ROCM_VENV=%USERPROFILE%\.venvs\rocm-pytorch"
if not defined WEBUI_VENV set "WEBUI_VENV=%USERPROFILE%\.venvs\open-webui"
if not defined DATA_DIR set "DATA_DIR=%USERPROFILE%\.open-webui-data"

set "API_URL=http://127.0.0.1:%API_PORT%/v1"
set "STARTED_API="

if not exist "%ROCM_VENV%\Scripts\python.exe" (
    echo [webui] 找不到 %ROCM_VENV%\Scripts\python.exe，請設定 ROCM_VENV
    exit /b 1
)
if not exist "%WEBUI_VENV%\Scripts\open-webui.exe" (
    echo [webui] 找不到 %WEBUI_VENV%\Scripts\open-webui.exe，請設定 WEBUI_VENV
    exit /b 1
)

rem ── 1. API ───────────────────────────────────────────────────────────────────
curl.exe -s -f -m 3 "%API_URL%/models" >nul 2>&1
if not errorlevel 1 (
    echo [webui] 沿用已在執行的 API：%API_URL%
    goto :webui
)

echo [webui] 啟動 API：%MODEL%（port %API_PORT%）
set "PYTHONIOENCODING=utf-8"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
start "RyzenAI API - %MODEL%" /D "%ROOT%" "%ROCM_VENV%\Scripts\python.exe" api.py --model %MODEL% --host 127.0.0.1 --port %API_PORT%
set "STARTED_API=1"

echo [webui] 等待模型載入（首次執行需下載權重）...
set /a WAITED=0
:wait_api
ping -n 4 127.0.0.1 >nul
curl.exe -s -f -m 3 "%API_URL%/models" >nul 2>&1
if not errorlevel 1 goto :api_ready
set /a WAITED+=3
if %WAITED% geq 900 (
    echo [webui] API 15 分鐘內未就緒，請查看 "RyzenAI API" 視窗的錯誤訊息
    goto :cleanup
)
goto :wait_api
:api_ready
echo [webui] API 就緒：%API_URL%

rem ── 2. Open WebUI ────────────────────────────────────────────────────────────
:webui
rem OPENAI_API_BASE_URL 只在資料夾首次初始化時寫入；之後以 Admin Panel ^> Settings ^> Connections 為準
set "OPENAI_API_BASE_URL=%API_URL%"
set "OPENAI_API_KEY=local"
set "ENABLE_OLLAMA_API=false"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo [webui] 啟動 Open WebUI：http://localhost:%WEBUI_PORT%（資料夾 %DATA_DIR%）
rem 在 DATA_DIR 下執行，讓 .webui_secret_key 與資料放在一起，而非建立在 repo 內
pushd "%DATA_DIR%"
"%WEBUI_VENV%\Scripts\open-webui.exe" serve --host 127.0.0.1 --port %WEBUI_PORT%
popd

rem ── 3. 清理 ──────────────────────────────────────────────────────────────────
:cleanup
if not defined STARTED_API goto :eof
echo [webui] 關閉 API（port %API_PORT%）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:"127.0.0.1:%API_PORT% .*LISTENING"') do taskkill /PID %%p /F >nul 2>&1
endlocal
