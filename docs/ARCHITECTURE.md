# Repository Architecture Design Pattern

要設計一個符合領域驅動設計 (DDD) 且能整合 Ryzen AI APU 軟體堆疊（PyTorch-ROCm 與 ONNX Runtime）的專案程式庫，核心關鍵在於將「推論邏輯」（策略）與「硬體實現」（機制）完全分離。以下是針對本專案輸入與輸出邊界設計的 DDD 開發流程與架構規範：

### 1. 設計策略

本專案的限界(Bounded Context) 為「AI 上下文推論服務」。開發者需按照與硬體專家（NPU/GPU）共同的詞彙來命名變數。

  - **Model（模型）**：來是HuggingFace原生transformers 提供的PyTorch模型及amd npu collection提供的onnx模型 
  - **Backend（硬體供應者）**：Ryzen AI APU內搭載GPU及NPU，GPU需要通過PyTorch ROCm Conda虛擬環境 offload模型，NPU需要通過Ryzen AI 1.7.1 Conda虛擬環境 offload模型 (這兩整生態系對模型推論的方法沒有一致的標準，需給一個類似nn.Module這樣的繼承類來將不統一的過程變成統一的過程，以此最小化開發負擔、最大化相容性)
  - **Task（推論任務）**：原則上提供一次性與互動式兩種推論的模式。前者主要用於測試，後者則是用於實際應用與demo。

### 2. 技術架構

技術採用整潔架構 (Clean Architecture) 分層，程式庫將分為以下四層，並嚴格遵守相依性規則 (Dependency Rule)：相依性只能指向內圓（核心）。

#### 領域層 (Domain Layer)：

本案的領域層設計，限界為「AI 上下文推論服務」，直接以模型與硬體後端的綁定為核心，並以上下文推論的需求來規劃各個元素。

  - Model(Entities)：代表可被呼叫的模型實體，定義模型類型並固定綁定其 Backend。
    - **LLM — Text2Text**：大型語言模型，純文字輸入/輸出。
    - **VLM — ImageText2Text**：大型語言模型，純文字輸入/輸出。文字）。

  - Backend(Entities)：：代表硬體/軟體堆疊的描述性實體，提供 Infrastructure 所需的識別與能力描述。
    - **NPU — ONNXVitisAIBackend(Backend Entities)**：`onnxruntime + ryzenai EP`，部署需求：`conda activate ryzen-ai-1.7.1`。
    - **GPU — ONNXDirectMLBackend(Backend Entities)**：`onnxruntime + DirectML`，部署需求：conda activate ryzen-ai-1.7.1`。
    - **GPU — PyTorchROCmBackend(Backend Entities)**：`pytorch + rocm`，部署需求：`conda activate rocm-pytorch`。
  
  - Conversation(Value Objects)：推論會話上下文。
    - Message：單一訊息項目，結構為 `Message(role, content, timestamp)`，其中 role 可為 user/system/assistant，content 為文字或資源，timestamp 為 ISO8601 格式。
    - Context(Value Objects)：會話上下文，結構為 `ConversationContext(messages, metadata)`，其中 messages 為 `List[Message]`，metadata 為附加描述（例如 session_id、language、client_info）。
    
  - InferenceSession(Aggregates)：聚合 Model、Backend、ConversationContext，代表一次完整的推論會話，確保模型與後端的綁定在上下文中保持一致。
  - ModelDefinition(Aggregates)：聚合 Model 與 Backend，確保模型在定義時即固定綁定其後端，避免執行階段的自動切換。
  - ChatOrchestrationService(Domain Services)：定義與推論相關的業務規則與抽象。
  - ModelRepository(Repository Interfaces)：提供模型的 CRUD 與查詢契約。
  - BackendRepository(Repository Interfaces)：提供後端的 CRUD 與查詢契約。

  

      
  - **領域服務 (Domain Services)**：定義Model類的推論抽象邏輯，例如：相容性託管與檢查、自動後端服務(如pytorch gpu availible就自動調用, 或onnx看有沒有vitis ep，也另外提供device='<使用者指定>'的管道。)。
  - **儲存庫接口 (Repository Interface)**：使用者可以透過Python Class定義模型(如：Gemma3, 繼承ImageText2Text)，將從huggingface下載的native or amd collected模型定義成本專案可使用的模型實例。

#### 應用層 (Application Layer)：

負責協調任務，實現基本功能需求。
- 推論案例 (Use Cases)：
  - **OneShotInference（一次性回覆）**：一次性推論，適合測試或單次回覆。
  - **InteractiveSession（互動式對話）**：互動式推論，維持上下文，適合 demo 或應用。

#### 基礎架構層 (Infrastructure Layer)：

處理所有硬體與 SDK 的技術細節，將 PyTorch 與 ONNX Runtime 的差異標準化，並提供統一的推論引擎介面。
- 推論引擎 (Inference Backends)：
  - 提供抽象類別 `InferenceEngine`，定義統一的 `run(model: Model, *args, **kwargs)` 方法，保持所有Backend方法一致。
    - **PyTorchROCmBackend (GPU)**：繼承 InferenceEngine，封裝 PyTorch + ROCm Conda 環境，負責執行綁定 GPU 的模型。
    - **OnnxVitisAIBackend (NPU)**：繼承 InferenceEngine，封裝 ONNX Runtime + Ryzen AI/Vitis AI EP，負責執行綁定 NPU 的模型。
    - **OnnxDirectMLBackend (GPU)**：繼承 InferenceEngine，封裝 ONNX Runtime + Ryzen AI/DirectML EP，負責執行綁定 GPU 的模型。
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

定義 Input/Output 邊界所在地，負責與使用者或外部系統互動。
- CLI 模組：提供一次性回覆與互動式推論的命令列工具。
  ```
  cli.py --task oneshot --model gemma3
  cli.py --task interactive --model customvlm
  ```
- API 服務：將推論功能暴露為 REST API，支援 JSON 請求與回應，且可部署於 Docker 容器。API 規格完全遵循 OpenAI API 規格，支援 /v1/chat/completions 端點，一律投入完整上下文，並透過 `stream=True` 或 `stream=False` 控制回應模式。
```http
POST /v1/chat/completions
{
  "model": "gemma3",
  "messages": [
    {"role": "user", "content": "解釋量子計算"}
  ],
  "stream": true
}
```
```json
#stream=False → 一次性回傳完整結果
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "量子計算是一種基於量子力學的計算方式..."},
      "finish_reason": "stop"
    }
  ]
}
```
```json
# stream=True → 逐步回傳事件流 (Server-Sent Events)，每個 chunk 包含 delta
{
  "id": "chatcmpl-123",
  "object": "chat.completion.chunk",
  "choices": [
    {
      "delta": {"content": "量子"},
      "index": 0,
      "finish_reason": null
    }
  ]
}
```
- Python SDK 整合：提供 Python SDK，直接整合 OpenAI Python SDK 的呼叫方式。
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")

# 非串流模式
response = client.chat.completions.create(
    model="gemma3",
    messages=[{"role": "user", "content": "解釋量子計算"}],
    stream=False,
)
print(response.choices[0].message.content)

# 串流模式
for chunk in client.chat.completions.create(
    model="gemma3",
    messages=[{"role": "user", "content": "解釋量子計算"}],
    stream=True,
):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```
- WebUI Demo：整合 Open WebUI 作為前端展示介面，提供指定Model+Backend推論的圖形化操作Demo，WebUI 會透過 `/v1/chat/completions` 呼叫 API。。



