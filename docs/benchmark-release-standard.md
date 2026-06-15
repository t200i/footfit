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
   └── License File 控制存取範圍，平台決定哪些帳戶可用哪些模型

3. Principal-Agent 監測層（Usage Monitoring）
   └── 每次推論的用量回報給平台，供 Principal 驗證各團隊承諾並設計對應獎酬
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
| Container Registry | `model-cards-registry` |
| ACR 完整網域 | `model-cards-registry.azurecr.io` |

---

## 概覽

```
上架方（模型貢獻團隊）
  └── 建置 Docker Image（含 Model Card 合約）→ 推送至 model-cards-registry

平台（model-cards-registry.azurecr.io）
  ├── 儲存 Image 與 Model Card（ACR Manifest Labels）
  ├── 核發 License File（控制哪些帳戶可用哪些模型）
  └── 接收 Usage Telemetry → 供 Principal 驗證承諾與設計獎酬

使用方（Edge 裝置 / 下游 Agent）
  ├── 持有 License File → 容器啟動時驗證（物理隔離閘門）
  ├── 拉取 Image → 只能透過 API 存取推論能力（無法直取底層）
  └── 每次推論後自動回報用量 → 平台即時記錄
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
供平台從 `model-cards-registry` 的 Manifest 直接讀取，無需掛載額外檔案。

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
| `ai.benchmark.license-required` | 是否需要 License File 才能啟動 | `true` |
| `ai.benchmark.telemetry-endpoint` | 計費遙測回報的平台 endpoint | `https://billing.ai-hub.example.com/v1/usage` |

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
      ai.benchmark.telemetry-endpoint="https://billing.ai-hub.example.com/v1/usage"
```

#### 從 ACR 讀取 Model Card（平台側）

```bash
# 拉取指定 Image 的 Manifest Labels（無需 pull 整個 Image）
az acr manifest show \
  --registry model-cards-registry \
  --name ryzenai-benchmark:1.2.0-rocm \
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
Image 命名格式固定為：

```
model-cards-registry.azurecr.io/<model-id>:<framework-version>-<backend>
```

範例：

```
model-cards-registry.azurecr.io/ryzenai-benchmark:1.2.0-rocm
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

# weights 與 license 由外部掛載，不打包進 Image
VOLUME ["/app/weights", "/app/license"]

EXPOSE 8000

ENV MODEL_ID=""
ENV HOST="0.0.0.0"
ENV PORT="8000"
ENV LICENSE_PATH="/app/license/license.json"
ENV TELEMETRY_ENDPOINT="https://billing.ai-hub.example.com/v1/usage"

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
      ai.benchmark.telemetry-endpoint="https://billing.ai-hub.example.com/v1/usage"

ENTRYPOINT ["./entrypoint.sh"]
```

---

### 2.2 License File 授權機制

每個 Edge 裝置在啟動容器前，**必須**持有平台核發的 License File。

#### License File 格式（`license.json`）

```json
{
  "license_id": "lic-abc123",
  "issued_to": "customer-device-001",
  "issued_at": "2026-06-15T00:00:00Z",
  "expires_at": "2026-07-15T00:00:00Z",
  "allowed_models": ["gemma4-4b-gpu", "gemma4-2b-gpu"],
  "signature": "<platform-signed-hmac-sha256>"
}
```

| 欄位 | 說明 |
|------|------|
| `license_id` | 平台核發的唯一授權 ID，用於計費關聯 |
| `issued_to` | 綁定的裝置或客戶識別碼 |
| `expires_at` | 授權到期時間，容器啟動時驗證，過期則拒絕啟動 |
| `allowed_models` | 此授權允許執行的 model-id 清單 |
| `signature` | 平台使用私鑰簽署的 HMAC-SHA256，防止偽造 |

#### 授權驗證流程

1. **容器啟動時**（`entrypoint.sh`）：讀取 `LICENSE_PATH` 並驗證簽章與到期日
2. **驗證失敗**：輸出錯誤說明後以 exit code 1 終止，不啟動推論服務
3. **到期預警**：距到期 7 天內，每次啟動輸出 WARNING 提示

---

### 2.3 `entrypoint.sh` — License 驗證守門

```bash
#!/bin/bash
set -euo pipefail

echo "[entrypoint] 啟動 AI Benchmark 服務..."

# ── 1. License File 驗證 ────────────────────────────────────────────────────
if [ ! -f "${LICENSE_PATH}" ]; then
  echo "[entrypoint][ERROR] License File 不存在：${LICENSE_PATH}" >&2
  echo "[entrypoint][ERROR] 請聯絡平台取得授權檔並掛載至 /app/license/" >&2
  exit 1
fi

python - <<'EOF'
import json, sys, datetime, os

license_path = os.environ["LICENSE_PATH"]
model_id = os.environ["MODEL_ID"]

with open(license_path) as f:
    lic = json.load(f)

expires = datetime.datetime.fromisoformat(lic["expires_at"].replace("Z", "+00:00"))
now = datetime.datetime.now(datetime.timezone.utc)
if now > expires:
    print(f"[entrypoint][ERROR] 授權已於 {lic['expires_at']} 到期，請向平台申請續約", file=sys.stderr)
    sys.exit(1)

days_left = (expires - now).days
if days_left <= 7:
    print(f"[entrypoint][WARNING] 授權將於 {days_left} 天後到期（{lic['expires_at']}），請提前續約")

if model_id not in lic.get("allowed_models", []):
    print(f"[entrypoint][ERROR] 此授權不允許執行模型 '{model_id}'，許可清單：{lic['allowed_models']}", file=sys.stderr)
    sys.exit(1)

print(f"[entrypoint] License 驗證通過（授權 ID：{lic['license_id']}，剩餘 {days_left} 天）")
EOF

# ── 2. MODEL_ID 必填檢查 ────────────────────────────────────────────────────
if [ -z "${MODEL_ID}" ]; then
  echo "[entrypoint][ERROR] 環境變數 MODEL_ID 未設定" >&2
  exit 1
fi

# ── 3. Weights 掛載確認（NPU ONNX 模型需要本地 weights）──────────────────
if [[ "${MODEL_ID}" == *"-npu"* ]]; then
  if [ ! -d "/app/weights" ] || [ -z "$(ls -A /app/weights)" ]; then
    echo "[entrypoint][ERROR] NPU 模型 weights 目錄為空：/app/weights" >&2
    exit 1
  fi
fi

echo "[entrypoint] 啟動推論服務，模型：${MODEL_ID}"
exec python api.py \
  --model "${MODEL_ID}" \
  --host "${HOST}" \
  --port "${PORT}"
```

---

### 2.4 使用量遙測（Principal-Agent 監測）

每次推論完成後，框架層**必須**非同步地向 `TELEMETRY_ENDPOINT` 回報使用量資料，供平台：

1. **驗證承諾**：比對各貢獻團隊聲明的模型能力與實際被使用的情況
2. **設計獎酬**：Principal 依據實際用量，核算對貢獻團隊符合承諾的回報
3. **漸進開放決策**：用量低或回報異常的模型，可縮減其 License 存取範圍

遙測邏輯在 API 層（`api.py`）統一注入，**不侵入**模型模組（`ryzenai/modules/`）。

#### 遙測 Payload（HTTP POST JSON）

```json
{
  "schema_version": "1.0",
  "license_id": "lic-abc123",
  "model_id": "gemma4-4b-gpu",
  "contributor_team": "team-placeholder",
  "request_id": "chatcmpl-a1b2c3d4",
  "timestamp": "2026-06-15T14:30:00+08:00",
  "backend": "igpu-rocm",
  "hardware": "AMD Ryzen AI 9 HX 370",
  "input_tokens": 42,
  "output_tokens": 128,
  "ttft_seconds": 1.87,
  "throughput_tps": 137.2,
  "error": null
}
```

#### 欄位說明

| 欄位 | 型別 | 監測用途 |
|------|------|---------|
| `license_id` | string | 關聯使用方帳戶，追蹤誰在用 |
| `model_id` | string | 關聯貢獻團隊，追蹤哪個模型被用 |
| `contributor_team` | string | 直接標記貢獻團隊（帳戶架構細化前暫以 placeholder 填入）|
| `request_id` | string | 防重複計量 |
| `input_tokens` / `output_tokens` | int | 用量計量基礎（可衍生獎酬或成本） |
| `ttft_seconds` / `throughput_tps` | float | 驗證模型實際效能是否符合 Model Card 聲明 |
| `error` | string \| null | 失敗請求不計入有效用量 |

#### 設計原則

- 遙測為**非同步**發送（`asyncio` background task），不阻塞推論回應
- 若 endpoint 不可達，寫入本地備援佇列（`logs/telemetry_queue.jsonl`），待連線恢復後補送
- `contributor_team` 欄位在帳戶架構確定後，由平台依 `model_id` 自動對應，無需上架方手動填寫

---

### 2.5 建立 Azure Container Registry（初次設定）

本節操作只需執行一次。`model-cards-registry` 已存在於資源群組 `ai-hub-webui` 時可跳過。

1. 在 Azure Portal 頂部搜尋列輸入 **Container registries**，確認 **`model-cards-registry`** 是否已存在於訂閱 **`eosl-r3-aihub`** 下。

2. 若尚未建立，在終端機執行：

   ```bash
   az login
   az account set --subscription eosl-r3-aihub

   az group create \
     --name ai-hub-webui \
     --location eastasia

   az acr create \
     --resource-group ai-hub-webui \
     --name model-cards-registry \
     --sku Standard \
     --admin-enabled false
   ```

   > **為什麼 `--admin-enabled false`？** Admin 帳號使用靜態密碼，無法輪替。本規章改用 Service Principal，能夠定期換證並精確限制權限。

3. 建立完成後，記錄以下資訊（後續步驟使用）：

   ```bash
   az acr show \
     --name model-cards-registry \
     --query "{loginServer:loginServer, id:id}" \
     --output table
   ```

---

### 2.6 建立 Edge 裝置拉取用 Service Principal（初次設定）

Edge 裝置拉取 Image 使用獨立 Service Principal，賦予最小權限（僅 `acrpull`）。

1. 取得 ACR 的 Resource ID：

   ```bash
   ACR_ID=$(az acr show \
     --name model-cards-registry \
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
   | **ACR_NAME** | `model-cards-registry` |

---

### 2.8 建置並推送 Image（每次發布）

每次推送 Git tag（格式 `v*.*.*`）時，GitHub Actions 自動執行建置與推送。  
手動執行時，步驟如下：

1. 登入 ACR：

   ```bash
   az login
   az acr login --name model-cards-registry
   ```

2. 建置並標記 Image：

   ```bash
   VERSION="1.2.0"   # 對應 Git tag v1.2.0

   docker build \
     -t model-cards-registry.azurecr.io/ryzenai-benchmark:${VERSION}-rocm \
     .
   ```

3. 推送至 ACR：

   ```bash
   docker push model-cards-registry.azurecr.io/ryzenai-benchmark:${VERSION}-rocm
   ```

4. 確認 Image 與 Model Card Labels 已上傳：

   ```bash
   az acr manifest show \
     --registry model-cards-registry \
     --name ryzenai-benchmark:${VERSION}-rocm \
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
SECRET_NAME="model-cards-registry-pull-password"

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

下游 Edge 裝置收到 License File 後，使用以下 `docker-compose.yml` 啟動服務：

```yaml
# docker-compose.yml（供 Edge 設備下游使用）
services:
  ryzenai-benchmark:
    image: model-cards-registry.azurecr.io/ryzenai-benchmark:1.2.0-rocm
    restart: unless-stopped
    environment:
      MODEL_ID: gemma4-4b-gpu
      LICENSE_PATH: /app/license/license.json
      TELEMETRY_ENDPOINT: https://billing.ai-hub.example.com/v1/usage
    ports:
      - "8000:8000"
    volumes:
      - ./weights:/app/weights:ro       # 本地 weights（唯讀）
      - ./license:/app/license:ro       # License File（唯讀）
      - ./logs:/app/logs                # 本地遙測備援佇列
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

### 3.2 暫行方案（License File 等效控制）

在 Docker 容器化可行前，NPU 路線採用以下替代授權機制：

| Layer 2 功能 | NPU 暫行替代方案 |
|-------------|----------------|
| ACR Image 存取控制 | Azure Blob Storage SAS Token（30 天有效期） |
| License File 驗證 | 相同格式，由 `entrypoint.py` 在 Conda 環境中執行驗證 |
| 計費遙測 | 相同 HTTP callback 規格，由 `api.py` 直接呼叫 |
| 金鑰輪替 | SAS Token 自動過期 + 通知客戶重新取得 |

---

## 附錄 A：驗收清單（Acceptance Checklist）

每次發布前，由負責人對照以下清單確認：

### Layer 1（所有專案必查）
- [ ] `CHANGELOG.md` 已更新本版本條目
- [ ] Git tag 格式符合 `v<major>.<minor>.<patch>`
- [ ] Dockerfile 已嵌入所有必要 Model Card Labels
- [ ] `ai.benchmark.license-required` 與 `ai.benchmark.telemetry-endpoint` 已正確設定

### Layer 2（Linux iGPU 容器化）
- [ ] `Dockerfile` 採多階段建置
- [ ] `entrypoint.sh` 在 License File 缺失或過期時正確終止（exit code 1）
- [ ] License File 驗證涵蓋：簽章、到期日、model 許可清單
- [ ] 計費遙測在測試環境中成功送達指定 endpoint，response 200
- [ ] 計費遙測在 endpoint 不可達時正確寫入 `logs/telemetry_queue.jsonl`
- [ ] ACR 映像標籤含版本號與 backend 標識（例：`1.2.0-rocm`）
- [ ] Service Principal `sp-model-cards-edge-pull` 僅持有 `acrpull` 權限
- [ ] `release.yml` 成功在 CI 執行並推送至 `model-cards-registry`
- [ ] Edge 裝置以 `docker-compose.yml` 啟動並驗證 `http://localhost:8000/v1/models` 正常回應

### Layer 3（Windows NPU）
- [ ] 已完成 PoC 評估報告並存入 `docs/`
- [ ] 暫行方案（Conda + SAS Token）已在目標裝置驗證

---

## 附錄 B：套用至其他 Benchmark 專案的客製化指引

本規章設計為**框架無關（Framework-agnostic）**。套用至其他專案時需調整：

| 需客製化的項目 | 本規章預設值 | 其他專案替換說明 |
|--------------|------------|----------------|
| ACR Image 命名前綴 | `ryzenai-benchmark` | 替換為對應專案名稱 |
| `TELEMETRY_ENDPOINT` | `https://billing.ai-hub.example.com/v1/usage` | 替換為對應平台的計費 endpoint |
| Dockerfile `LABEL` 區塊 | `gemma4-4b-gpu` 相關資訊 | 替換為對應模型的 Model Card 資訊 |
| `entrypoint.sh` 的 weights 路徑邏輯 | `/app/weights` | 依各專案 weights 目錄結構調整 |
| `docker-compose.yml` 的 `devices` 區塊 | AMD ROCm（`/dev/kfd`, `/dev/dri`） | 依硬體替換（見下表） |

> 訂閱 `eosl-r3-aihub`、資源群組 `ai-hub-webui`、ACR `model-cards-registry` 為本平台固定資源，**所有 benchmark 專案共用**，不需替換。

### 各加速器 Docker device 直通參數

| 加速器 | Vendor | `docker-compose.yml` 設定 |
|--------|--------|--------------------------|
| NVIDIA GPU | NVIDIA | `runtime: nvidia` + `NVIDIA_VISIBLE_DEVICES=all` |
| AMD iGPU (ROCm) | AMD | `devices: [/dev/kfd, /dev/dri]` |
| AMD NPU (XDNA) | AMD | 尚在評估（參閱 Layer 3） |
| Intel GPU (OpenVINO) | Intel | `devices: [/dev/dri]` |
| Qualcomm QNN | Qualcomm | 依各 SDK 文件指定裝置節點 |
