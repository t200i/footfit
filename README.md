# FY115-BCI-Agent

### 安裝 Python 套件：

  ```
  uv init -p 3.12
  uv add git+https://github.com/AMDResearch/Ryzers.git
  uv add onnxruntime-genai huggingface_hub
  ```

### 2. 下載模型：

  ```
  uv run huggingface-cli download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./gemma3_4b_npu
  ```

### 在程式裡呼叫：

```python
import onnxruntime_genai as og

# 在 Windows 上用 DirectML provider
session = og.InferenceSession(
    "./gemma3_4b_npu",
    providers=["DmlExecutionProvider"]
)
generator = og.Generator(session)

prompt = "Explain ESOP RAG benchmarks."
output = generator.generate(prompt, max_tokens=200)
print(output)
```
