# Repository Architecture Design Pattern

本專案程式庫旨在設計一套符合領域驅動設計 (DDD) 原則、並整合 Ryzen AI APU 軟體堆疊（PyTorch-ROCm 與 ONNX Ryzen AI Software）的推論框架。核心設計策略為將指定的「Model」（模型權重）與「Backend」（運算後端）進行靜態綁定，形成獨立且不可替換的推論部署單元——每一個部署單元僅對應一組固定的模型與後端組合，不支援執行期間的動態替換。以下為本專案輸入與輸出邊界設計的 DDD 開發流程與架構規範。

### 1. 設計目標及策略

  - **Model（模型）**：模型來源為 HuggingFace 原生 transformers 提供的 PyTorch 模型，以及 AMD NPU Collection 提供的 ONNX 模型。
  - **Backend（硬體後端）**：Ryzen AI APU 內建 GPU 與 NPU 兩種運算單元，分別對應不同的 Conda 執行環境。由於兩套生態系對模型推論的介面規範不一致，本專案透過定義統一的抽象繼承類別（類比於 PyTorch 的 `nn.Module`），將異質推論流程標準化為一致的呼叫介面，以降低開發耦合度並最大化跨後端相容性。
    - **`ryzen-ai-1.7.1`**：NPU 推論環境，透過 ONNX Runtime 搭配 Ryzen AI Execution Provider 執行 NPU 模型推論；亦支援 DirectML Execution Provider 進行 GPU 推論。
    - **`rocm-pytorch`**：GPU 推論環境，透過 PyTorch ROCm 原生 GPU 支援執行模型推論。
  - **Task（推論任務）**：推論任務區分為兩種模式：**一次性推論（One-Shot）** 適用於測試與單次查詢；**互動式推論（Interactive）** 維持會話上下文，適用於應用整合與展示情境。

### 2. 技術架構

技術採用整潔架構 (Clean Architecture) 分層，程式庫將分為以下四層，並嚴格遵守相依性規則 (Dependency Rule)：相依性只能指向內圓（核心）。

#### 領域層 (Domain Layer)：

本案的領域層設計，限界為「AI 上下文推論服務」，直接以模型與硬體後端的綁定為核心，並以上下文推論的需求來規劃各個元素。

  - Model(Entities)：代表可被呼叫的模型實體，定義模型類型並固定綁定其 Backend。
    - **LLM — Text2Text**：大型語言模型，純文字輸入/輸出。
    - **VLM — ImageText2Text**：視覺語言模型，影像 + 文字輸入 → 文字輸出。

  - Backend(Entities)：代表硬體/軟體堆疊的描述性實體，提供 Infrastructure 所需的識別與能力描述。
    - **NPU — ONNXVitisAIBackend**：`onnxruntime + ryzenai EP`，部署需求：`conda activate ryzen-ai-1.7.1`。
    - **GPU — ONNXDirectMLBackend**：`onnxruntime + DirectML`，部署需求：conda activate ryzen-ai-1.7.1`。
    - **GPU — PyTorchROCmBackend**：`pytorch + rocm`，部署需求：`conda activate rocm-pytorch`。
  
  - Conversation(Value Objects)：推論會話上下文。
    - **Message**：單一訊息項目，結構為 `Message(role, content, timestamp)`，其中 role 可為 user/system/assistant，content 為文字或資源，timestamp 為 ISO8601 格式。
    - **Context**：會話上下文，結構為 `ConversationContext(messages, metadata)`，其中 messages 為 `List[Message]`，metadata 為附加描述（例如 session_id、language、client_info）。

#### 基礎架構層 (Infrastructure Layer)：

處理所有硬體與 SDK 的技術細節，將 PyTorch 與 ONNX Runtime 的差異封裝於各自的計算實體內，並透過統一的抽象介面向上層提供一致的推論呼叫方式。

- 計算實體 (Compute Instance)：
  - **transformers**：透過 HuggingFace transformers 的 PyTorch ROCm GPU 支援實作 `generate()`。
  - **onnxruntime_genai**：透過 onnxruntime-genai 的 Vitis AI EP 或 DirectML EP 實作 `generate()`。
    - 範例：
      ```python
      class CustomVLM(ImageText2Text):
          def __init__(self):
              super().__init__(OnnxVitisAIBackend())
              # 於此初始化 onnxruntime_genai model 與 processor

          def generate(self, context: ConversationContext) -> Generator[str, None, None]:
              # 實作 onnxruntime_genai 推論邏輯，以 yield 逐步產出 token
              ...
      ```

#### 應用層 (Application Layer)：

負責協調任務，實現基本功能需求。
- 推論案例 (Use Cases)：
  - **OneShotInference（一次性回覆）**：一次性推論，適合測試或單次回覆。
  - **InteractiveSession（互動式對話）**：互動式推論，維持上下文，適合 demo 或應用。
  
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
