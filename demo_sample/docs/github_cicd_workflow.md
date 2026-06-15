# GitHub CI/CD 工作流程說明

本文件說明 Agentic SDK 的自動化部署架構，包含初次設定步驟與工作流程結構。

完成初次設定約需 **15 分鐘**。

---

## 事前準備

開始之前，請確認：

- 您擁有一個 Azure 訂閱，且角色為 **Owner** 或 **Contributor**
- 您擁有該訂閱的 Azure Active Directory 存取權，可建立 **App Registration**
- 您擁有 GitHub 儲存庫 `R300-AI/Agentic-SDK` 的 **Admin** 權限（用於設定 Repository Variables）

> **本專案目前使用的訂閱為 `eosl-r3-aihub`。** 若您使用不同訂閱，後續步驟中所有涉及訂閱的選擇，請以您自己的訂閱取代。

---

## 概覽

每次推送至 **main** 分支，工作流程會執行單一部署 job：

```
推送至 main
    │
    ▼
[deploy]
    ├─ 以 OIDC 登入您指定的 Azure 訂閱
    ├─ 自動佈建所需 Azure 資源（冪等，已存在則略過）
    ├─ 建置 Vite 前端（npm run build → demo/dist/）
    ├─ 部署整包（Python 後端 + 前端靜態檔案）至 App Service
    └─ 設定 App Service 啟動指令與環境參數
```

前後端統一由同一個 App Service 對外服務，瀏覽位置即為
`https://{AZURE_WEBAPP_NAME}.azurewebsites.net`。

所有 Azure 資源（Resource Group、App Service Plan、App Service、Key Vault）
均由工作流程在首次執行時自動建立，無需手動操作。

---

## 第一節：設定 OIDC 身分驗證（初次設定）

GitHub Actions 透過 OIDC（OpenID Connect）向 Azure 驗證身分，無需儲存任何密碼。

### 步驟 1-1：建立 App Registration

1. 前往 [Azure Portal](https://portal.azure.com)，在頂部搜尋列輸入 **App registrations**，選取搜尋結果。

2. 選取 **+ New registration**，填入：

   - **Name**：`agentic-sdk-github-actions`
   - **Supported account types**：**Accounts in this organizational directory only**

3. 選取 **Register**。

4. 建立完成後，記錄以下兩個值：

   - **Application (client) ID**
   - **Directory (tenant) ID**

### 步驟 1-2：建立 Federated Credential

1. 在 App registration 頁面，選取左側 **Certificates & secrets**。

2. 選取 **Federated credentials** 分頁，再選取 **+ Add credential**。

3. 在 **Federated credential scenario** 下拉選單選取 **GitHub Actions deploying Azure resources**，填入：

   - **Organization**：`R300-AI`
   - **Repository**：`Agentic-SDK`
   - **Entity type**：**Branch**
   - **GitHub branch name**：`main`
   - **Name**：`agentic-sdk-main-branch`

4. 選取 **Add**。

### 步驟 1-3：授予訂閱層級的 Contributor 角色

工作流程需要在訂閱層級建立 Resource Group 與其他資源，因此授予範圍設定在訂閱層級。

1. 在 Azure Portal 頂部搜尋列輸入 **Subscriptions**，選取您使用的訂閱。

2. 記錄 **Subscription ID**（GUID 格式）。

3. 選取左側 **Access control (IAM)**，再選取 **+ Add** → **Add role assignment**。

4. 在 **Role** 分頁搜尋並選取 **Owner**，選取 **Next**。

5. 在 **Members** 分頁，**Assign access to** 選取 **User, group, or service principal**，選取 **+ Select members**，搜尋並選取 `agentic-sdk-github-actions`。

6. 選取 **Review + assign**，完成授權。

   > **為什麼需要 Owner？** 工作流程除了建立資源（Contributor），還需要對 Key Vault 指派 Managed Identity 讀取權限（`roleAssignments/write`），Owner 同時涵蓋這兩項能力。

---

## 第二節：設定 GitHub Repository Variables

所有部署參數統一存放於 GitHub Repository Variables，不寫入原始碼。

1. 前往 GitHub 儲存庫 `R300-AI/Agentic-SDK`，選取 **Settings**。

2. 在左側選取 **Secrets and variables** → **Actions**。

3. 選取 **Variables** 分頁，依序選取 **New repository variable**，新增以下七個變數：

   **OIDC 身分驗證（值來自第一節）：**

   | 變數名稱 | 值 |
   |---|---|
   | **AZURE_CLIENT_ID** | 步驟 1-1 取得的 Application (client) ID |
   | **AZURE_TENANT_ID** | 步驟 1-1 取得的 Directory (tenant) ID |
   | **AZURE_SUBSCRIPTION_ID** | 步驟 1-3 取得的 Subscription ID |

   **部署目標（依您的環境決定，本專案預設值如括號所示）：**

   | 變數名稱 | 說明 | 本專案預設值 |
   |---|---|---|
   | **AZURE_REGION** | 部署區域 | `southeastasia` |
   | **AZURE_RESOURCE_GROUP** | 資源群組名稱 | `agentic-sdk` |
   | **AZURE_WEBAPP_NAME** | App Service 名稱 | `agentic-sdk-playground` |
   | **KEY_VAULT_NAME** | Key Vault 名稱（模型端點儲存庫） | `agentic-sdk-models` |

4. 完成後，推送任何變更至 **main** 分支即可觸發工作流程，Azure 資源將自動建立。

---

## 附錄：工作流程階段說明

| 步驟 | 說明 |
|---|---|
| 佈建 Azure 資源 | 以 OIDC 登入、冪等建立 Resource Group / App Service Plan / App Service / Key Vault |
| 建置前端 | `npm ci` + `npm run build`，產生 `demo/dist/` |
| 部署 | 整包（Python + 靜態前端）部署至 App Service |
| 設定啟動參數 | 設定 startup-file、PORT、KEY_VAULT_NAME 等非敏感參數 |

> 敏感資料（模型 API key）不經過 CI/CD，App Service 在執行時透過 Managed Identity 從 Key Vault 讀取。詳見 [setup_default_models.md](setup_default_models.md)。

## 附錄：工作流程檔案對應

| 檔案 | 用途 |
|---|---|
| `.github/workflows/deploy-gateway.yml` | 主工作流程：佈建 + build 前端 + 部署 |
| `.github/workflows/ci.yml` | 每次 PR/push 執行 Python 測試與 TypeScript 型別檢查 |
