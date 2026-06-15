# ITRI AI Hub — 容器授權交握協定

本文件說明 ITRI AI Hub 與 Docker Model Image 之間的三段式交握機制（Three-Phase Handshake）。  
此機制在保持 **`docker pull` + `docker run` 簡單 UX** 的前提下，將 License Key 綁定至唯一設備指紋，任何指紋不符的執行請求均被拒絕。

完成首次啟用約需 **30 秒**（自動在背景執行，不影響推論服務啟動）。

---

## 使用者體驗（User-Facing UX）

Licensee 只需做兩件事：

```bash
# 步驟一：設定 License Key（一次性，建議寫入 ~/.bashrc 或 ~/.zshrc）
export AIHUB_LICENSE_KEY=lic-xxxxxxxxxxxxxxxx

# 步驟二：拉取並執行
docker pull model-cards-registry.azurecr.io/ryzenai/gemma4-4b-gpu:latest
docker run --rm -p 8000:8000 \
  -e AIHUB_LICENSE_KEY \
  -v aihub-telemetry:/app/logs \
  model-cards-registry.azurecr.io/ryzenai/gemma4-4b-gpu:latest
```

> **`-v aihub-telemetry:/app/logs` 是必要參數。**  
> `aihub-telemetry` 是 Docker Named Volume，由 Docker daemon 管理，`--rm` 不會刪除它。  
> 此 volume 用於在網路中斷期間暫存用量紀錄，容器重啟後自動補送。

啟動後，服務即可接受 OpenAI 相容 API 請求：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma4-4b-gpu","messages":[{"role":"user","content":"你好"}]}'
```

所有授權驗證、設備綁定、用量回報均在容器內部自動處理，**使用者不需要了解交握細節**。

---

## 設計目標

| 目標 | 機制 |
|------|------|
| 簡單 UX | 一個環境變數 `AIHUB_LICENSE_KEY` + 一個 Named Volume |
| 一 Key 一設備 | License Key 於首次啟用時綁定設備指紋（CPU_ID + MAC + hostname），指紋不符一律拒絕 |
| 離線容錯 | Docker Named Volume 暫存用量，`--rm` 不會刪除；重連後自動補送 |
| 離線緩衝防竄改 | 每筆紀錄附 HMAC 簽章 + 單調遞增序列號；Hub 偵測序列缺口時停止服務 |
| 用量追蹤 | Heartbeat 定期回報，供 Principal 核算貢獻獎酬 |

---

## 三段式交握流程

### Phase 0 — 環境準備（使用者側，一次性）

```
使用者設定環境變數
    └── export AIHUB_LICENSE_KEY=lic-xxxxxxxxxxxxxxxx
         └── docker run -e AIHUB_LICENSE_KEY ...
              └── 容器從環境變數讀取 Key，進入 Phase 1
```

---

### Phase 1 — 啟動啟用（Activation Handshake）

> **觸發時機**：容器每次啟動時執行一次

```mermaid
sequenceDiagram
    participant E as 容器<br/>entrypoint.sh
    participant H as AI Hub<br/>activation.ai-hub.itri.org.tw

    Note over E: 1. 計算設備指紋<br/>SHA256(CPU_ID + MAC + hostname)

    E->>H: 2. POST /v1/activate<br/>{ license_key, device_fingerprint,<br/>  model_id, container_image }

    Note over H: 驗證 license_key 有效性<br/>比對綁定的 device_fingerprint<br/>（首次啟用則寫入綁定；<br/> 後續啟用需完全吻合）

    alt 啟用成功（fingerprint 吻合或首次綁定）
        H-->>E: 3. 200 OK<br/>{ session_token (記憶體暫存),<br/>  quota_tokens_remaining,<br/>  heartbeat_interval_seconds: 300,<br/>  grace_period_seconds: 1800,<br/>  expires_at }
        Note over E: 4. 啟動推論服務（api.py）
    else 啟用失敗
        H-->>E: 4xx { error, message }
        Note over E: 印出錯誤訊息，exit 1
    end
```

**啟用失敗的情況：**

| 錯誤碼 | 原因 | 容器行為 |
|--------|------|---------|
| `LICENSE_INVALID` | Key 不存在或已撤銷 | 印出錯誤訊息，exit 1 |
| `LICENSE_EXPIRED` | Key 已過期 | 印出到期日，exit 1 |
| `DEVICE_MISMATCH` | 設備指紋與綁定紀錄不符（Key 已綁定至另一台設備） | 印出錯誤訊息，提示聯絡 AI Hub 解綁，exit 1 |
| `MODEL_NOT_PERMITTED` | 此 Key 不允許執行此模型 | 列出許可的模型清單，exit 1 |

---

### Phase 2 — 定期心跳（Heartbeat）

> **觸發時機**：推論服務啟動後，每 `heartbeat_interval_seconds`（預設 5 分鐘）執行一次

```mermaid
sequenceDiagram
    participant E as 容器<br/>背景 async task
    participant H as AI Hub

    loop 每 heartbeat_interval_seconds（預設 300s）
        E->>H: POST /v1/heartbeat<br/>{ session_token, device_fingerprint,<br/>  seq_no, usage: { input_tokens, output_tokens, request_count } }
        Note over H: 驗證 session_token<br/>確認 device_fingerprint 未變動<br/>比對伺服器端帳本的 last_confirmed_seq_no<br/>累計用量，更新帳本與配額餘量
        H-->>E: { continue: true,<br/>  quota_tokens_remaining,<br/>  last_confirmed_seq_no,<br/>  next_heartbeat_seconds }
    end
```

**心跳中斷的處理（預授權離線額度機制）：**

> **設計原則**：Hub 是唯一帳本。離線期間，容器只能消耗「已預先授權的離線額度」，不依賴本地記錄的用量準確性。

每次心跳回應中，Hub 同時下發下一個心跳週期的**預授權離線額度（Offline Budget）**：

```mermaid
sequenceDiagram
    participant E as 容器
    participant H as AI Hub

    E->>H: POST /v1/heartbeat<br/>{ session_token, seq_no,<br/>  usage_this_period: { input, output } }
    Note over H: 扣除本期用量<br/>更新伺服器端帳本<br/>核算下一期離線額度
    H-->>E: { continue: true,<br/>  quota_remaining,<br/>  offline_budget_tokens: 10000,<br/>  offline_budget_expires_in: 1800 }
    Note over E: 將 offline_budget 存入記憶體
```

```mermaid
flowchart TD
    A([Hub 不可達]) --> B["使用記憶體中的 offline_budget_tokens"]
    B --> C{offline_budget_tokens > 0\n且尚未到期?}
    C -- 是 --> D[允許推論\n每次扣減消耗量]
    C -- 否 --> E([停止服務 HTTP 503\n等待重連或預算補發])
    D --> F{每 60 秒重試連線}
    F -- 連線恢復 --> G["送出本期實際用量\nHub 扣帳 + 補發新 offline_budget\n恢復正常 Heartbeat 週期"]
    F -- 仍離線 --> C
```

**為什麼這樣設計是安全的：**

| 攻擊情境 | 系統回應 |
|---------|---------|
| 使用者刪除 Named Volume | 記憶體中的 offline_budget 本就不在 Volume，不受影響；Hub 帳本不變 |
| 使用者修改 Volume 中的暫存紀錄 | Hub 只看自己下發的 offline_budget 上界，不信任客戶端回報的數字是「節省」了多少 |
| 使用者讓容器永遠離線不重連 | offline_budget 有到期時間（`offline_budget_expires_in`），到期後停服 |
| 使用者重啟容器嘗試重置 offline_budget | 重啟後必須重走 Phase 1 Activation；Hub 帳本知道上次下發的 budget，不會重複授予 |

**Named Volume 在此設計中的角色縮減為：**
- 暫存「本期已消耗用量」，在重連後誠實回報給 Hub
- 即使全部刪除，Hub 只會以「offline_budget 全數消耗完」來計帳（最保守估算）
- 使用者無法靠刪除 Volume 來獲利

---

### Phase 3 — 逐請求配額防護（Per-Request Guard）

> **觸發時機**：每次推論請求進入 `api.py` 時，在模型推論前檢查

```mermaid
flowchart TD
    A([推論請求進入]) --> B{quota_tokens_remaining > 0?}
    B -- 是 --> C[執行模型推論]
    C --> D[扣減消耗的 token 數]
    D --> E([回傳推論結果])
    B -- 否 --> F([HTTP 429\nerror: quota_exceeded\ncontact: ai-hub@itri.org.tw])
```

---

## 設備指紋（Device Fingerprint）計算方式

設備指紋由容器內部計算，不需要使用者操作：

```python
import hashlib, platform, uuid

def compute_device_fingerprint() -> str:
    """
    組合多個硬體識別碼，對 MAC 位址異動（如 VPN、容器網路重建）有一定容忍度。
    最終結果為 SHA256 hex digest（64 字元）。
    """
    components = []

    # CPU 序號（Linux: /proc/cpuinfo，Windows: wmic）
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "Serial" in line or "Hardware" in line:
                    components.append(line.strip())
    except Exception:
        pass

    # 主機名稱（穩定識別符）
    components.append(platform.node())

    # 第一個非 loopback MAC（轉換為字串避免每次啟動漂移）
    mac = uuid.getnode()
    if mac != uuid.getnode():  # 若每次不同（虛擬 MAC）則略過
        pass
    else:
        components.append(str(mac))

    raw = "|".join(components)
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
```

> **隱私說明**：設備指紋僅儲存其雜湊值，不包含可識別個人身份的資訊。AI Hub 收到的是不可逆的 SHA256 摘要。

---

## 防複製機制說明

下圖說明當使用者嘗試將同一個 License Key 複製到未授權設備時，系統如何回應：

```mermaid
sequenceDiagram
    participant A as 設備 A（已綁定）
    participant H as AI Hub
    participant B as 設備 B（嘗試啟用）

    Note over A,H: License Key 已於設備 A 首次啟用時綁定其指紋

    A->>H: Heartbeat（正常運作中）
    H-->>A: continue: true

    B->>H: POST /v1/activate<br/>{ license_key: 同一個 Key,<br/>  device_fingerprint: 不同 }

    Note over H: 比對 fingerprint<br/>與綁定紀錄不吻合

    H-->>B: 403 DEVICE_MISMATCH<br/>{ message: "此 Key 已綁定至另一台設備" }

    Note over B: 容器 exit 1<br/>此 License Key 已綁定至另一台設備。<br/>如需更換設備，請聯絡 AI Hub 解除綁定。
```

**若使用者需要合法更換設備：**

1. 聯絡 AI Hub（ai-hub@itri.org.tw）申請解除原設備綁定
2. 平台確認後清除該 License Key 的 fingerprint 紀錄
3. 在新設備重新執行 `docker run`，首次啟用自動完成新設備綁定

---

## AI Hub 平台側 API 規格（Platform Reference）

以下為 AI Hub 需實作的端點規格，供平台開發團隊參考。

### `POST /v1/activate`

**Request:**
```json
{
  "license_key": "lic-xxxxxxxxxxxxxxxx",
  "device_fingerprint": "sha256:abcdef...",
  "model_id": "gemma4-4b-gpu",
  "container_image": "model-cards-registry.azurecr.io/ryzenai/gemma4-4b-gpu@sha256:def456"
}
```

**Response 200:**
```json
{
  "session_token": "st-yyyyyyyyyy",
  "quota_tokens_remaining": 500000,
  "heartbeat_interval_seconds": 300,
  "grace_period_seconds": 1800,
  "expires_at": "2026-07-15T00:00:00Z"
}
```

**Response 4xx:**
```json
{
  "error": "DEVICE_MISMATCH",
  "message": "此 License Key 已綁定至另一台設備。如需更換設備，請聯絡 AI Hub 解除綁定。"
}
```

---

### `POST /v1/heartbeat`

**Request:**
```json
{
  "session_token": "st-yyyyyyyyyy",
  "device_fingerprint": "sha256:abcdef...",
  "usage_since_last_heartbeat": {
    "input_tokens": 1240,
    "output_tokens": 3871,
    "request_count": 12
  }
}
```

**Response 200:**
```json
{
  "continue": true,
  "quota_tokens_remaining": 495000,
  "next_heartbeat_seconds": 300
}
```

**Response 401（session 被撤銷時）:**
```json
{
  "continue": false,
  "error": "SESSION_REVOKED",
  "message": "License Key 已被撤銷或設備授權已解除，請重新啟用或聯絡 AI Hub。"
}
```

---

## 附錄：容器側實作責任分工

| 元件 | 負責的交握行為 |
|------|--------------|
| `entrypoint.sh` | Phase 1 啟動啟用、啟用失敗時 exit 1 |
| `api.py`（背景 task） | Phase 2 定期 Heartbeat、離線暫存 |
| `api.py`（請求攔截）| Phase 3 逐請求配額防護（429 回應） |
| `ryzenai/modules/` | **不涉及任何交握邏輯**（由框架層統一處理） |
