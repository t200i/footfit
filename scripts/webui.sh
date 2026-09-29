#!/usr/bin/env bash
# ============================================================================
#  啟動本地 API（api.py）與 Open WebUI（Linux / macOS / Windows Git Bash）
#
#  用法：scripts/webui.sh [model-id]          預設 model-id = gemma4-2b-gpu
#
#  可用環境變數覆寫：
#    API_PORT    API 埠（預設 8000）
#    WEBUI_PORT  Open WebUI 埠（預設 3000）
#    ROCM_VENV   api.py 使用的 venv（預設 ~/.venvs/rocm-pytorch）
#    WEBUI_VENV  Open WebUI 的 venv（預設 ~/.venvs/open-webui）
#    DATA_DIR    Open WebUI 資料夾（預設 ~/.open-webui-data）
#
#  若 API_PORT 上已有 API 在執行，會直接沿用，不另外啟動。
#  API log 寫入 $DATA_DIR/api.log；Ctrl+C 結束時會一併關閉本腳本啟動的 API。
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="${1:-gemma4-2b-gpu}"
API_PORT="${API_PORT:-8000}"
WEBUI_PORT="${WEBUI_PORT:-3000}"
ROCM_VENV="${ROCM_VENV:-$HOME/.venvs/rocm-pytorch}"
WEBUI_VENV="${WEBUI_VENV:-$HOME/.venvs/open-webui}"
DATA_DIR="${DATA_DIR:-$HOME/.open-webui-data}"
API_URL="http://127.0.0.1:${API_PORT}/v1"

# venv 執行檔：Windows 為 Scripts/*.exe，Linux/macOS 為 bin/*
venv_bin() {
    if [ -e "$1/Scripts/$2.exe" ]; then echo "$1/Scripts/$2.exe"; else echo "$1/bin/$2"; fi
}
API_PYTHON="$(venv_bin "$ROCM_VENV" python)"
WEBUI_BIN="$(venv_bin "$WEBUI_VENV" open-webui)"

[ -e "$API_PYTHON" ] || { echo "[webui] 找不到 $API_PYTHON，請設定 ROCM_VENV" >&2; exit 1; }
[ -e "$WEBUI_BIN" ]  || { echo "[webui] 找不到 $WEBUI_BIN，請設定 WEBUI_VENV" >&2; exit 1; }
mkdir -p "$DATA_DIR"

api_up() { curl -s -f -m 3 "$API_URL/models" >/dev/null 2>&1; }

API_PID=""
cleanup() {
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        echo "[webui] 關閉 API（pid $API_PID）"
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# ── 1. API ───────────────────────────────────────────────────────────────────
if api_up; then
    echo "[webui] 沿用已在執行的 API：$API_URL"
else
    echo "[webui] 啟動 API：$MODEL（port $API_PORT，log：$DATA_DIR/api.log）"
    (
        cd "$ROOT"
        PYTHONIOENCODING=utf-8 HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
            exec "$API_PYTHON" api.py --model "$MODEL" --host 127.0.0.1 --port "$API_PORT"
    ) >"$DATA_DIR/api.log" 2>&1 &
    API_PID=$!

    echo "[webui] 等待模型載入（首次執行需下載權重）..."
    for _ in $(seq 1 300); do
        api_up && break
        if ! kill -0 "$API_PID" 2>/dev/null; then
            echo "[webui] API 啟動失敗，最後 20 行 log：" >&2
            tail -n 20 "$DATA_DIR/api.log" >&2
            exit 1
        fi
        sleep 3
    done
    api_up || { echo "[webui] API 15 分鐘內未就緒，請查看 $DATA_DIR/api.log" >&2; exit 1; }
    echo "[webui] API 就緒：$API_URL"
fi

# ── 2. Open WebUI ────────────────────────────────────────────────────────────
# OPENAI_API_BASE_URL 只在資料夾首次初始化時寫入；之後以 Admin Panel > Settings > Connections 為準
export OPENAI_API_BASE_URL="$API_URL"
export OPENAI_API_KEY="local"
export ENABLE_OLLAMA_API="false"
export DATA_DIR

echo "[webui] 啟動 Open WebUI：http://localhost:${WEBUI_PORT}（資料夾 $DATA_DIR）"
# 在 DATA_DIR 下執行，讓 .webui_secret_key 與資料放在一起，而非建立在 repo 內
cd "$DATA_DIR"
"$WEBUI_BIN" serve --host 127.0.0.1 --port "$WEBUI_PORT"
