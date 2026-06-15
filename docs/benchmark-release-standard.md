# AI Benchmark 數據合約規章

本文件定義以「數據合約（Data Contract）」為核心的模型資源管理機制。  
數據合約是多 Agent 協作中的**早期知識禮物**——在 Agent 做出工具選擇之前，先以結構化方式揭露平台的能力邊界與存取規則，透過物理隔離與漸進式移轉策略，使 Agent 在逆向選擇時自然傾向使用平台資源而非繞道內部工具。

完成初次 ACR 設定與第一次發布約需 **30 分鐘**。

---

## 設計理念

### 問題：多 Agent 的逆向選擇

當多個 Agent 協作時，Agent 面臨工具選擇的資訊不對稱：  
平台方的資源能力不透明 → Agent 傾向使用自己熟悉的內建工具 → 平台資源閒置、難以計量各團隊貢獻。

### 解法：數據合約作為早期知識禮物

在 Agent 決策之前，主動給出一份可機讀的合約，揭露：

- **能力聲明**：這個模型能做什麼、支援什麼輸入格式
- **存取規則**：如何取得授權、授權的時效與範圍
- **使用量回報義務**：每次推論後的計量責任

這不是限制，而是**讓平台選項比內部工具更容易被 Agent 讀懂與選擇**。

### 三層機制

```
1. 物理隔離層（Physical Isolation）
   └── Docker 容器封裝推論邏輯，Agent 只能透過 API 存取，無法直取底層權重或程式碼

2. 漸進式移轉層（Progressive Transfer）
   └── License Key 控制存取範圍，平台決定哪些帳戶可用哪些模型

3. Principal-Agent 監測層（Usage Monitoring）
   └── 授權購買時即結算設備月數，帳本同步更新 Deployer Budget 與 Model Owner Credit
```

---

## 事前準備

開始之前，請確認：

- 您擁有 Azure 訂閱 **`eosl-r3-aihub`** 的存取權，且角色為 **Owner** 或 **Contributor**
- 您擁有 GitHub 儲存庫的 **Admin** 權限（用於設定 Repository Secrets）
- 本地端已安裝 **Docker Engine** 與 **Azure CLI 2.0.80+**

> **本規章所使用的 Azure 資源均固定如下。** 若您套用至其他專案，請在對應欄位以自己的資源名稱取代。

| Azure 資源 | 固定名稱 |
|---|---|
| 訂閱 | `eosl-r3-aihub` |
| 資源群組 | `ai-hub-webui` |
| Container Registry | `model-cards` |
| ACR 完整網域 | `model-cards.azurecr.io` |

---

## 概覽

```
上架方（模型貢獻團隊）
  └── 建置 Docker Image（含 Model Card 合約）→ 推送至 model-cards

平台（model-cards.azurecr.io）
  ├── 儲存 Image 與 Model Card（ACR Manifest Labels）
  ├── 核發 License Key（控制哪些帳戶可用哪些模型）
  └── 授權購買時結算 Dual-Ledger（Deployer Budget / Model Owner Credit）

使用方（Edge 裝置 / 下游 Agent）
  ├── 持有 License Key → 容器啟動時 Activation Handshake（物理隔離閘門）
  ├── 拉取 Image → 只能透過 API 存取推論能力（無法直取底層）
  └── 到期由 `license_expires_at` + 時鐘校正自動處理，無需持續連線 AI Hub
```

---

## 總覽

| 層級 | 名稱 | 適用情境 | 強制性 |
|------|------|---------|--------|
| Layer 1 | Model Card 與版本管理 | **所有** benchmark 專案 | ✅ 必須 |
| Layer 2 | 容器化、授權與使用量監測 | Linux iGPU（ROCm）路線（**正式支援**） | ✅ 必須 |
| Layer 3 | Windows NPU 特殊路徑 | Windows-native NPU（XDNA）路線 | 🟡 進階待評估 |

---

## Layer 1 — Model Card 與版本管理（所有專案必須）

### 1.1 Model Card（ACR Image Manifest Labels）

每個發布的 Docker Image **必須**在 `Dockerfile` 中透過 `LABEL` 指令嵌入 Model Card，  
供平台從 `model-cards` 的 Manifest 直接讀取，無需掛載額外檔案。

#### 必要 Labels

| Label 鍵 | 說明 | 範例值 |
|----------|------|--------|
| `ai.benchmark.model-id` | 模型識別名稱（與 registry.py 一致） | `gemma4-4b-gpu` |
| `ai.benchmark.model-name` | 人類可讀的模型全名 | `Google Gemma 4 4B` |
| `ai.benchmark.model-version` | 模型版本（來源版本號） | `4.0` |
| `ai.benchmark.backend` | 推論後端 | `igpu-rocm` / `npu-vitisai` |
| `ai.benchmark.hardware` | 建議執行硬體 | `AMD Ryzen AI 9 HX 370` |
| `ai.benchmark.framework-version` | 本 benchmark 框架版本 | `1.2.0` |
| `ai.benchmark.input-types` | 支援的輸入類型（逗號分隔） | `text,image` |
| `ai.benchmark.context-length` | 最大 context 長度（tokens） | `8192` |
| `ai.benchmark.license-required` | 是否需要 License Key 才能啟動 | `true` |
| `ai.benchmark.model-owner` | 模型擁有者帳號（鎖定，決定 Credit 歸屬） | `team-amd-ryzenai` |

#### Dockerfile 範例（以 `gemma4-4b-gpu` 為例）

```dockerfile
# ── Model Card（嵌入 ACR Image Manifest）────────────────────────────────────
LABEL ai.benchmark.model-id="gemma4-4b-gpu" \
      ai.benchmark.model-name="Google Gemma 4 4B" \
      ai.benchmark.model-version="4.0" \
      ai.benchmark.backend="igpu-rocm" \
      ai.benchmark.hardware="AMD Ryzen AI 9 HX 370" \
      ai.benchmark.framework-version="1.2.0" \
      ai.benchmark.input-types="text,image" \
      ai.benchmark.context-length="8192" \
      ai.benchmark.license-required="true" \
      ai.benchmark.model-owner="team-amd-ryzenai"
```

#### 從 ACR 讀取 Model Card（平台側）

```bash
# 拉取指定 Image 的 Manifest Labels（無需 pull 整個 Image）
az acr manifest show \
  --registry model-cards \
  --name itri/rocm/ryzenai-benchmark:1.2.0 \
  --query "config.Labels"
```

---

### 1.2 版本管理與 CHANGELOG

- Docker Image tag 格式：`<framework-version>-<backend>`，例如 `1.2.0-rocm`
- 框架版本號遵循 [SemVer 2.0](https://semver.org/)，以 Git tag 標記（例如 `v1.2.0`）
- 根目錄**必須**存在 `CHANGELOG.md`，每個版本條目至少包含：
  - 新增或更新的模型
  - Model Card Labels 變更
  - 遙測欄位異動（會影響下游平台的監測與獎酬計算）

---

## Layer 2 — 容器化、授權與使用量監測（Linux iGPU 正式支援）

### 2.1 Dockerfile 規範

Dockerfile **必須**採用多階段建置，並於第二階段嵌入 Model Card Labels。  
Image 命名規則：

```
model-cards.azurecr.io/<供應商>/<軟體堆疊>/<模型>:<tag>
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| `<供應商>` | 模型或框架的原始供應商 | `amd`, `google`, `itri` |
| `<軟體堆疊>` | 推論後端 / 硬體路徑 | `rocm`, `npu`, `cpu`, `cuda` |
| `<模型>` | 模型名稱（小寫、連字號分隔） | `gemma4-4b`, `llama3-8b`, `ryzenai-benchmark` |
| `<tag>` | 語意化版本號 | `latest`, `1.2.0` |

範例：

```
# AMD ROCm 路徑的 Gemma 4 模型
model-cards.azurecr.io/amd/rocm/gemma4-4b:latest

# ITRI 自有 benchmark 工具（ROCm 後端）
model-cards.azurecr.io/itri/rocm/ryzenai-benchmark:1.2.0
```

完整 Dockerfile 範例：

```dockerfile
# ── Stage 1: 依賴安裝 ──────────────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: 執行映像 ──────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

COPY --from=builder /install /usr/local
COPY ryzenai/ ./ryzenai/
COPY api.py cli.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# weights 由外部掛載，不打包進 Image
VOLUME ["/app/weights"]

EXPOSE 8000

ENV HOST="0.0.0.0"
ENV PORT="8000"

# ── Model Card ──────────────────────────────────────────────────────────────
LABEL ai.benchmark.model-id="gemma4-4b-gpu" \
      ai.benchmark.model-name="Google Gemma 4 4B" \
      ai.benchmark.model-version="4.0" \
      ai.benchmark.backend="igpu-rocm" \
      ai.benchmark.hardware="AMD Ryzen AI 9 HX 370" \
      ai.benchmark.framework-version="1.2.0" \
      ai.benchmark.input-types="text,image" \
      ai.benchmark.context-length="8192" \
      ai.benchmark.license-required="true" \
      ai.benchmark.model-owner="team-amd-ryzenai"

ENTRYPOINT ["./entrypoint.sh"]
```

---

### 2.2 License Key 授權機制

每個 Edge 裝置透過 `AIHUB_LICENSE_KEY` 環境變數取得授權，**不需要掛載任何本地授權檔案**。

License Key 由 AI Hub Portal 核發，格式為不透明字串。容器啟動時自動向 Hub 完成 Activation Handshake，將 Key 綁定至設備指紋（CPU + MAC + hostname）。

詳細交握流程見 [docs/aihub-activation-handshake.md](./aihub-activation-handshake.md)。

---

### 2.3 `entrypoint.sh` — License 驗證守門

```bash
#!/bin/bash
set -euo pipefail

echo "[entrypoint] 啟動 AI Benchmark 服務..."

# ── 1. License Key 必填檢查 ─────────────────────────────────────────────────
if [ -z "${AIHUB_LICENSE_KEY:-}" ]; then
  echo "[entrypoint][ERROR] 環境變數 AIHUB_LICENSE_KEY 未設定" >&2
  echo "[entrypoint][ERROR] 請從 AI Hub Portal 取得授權金鑰，以 -e AIHUB_LICENSE_KEY=<key> 傳入" >&2
  exit 1
fi

# ── 2. Activation Handshake（由 Python 執行，取得 session_token）──────────
python - <<'EOF'
import sys
from ryzenai.license import activate
result = activate()  # 向 Hub 驗證 Key、綁定指紋、取得 session_token
if not result.ok:
    print(f"[entrypoint][ERROR] {result.error}: {result.message}", file=sys.stderr)
    sys.exit(1)
print(f"[entrypoint] 授權驗證通過（到期日：{result.license_expires_at}）")
EOF

# ── 3. Weights 掛載確認（NPU ONNX 模型需要本地 weights）──────────────────
MODEL_ID=$(python -c "from ryzenai.config import MODEL_ID; print(MODEL_ID)")
if [[ "${MODEL_ID}" == *"-npu"* ]]; then
  if [ ! -d "/app/weights" ] || [ -z "$(ls -A /app/weights)" ]; then
    echo "[entrypoint][ERROR] NPU 模型 weights 目錄為空：/app/weights" >&2
    exit 1
  fi
fi
  fi
fi

echo "[entrypoint] 啟動推論服務，模型：${MODEL_ID}"
exec python api.py \
  --model "${MODEL_ID}" \
  --host "${HOST}" \
  --port "${PORT}"
```

---

### 2.4 授權驗證機制（Principal-Agent 監測）

帳本在**授權購買時**一次結算，不依賴執行期推論計量：

- **Deployer Budget**：購買 N 設備月授權 → 帳本 −N
- **Model Owner Credit**：同一筆購買 → 模型擁有者帳本 +N（依 `ai.benchmark.model-owner` Label 決定歸屬）

排行榜直接查詢帳本累計值，無需 runtime telemetry。

容器在執行期間僅傳送**定期心跳**（每小時一次），確認 License Key 尚未被撤銷，不回報任何推論數據。詳細交握流程見 [docs/aihub-activation-handshake.md](./aihub-activation-handshake.md)。

> `ai.benchmark.model-owner` 欄位在 Model Card 發布時鎖定，不可事後修改。此欄位決定每筆授權購買的 Credit 歸屬。

---

### 2.5 建立 Azure Container Registry（初次設定）

本節操作只需執行一次。`model-cards` 已存在於資源群組 `ai-hub-webui` 時可跳過。

1. 在 Azure Portal 頂部搜尋列輸入 **Container registries**，確認 **`model-cards`** 是否已存在於訂閱 **`eosl-r3-aihub`** 下。

2. 若尚未建立，在終端機執行：

   ```bash
   az login
   az account set --subscription eosl-r3-aihub

   az group create \
     --name ai-hub-webui \
     --location eastasia

   az acr create \
     --resource-group ai-hub-webui \
     --name model-cards \
     --sku Standard \
     --admin-enabled false
   ```

   > **為什麼 `--admin-enabled false`？** Admin 帳號使用靜態密碼，無法輪替。本規章改用 Service Principal，能夠定期換證並精確限制權限。

3. 建立完成後，記錄以下資訊（後續步驟使用）：

   ```bash
   az acr show \
     --name model-cards \
     --query "{loginServer:loginServer, id:id}" \
     --output table
   ```

---

### 2.6 建立 Edge 裝置拉取用 Service Principal（初次設定）

Edge 裝置拉取 Image 使用獨立 Service Principal，賦予最小權限（僅 `acrpull`）。

1. 取得 ACR 的 Resource ID：

   ```bash
   ACR_ID=$(az acr show \
     --name model-cards \
     --query id \
     --output tsv)
   ```

2. 建立 Service Principal，賦予 `acrpull` 角色：

   ```bash
   az ad sp create-for-rbac \
     --name "sp-model-cards-edge-pull" \
     --role acrpull \
     --scopes ${ACR_ID} \
     --years 1
   ```

   指令執行後會輸出類似以下內容，請**妥善保存** `appId` 與 `password`：

   ```json
   {
     "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
     "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   }
   ```

   > **重要**：`password` 離開此頁面後無法再次查閱，請立即存入 Key Vault 或安全密碼管理工具。

---

### 2.7 設定 GitHub Repository Secrets

CI/CD 所需的憑證統一存放於 GitHub Repository Secrets，不寫入原始碼。

1. 前往 GitHub 儲存庫，選取 **Settings**。

2. 在左側選取 **Secrets and variables** → **Actions**。

3. 選取 **Secrets** 分頁，依序選取 **New repository secret**，新增以下兩個 secret：

   | Secret 名稱 | 值 |
   |---|---|
   | **AZURE_CREDENTIALS** | `az ad sp create-for-rbac --sdk-auth` 輸出的完整 JSON（需另建一個 Contributor SP 用於 CI） |
   | **ACR_NAME** | `model-cards` |

---

### 2.8 建置並推送 Image（每次發布）

每次推送 Git tag（格式 `v*.*.*`）時，GitHub Actions 自動執行建置與推送。  
手動執行時，步驟如下：

1. 登入 ACR：

   ```bash
   az login
   az acr login --name model-cards
   ```

2. 建置並標記 Image：

   ```bash
   VERSION="1.2.0"   # 對應 Git tag v1.2.0

   docker build \
     -t model-cards.azurecr.io/itri/rocm/ryzenai-benchmark:${VERSION} \
     .
   ```

3. 推送至 ACR：

   ```bash
   docker push model-cards.azurecr.io/itri/rocm/ryzenai-benchmark:${VERSION}
   ```

4. 確認 Image 與 Model Card Labels 已上傳：

   ```bash
   az acr manifest show \
     --registry model-cards \
     --name itri/rocm/ryzenai-benchmark:${VERSION} \
     --query "config.Labels" \
     --output table
   ```

---

### 2.9 GitHub Actions — Release Pipeline

```yaml
# .github/workflows/release.yml
name: Release — Build & Push to ACR

on:
  push:
    tags: ['v*.*.*']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        run: az acr login --name ${{ secrets.ACR_NAME }}

      - name: Extract version tag
        id: version
        run: echo "tag=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Build and push (ROCm / iGPU)
        run: |
          IMAGE="${{ secrets.ACR_NAME }}.azurecr.io/ryzenai-benchmark:${{ steps.version.outputs.tag }}-rocm"
          docker build -t ${IMAGE} .
          docker push ${IMAGE}
```

---

### 2.10 每月金鑰輪替（`scripts/rotate_sp_key.sh`）

Edge 裝置用 Service Principal 的密碼需每月輪替，建議透過排程任務自動執行。

```bash
#!/bin/bash
# 建議搭配 Azure Automation 或 cron 每月執行一次

SP_APP_ID="<步驟 2.6 取得的 appId>"
KV_NAME="<存放密碼的 Key Vault 名稱>"
SECRET_NAME="model-cards-pull-password"

NEW_PASSWORD=$(az ad sp credential reset \
  --id ${SP_APP_ID} \
  --query password \
  --output tsv)

az keyvault secret set \
  --vault-name ${KV_NAME} \
  --name ${SECRET_NAME} \
  --value "${NEW_PASSWORD}"

echo "金鑰輪替完成：${KV_NAME}/${SECRET_NAME}"
```

> Edge 裝置應從 Key Vault 動態讀取 ACR 密碼，而非在本地硬式編碼。

---

### 2.11 Edge 裝置部署（`docker-compose.yml`）

下游 Edge 裝置取得 License Key 後，使用以下 `docker-compose.yml` 啟動服務：

```yaml
# docker-compose.yml（供 Edge 設備下游使用）
services:
  ryzenai-benchmark:
    image: model-cards.azurecr.io/itri/rocm/ryzenai-benchmark:1.2.0
    restart: unless-stopped
    environment:
      AIHUB_LICENSE_KEY: <你的授權金鑰>
    ports:
      - "8000:8000"
    volumes:
      - ./weights:/app/weights:ro       # 本地 weights（唯讀）
    devices:
      - /dev/kfd                        # AMD ROCm iGPU 直通
      - /dev/dri
```

啟動後，服務對外暴露於 `http://localhost:8000`，相容 OpenAI Chat Completions API。

---

## Layer 3 — Windows NPU 特殊路徑（進階待評估）

AMD Ryzen AI NPU（VitisAI EP）因驅動僅支援 Windows，目前尚無成熟的 Linux 容器化方案。  
**此路線不納入正式支援，待 PoC 評估後決定是否升級為正式規格。**

### 3.1 技術限制

| 限制項目 | 說明 |
|---------|------|
| 驅動僅支援 Windows | NPU Driver 32.x 無 Linux 版本，Linux Docker 無法直通 |
| VitisAI EP DLL 依賴 | 需要 `C:\Program Files\RyzenAI\` 下的 DLL，容器化困難 |
| Windows Container 成熟度 | GPU/NPU 直通支援遠不如 Linux + Docker |

### 3.2 暫行方案（License Key 等效控制）

在 Docker 容器化可行前，NPU 路線採用以下替代授權機制：

| Layer 2 功能 | NPU 暫行替代方案 |
|-------------|----------------|
| ACR Image 存取控制 | Azure Blob Storage SAS Token（30 天有效期） |
| License Key 驗證 | 相同機制，由 `entrypoint.py` 在 Conda 環境中執行 Activation Handshake |
| 時鐘校正 | 相同邏輯，記憶體持有 `clock_offset`，每次推論前檢查 |
| 金鑰輪替 | SAS Token 自動過期 + 通知客戶重新取得 |

---

## 附錄 A：驗收清單（Acceptance Checklist）

每次發布前，由負責人對照以下清單確認：

### Layer 1（所有專案必查）
- [ ] `CHANGELOG.md` 已更新本版本條目
- [ ] Git tag 格式符合 `v<major>.<minor>.<patch>`
- [ ] Dockerfile 已嵌入所有必要 Model Card Labels
- [ ] `ai.benchmark.license-required` 與 `ai.benchmark.model-owner` 已正確設定

### Layer 2（Linux iGPU 容器化）
- [ ] `Dockerfile` 採多階段建置
- [ ] `entrypoint.sh` 在 License Key 無效或過期時正確終止（exit code 1）
- [ ] Activation Handshake 在測試環境中成功完成，取得 `session_token` 與 `server_time`
- [ ] 時鐘校正 `clock_offset` 正確計算，調慢系統時鐘時觸發 `CLOCK_TAMPER` 終止
- [ ] ACR 映像路徑格式正確（例：`model-cards.azurecr.io/itri/rocm/ryzenai-benchmark:1.2.0`）
- [ ] Service Principal `sp-model-cards-edge-pull` 僅持有 `acrpull` 權限
- [ ] `release.yml` 成功在 CI 執行並推送至 `model-cards`
- [ ] Edge 裝置以 `docker-compose.yml` 啟動並驗證 `http://localhost:8000/v1/models` 正常回應

### Layer 3（Windows NPU）
- [ ] 已完成 PoC 評估報告並存入 `docs/`
- [ ] 暫行方案（Conda + SAS Token）已在目標裝置驗證

---

## 附錄 B：套用至其他 Benchmark 專案的客製化指引

本規章設計為**框架無關（Framework-agnostic）**。套用至其他專案時需調整：

| 需客製化的項目 | 本規章預設值 | 其他專案替換說明 |
|--------------|------------|----------------|
| ACR Image 路徑 | `itri/rocm/ryzenai-benchmark` | 替換為 `<供應商>/<軟體堆疊>/<模型>` |
| `ai.benchmark.model-owner` | `team-amd-ryzenai` | 替換為對應模型擁有者帳號 |
| Dockerfile `LABEL` 區塊 | `gemma4-4b-gpu` 相關資訊 | 替換為對應模型的 Model Card 資訊 |
| `entrypoint.sh` 的 weights 路徑邏輯 | `/app/weights` | 依各專案 weights 目錄結構調整 |
| `docker-compose.yml` 的 `devices` 區塊 | AMD ROCm（`/dev/kfd`, `/dev/dri`） | 依硬體替換（見下表） |

> 訂閱 `eosl-r3-aihub`、資源群組 `ai-hub-webui`、ACR `model-cards` 為本平台固定資源，**所有 benchmark 專案共用**，不需替換。

### 各加速器 Docker device 直通參數

| 加速器 | Vendor | `docker-compose.yml` 設定 |
|--------|--------|--------------------------|
| NVIDIA GPU | NVIDIA | `runtime: nvidia` + `NVIDIA_VISIBLE_DEVICES=all` |
| AMD iGPU (ROCm) | AMD | `devices: [/dev/kfd, /dev/dri]` |
| AMD NPU (XDNA) | AMD | 尚在評估（參閱 Layer 3） |
| Intel GPU (OpenVINO) | Intel | `devices: [/dev/dri]` |
| Qualcomm QNN | Qualcomm | 依各 SDK 文件指定裝置節點 |
