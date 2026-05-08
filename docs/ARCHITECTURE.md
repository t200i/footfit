# Repository Architecture Design Pattern

要設計一個符合領域驅動設計 (DDD) 且能整合 Ryzen AI APU 軟體堆疊（PyTorch-ROCm 與 ONNX Runtime）的專案程式庫，核心關鍵在於將「推論邏輯」（策略）與「硬體實現」（機制）完全分離。以下是針對本專案輸入與輸出邊界設計的 DDD 開發流程與架構規範：

### 1. 設計策略

本專案的限界 (Bounded Context)為「AI 上下文推論服務」。開發者需按照與硬體專家（NPU/GPU）共同的詞彙來命名變數。
  - **Model（模型）**：來是HuggingFace原生transformers 提供的PyTorch模型及amd npu collection提供的onnx模型 
  - **Backend（硬體供應者）**：Ryzen AI APU內搭載GPU及NPU，GPU需要通過PyTorch ROCm Conda虛擬環境 offload模型，NPU需要通過Ryzen AI 1.7.1 Conda虛擬環境 offload模型 (這兩整生態系對模型推論的方法沒有一致的標準，需給一個類似nn.Module這樣的繼承類來將不統一的過程變成統一的過程，以此最小化開發負擔、最大化相容性)
  - **Task（推論任務）**：原則上提供一次性與互動式兩種推論的模式。前者主要用於測試，後者則是用於實際應用與demo。

### 1. 技術架構

技術採用整潔架構 (Clean Architecture) 分層，程式庫將分為以下四層，並嚴格遵守相依性規則 (Dependency Rule)：相依性只能指向內圓（核心）。

#### 領域層 (Domain Layer)：

這是程式庫的最中心，包含與技術無關的業務規則。
  - **領域模型 (Entities/Value Objects)**：定義 Model（統一模型類型的實體。e.x, LLM - Text2Text； VLM - ImageText2Text）、Backend（統一模型呼叫軟體堆疊的介面。NPU - onnxruntime with ryzen ai software； GPU - pytorch with rocm）。
  - **領域服務 (Domain Services)**：定義Model類的推論抽象邏輯，例如：相容性託管與檢查、自動後端服務(如pytorch gpu availible就自動調用, 或onnx看有沒有vitis ep，也另外提供device='<使用者指定>'的管道。)。
  - **儲存庫接口 (Repository Interface)**：使用者可以透過Python Class定義模型(如：Gemma3, 繼承ImageText2Text)，將從huggingface下載的native or amd collected模型定義成本專案可使用的模型實例。

#### 應用層 (Application Layer)：

負責協調任務，實現基本功能需求。
- 推論案例 (Use Cases)：
  - OneShotInference（一次性回覆）：一次性推論，適合測試或單次回覆。
  - InteractiveSession（互動式對話）：互動式推論，維持上下文，適合 demo 或應用。

#### 基礎架構層 (Infrastructure Layer)：

處理所有硬體與 SDK 的技術細節，將 PyTorch 與 ONNX Runtime 的差異標準化，並提供統一的推論引擎介面。
- 推論引擎 (Inference Backends)：
  - 提供抽象類別 `InferenceEngine`，定義統一的 `run(model: Model, *args, **kwargs)` 方法，保持所有Backend方法一致。
    - PyTorchROCmBackend (GPU)：繼承 InferenceEngine，封裝 PyTorch + ROCm Conda 環境，負責執行綁定 GPU 的模型。
    - OnnxVitisAIBackend (NPU)：繼承 InferenceEngine，封裝 ONNX Runtime + Ryzen AI/Vitis AI EP，負責執行綁定 NPU 的模型。
    - - OnnxDirectMLBackend (GPU)：繼承 InferenceEngine，封裝 ONNX Runtime + Ryzen AI/DirectML EP，負責執行綁定 GPU 的模型。
    - 範例：
      ```python
      class Gemma3(Text2Text):
        backend = PyTorchROCmBackend()
      ```
      ```python
      class CustomVLM(ImageText2Text):
        backend = OnnxVitisAIBackend()
      ```

#### 表現層 (Presentation Layer)：

CLI 模組 (Command Line Interface)
- CLI 模組：提供一次性回覆與互動式推論的命令列工具。
  ```
  cli.py --task oneshot --model <offloaded-gemma3-implementation>
  cli.py --task interactive --model <offloaded-customvlm-implementation>
  ```
- API 服務：將推論功能暴露為 REST API，支援 JSON 請求與回應，且可部署於 Docker 容器。
- WebUI Demo：整合 Open WebUI 作為前端展示介面，提供指定Model+Backend推論的圖形化操作Demo。



