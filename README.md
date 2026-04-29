# FY115-BCI-Agent

### 1. 確保環境支援 (Docker + Ryzen AI Software)

拉取 AMD 提供的 Ryzen AI Docker Image
  ```
  git clone https://github.com/amd/Ryzers.git
  cd Ryzers/docker
  docker build -t ryzenai .
  ```

啟動容器並掛載本地目錄
  ```
  # 這個容器已經包含 ROCm 與 ONNX Runtime GenAI，確保能直接使用 NPU。
  docker run -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  -v $PWD:/workspace \
  --name ryzenai-test \
  ryzenai-dev /bin/bash
  ```
下次可以用啟動服務
  ```
  docker start -ai ryzenai-test
  ```

### 2. 下載 Hugging Face 模型 (Gemma‑3 4B NPU 版本)

安裝 Hugging Face Hub 工具
  ```
  pip install huggingface_hub
  ```
下載 AMD 提供的 Gemma-3 4B NPU 模型
  ```
  huggingface-cli download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu \
    --local-dir ./gemma3_4b_npu
  ```

### 3. 使用 ONNX Runtime GenAI 載入模型

這裡的 `providers=["ROCMExecutionProvider"]` 會確保推論運算 offload 到 Ryzen AI NPU。

```python
import onnxruntime_genai as og

# 指定模型路徑
model_path = "./gemma3_4b_npu"

# 建立 session，指定使用 NPU
session = og.InferenceSession(model_path, providers=["ROCMExecutionProvider"])

# 建立生成器
generator = og.Generator(session)

# 測試 prompt → generate
prompt = "Explain the importance of edge AI in industrial safety."
output = generator.generate(prompt, max_tokens=200)

print("Generated text:\n", output)
```

### 4. 部署成 API 服務 (選用 vLLM)

安裝 vLLM
```
pip install vllm
```

啟動服務，指定 ONNX 模型路徑
```
python -m vllm.entrypoints.openai.api_server \
  --model ./gemma3_4b_npu \
  --port 8000
```
然後就能用 OpenAI API 格式呼叫：
```
import openai

openai.api_base = "http://localhost:8000/v1"
openai.api_key = "dummy"

response = openai.ChatCompletion.create(
    model="gemma3_4b_npu",
    messages=[{"role": "user", "content": "Hello, explain ESOP RAG benchmarks."}]
)

print(response["choices"][0]["message"]["content"
```

