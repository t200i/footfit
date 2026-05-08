# Repository Architecture Design Pattern

要設計一個符合領域驅動設計 (DDD) 且能整合 Ryzen AI APU 軟體堆疊（PyTorch-ROCm 與 ONNX Runtime）的專案程式庫，核心關鍵在於將「推論邏輯」（策略）與「硬體實現」（機制）完全分離。以下是針對本專案輸入與輸出邊界設計的 DDD 開發流程與架構規範：

### 1. 設計策略

本專案的限界 (Bounded Context)為「AI 上下文推論服務」。開發者需按照與硬體專家（NPU/GPU）共同的詞彙來命名變數。
  - Model（模型）：來是HuggingFace原生transformers 提供的PyTorch模型及amd npu collection提供的onnx模型 
  - Backend（硬體供應者）：Ryzen AI APU內搭載GPU及NPU，GPU需要通過PyTorch ROCm Conda虛擬環境 offload模型，NPU需要通過Ryzen AI 1.7.1 Conda虛擬環境 offload模型 (這兩整生態系對模型推論的方法沒有一致的標準，需給一個類似nn.Module這樣的繼承類來將不統一的過程變成統一的過程，以此最小化開發負擔、最大化相容性)
  - Task（推論任務）：原則上提供一次性與互動式兩種推論的模式。前者主要用於測試，後者則是用於實際應用與demo。

### 1. 技術架構

技術採用整潔架構 (Clean Architecture) 分層，程式庫將分為以下四層，並嚴格遵守相依性規則 (Dependency Rule)：相依性只能指向內圓（核心）。

#### 領域層 (Domain Layer)：

這是程式庫的最中心，包含與技術無關的業務規則。
  - 領域模型 (Entities/Value Objects)：定義 Model（統一模型類型的實體。e.x, LLM - Text2Text； VLM - ImageText2Text）、Hardware（統一模型呼叫軟體堆疊的介面。NPU - onnxruntime with ryzen ai software； GPU - pytorch with rocm），並透過繼承Model(Hardware)讓使用者自行定義從huggingface下載的native or amd collected模型。
  - 領域服務 (Domain Services)：定義推論的抽象邏輯，例如 InteractiveService 接口。
  - 儲存庫接口 (Repository Interface)：定義如何「取得」模型的接口（例如從 HF 或 AMD Collection 加載），但不涉及具體下載實作。

#### 應用層 (Application Layer)：

負責協調任務，實現你的功能需求（Use Cases）。
- 推論案例 (Use Cases)：例如 RunOneShotInference（一次性回覆）與 StartInteractiveSession（互動式對話）。
- 它會呼叫領域層的接口，但不關心底層是用 PyTorch 還是 ONNX Runtime。

#### 基礎架構層 (Infrastructure Layer)：

處理所有硬體與 SDK 的技術細節。這是你實現 Ryzen AI 堆疊的地方。
- 推論引擎實現：在此實作領域層定義的接口。例如 ROCmPyTorchEngine 用於 GPU 模型，ONNXRuntimeNPUEngine 用於 NPU 模型。
- 硬體抽象層 (HAL)：考慮到硬體（NPU/GPU）會隨驅動或軟體堆疊更新，應將硬體細節隱藏在 HAL 之後，讓上層軟體能保持穩定。
- OpenAI SDK 整合：在此實作 ACL，將 OpenAI Python SDK 的請求映射到你的應用層 Use Case。

#### 表現層 (Presentation Layer)：
這是你定義的 Input/Output 邊界所在地。
- CLI 模組：實作一次性回覆與互動式 CLI。
- API 服務：實作 Docker API 服務，將你的推論功能暴露為 REST 接口。
- WebUI Demo：整合 Open WebUI 作為前端呈現。

4. 符合 DDD 的開發流程建議
為了確保專案不淪為亂糟糟的「大泥球」(Big Ball of Mud)
，建議遵循以下流程：
定義核心領域：先寫領域層的 Python 抽象類（Abstract Base Classes），定義推論任務的 Input（Prompt, Config）與 Output（Tensor, String）
。
實作應用邏輯：編寫應用層 Use Case，例如「接收 CLI 輸入 -> 呼叫推論引擎 -> 返回結果」
。
插件式實作基礎設施 (Plugin Architecture)：將 PyTorch-ROCm 與 ONNX Runtime 視為核心層的「插件」
。這讓你未來若增加新的硬體支援（如未來的新 APU），不需修改核心推論邏輯
。
測試驅動 (Testability)：利用分層架構，你可以在沒有 NPU/GPU 實體硬體的情況下，使用 Mock 對應用層邏輯進行單元測試
。
總結架構圖思考
你的「邊界」設計可以看作是 六角形架構 (Hexagonal Architecture)：
中心：模型與推論領域邏輯。
左側 (輸入適配器)：CLI、OpenAI SDK 入口、Open WebUI
。
右側 (輸出適配器)：PyTorch-ROCm (GPU)、ONNX Runtime (NPU)、模型存儲
。
這種設計能確保你的庫既能支援 AMD 的特定硬體優化，又能彈性整合 HuggingFace 上的開源生態，且易於維護與擴展
。

以下是針對你的 Ryzen AI APU 堆疊（包含 ROCm GPU 與 ONNX NPU）以及 OpenAI SDK 整合所設計的目錄結構：
具體 Python 庫目錄結構
ryzen_ai_repo/
├── src/
│   └── ryzen_ai/
│       ├── domain/                # 核心層：業務邏輯與硬體抽象 [3]
│       │   ├── models/            # 領域模型 (Entities/Value Objects) [3]
│       │   │   ├── model_spec.py  # 模型規格 (例如：NPU 或 GPU)
│       │   │   └── inference.py   # 推論任務模型
│       │   ├── services/          # 領域服務介面 (Interfaces) [3]
│       │   │   └── engine_base.py # 定義推論引擎的抽象基類
│       │   └── repository/        # 儲存庫介面 [4]
│       │       └── model_repo.py  # 定義如何載入模型的介面
│       │
│       ├── application/           # 應用層：協調 Use Cases [5]
│       │   ├── use_cases/
│       │   │   ├── one_shot.py    # 一次性回覆任務
│       │   │   └── interactive.py # 互動式對話任務
│       │   └── dtos/              # 資料傳輸物件 [5]
│       │
│       ├── infrastructure/        # 基礎設施層：硬體實現與技術細節 [6]
│       │   ├── engines/           # Ryzen AI 堆疊實現
│       │   │   ├── rocm_pytorch.py# GPU 模型實作 (PyTorch-ROCm)
│       │   │   └── npu_onnx.py    # NPU 模型實作 (ONNX Runtime)
│       │   ├── adapters/          # 外部系統適配器 [7]
│       │   │   └── openai_acl.py  # OpenAI SDK 防腐層 (ACL) [7, 8]
│       │   └── loaders/           # 模型載入實作 (HF/AMD Collection)
│       │
│       └── presentation/          # 表現層：定義 I/O 邊界 [6]
│           ├── cli/               # CLI 模組 (支援互動式與一次性)
│           ├── api/               # Docker API 服務 (如 FastAPI)
│           └── webui/             # Open WebUI Demo 整合邏輯
│
├── tests/                         # 測試目錄，按層級劃分 [9, 10]
│   ├── unit/                      # 領域層與應用層單元測試 [11]
│   └── integration/               # 基礎設施層硬體測試 [11]
├── docker/                        # Docker 部署設定 [6]
│   └── Dockerfile
├── README.md                      # 包含 Ubiquitous Language 說明 [12]
└── pyproject.toml                 # 專案相依性管理
各層設計要點說明
領域層 (Domain Layer)：
這是程式庫的最核心，不應包含任何 PyTorch 或 ONNX 的程式碼
。
在 services/engine_base.py 中定義推論引擎的介面，確保上層邏輯不會與特定的硬體堆疊綁死
。
應用層 (Application Layer)：
負責協調任務。例如，當 CLI 請求一次性回覆時，應用層會調用領域層的介面，並由基礎設施層的特定實現（NPU 或 GPU）來執行
。
基礎設施層 (Infrastructure Layer)：
這是你實作 Ryzen AI 軟體堆疊 的地方
。
OpenAI SDK 整合：必須實作 防腐層 (ACL)，確保 OpenAI 的數據格式（如 JSON）在進入你的核心領域前，先轉換為內部的領域模型，避免外部 SDK 的變動感染整個專案
。
表現層 (Presentation Layer)：
根據你的需求，這裡包含 CLI 進入點、API 服務以及 WebUI 適配器
。
這層負責將使用者的輸入（如互動式 CLI 指令）格式化後傳遞給應用層
。


