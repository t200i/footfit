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
    ```python
    # 以下為範例，實際實作依部署模型與所選 SDK 而定。
    class CustomVLM(ImageText2Text):
        def __init__(self):
            super().__init__(OnnxVitisAIBackend())
            # 於此初始化 onnxruntime_genai model 與 processor

        def generate(self, context: ConversationContext) -> Generator[str, None, None]:
            # 實作 onnxruntime_genai 推論邏輯，以 yield 逐步產出 token
            ...
    ```

#### 應用層 (Application Layer)：

負責協調推論任務的業務流程，管理 `ConversationContext` 的生命週期，並將 Infrastructure Layer 回傳的 token 串流傳遞至上層介面。

- 推論案例 (Use Cases)：
  - **OneShotInference（一次性推論）**：接收單次 user input，建立僅含該訊息的 `ConversationContext`，呼叫 `model(context)` 後將 token 串流回傳，不保留任何會話狀態。
  - **InteractiveSession（互動式對話）**：持有跨輪次的 `ConversationContext`，每輪推論前將 user message append 至 context，取得完整回覆後再將 assistant message append 回 context，以維護多輪對話歷史，並將每輪的 token 串流回傳。
  
#### 表現層 (Presentation Layer)：

本層對外的互動邊界設計核心在於生態系整合：REST API 規格完全遵循 OpenAI `/v1/chat/completions` 端點規範，使 OpenAI Python SDK 與 Open WebUI 等現有生態工具無需任何修改即可直接對接，以最小的介面實作覆蓋所有消費路徑。

所有介面均支援兩種回應模式：
- `stream=false`：彙整所有 token 為完整回覆後一次性回傳。
- `stream=true`：以 Server-Sent Events 逐步推送每個 token chunk。

- 消費路徑 (Consumer Paths)：
  - **CLI**：本專案唯一直接支援 `OneShotInference` 與 `InteractiveSession` 兩種推論模式的原生介面，適用於本地測試與開發驗證。以 `--task` 指定推論模式（預設 `oneshot`），以 `--stream` 控制輸出方式（預設 `false`）。
    ```
    cli.py --model gemma3                        # --task 預設為 oneshot，--stream 預設為 false
    cli.py --task interactive --model gemma3     # --stream 預設為 false
    cli.py --task interactive --model customvlm --stream true
    ```
    
  - **REST API**：將互動式推論能力暴露為可部署於 Docker 容器的 HTTP 服務，作為 OpenAI Python SDK 與 Open WebUI 的統一後端。規格遵循 OpenAI `/v1/chat/completions` 端點，由呼叫方負責傳入並維護完整的 `messages` 上下文。以下為請求與回應的完整欄位規範——所有欄位均為 OpenAI Python SDK 解析所必要，實作時不可省略。
  ```http
  POST /v1/chat/completions
  {
    "model": "gemma3",        // 必填，對應本專案部署的模型識別名稱
    "messages": [             // 必填，由呼叫方維護並傳入完整的多輪對話歷史
      {"role": "user", "content": "解釋量子計算"}
    ],
    "stream": true            // 選填，預設 false；控制回應模式
  }
  ```
  ```json
  // stream=false：一次性回傳完整回覆
  {
    "id": "chatcmpl-123",           // 本次請求的唯一識別碼
    "object": "chat.completion",    // 固定值，SDK 以此判斷物件型別
    "created": 1700000000,          // Unix timestamp，SDK 會存取此欄位
    "model": "gemma3",              // 回傳實際使用的模型名稱，SDK 會存取此欄位
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",      // 固定值
          "content": "量子計算是一種基於量子力學的計算方式..."
        },
        "finish_reason": "stop"     // 正常結束為 "stop"，超出長度限制為 "length"
      }
    ]
  }
  ```
  ```json
  // stream=true：以 Server-Sent Events 逐步回傳
  // 每個 chunk 結構相同；首個 chunk 的 delta 須包含 role，後續 chunk 僅含 content
  // 最終 chunk 的 delta 為空物件，finish_reason 為 "stop"，標示串流結束

  // 首個 chunk（含 role）
  {
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",   // 固定值，與非串流的 object 不同，不可混用
    "created": 1700000000,
    "model": "gemma3",
    "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": null}]
  }
  // 中間 chunk（僅含 content）
  {
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 1700000000,
    "model": "gemma3",
    "choices": [{"index": 0, "delta": {"content": "量子"}, "finish_reason": null}]
  }
  // 末尾 chunk（delta 為空，finish_reason 標示結束）
  {
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 1700000000,
    "model": "gemma3",
    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
  }
  ```

  - **OpenAI Python SDK**：由於 REST API 完整遵循 OpenAI 規格，呼叫方僅需將 `base_url` 指向本專案服務即可使用 OpenAI Python SDK 的原生呼叫方式，無需本專案額外實作任何 SDK 層。
  ```python
  from openai import OpenAI

  client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")

  response = client.chat.completions.create(
      model="gemma3",
      messages=[{"role": "user", "content": "解釋量子計算"}],
      stream=False,
  )
  print(response.choices[0].message.content)
  ```

  - **Open WebUI**：透過 Open WebUI 現有的 OpenAI 相容設定直接對接本專案 REST API，提供圖形化互動展示介面，無需本專案額外開發任何前端元件。
