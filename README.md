# FY115-BCI-Agent

### 安裝 Python 套件：

  ```
  pip install Ryzers
  pip install onnxruntime-genai huggingface_hub
  ```

### 2. 下載模型：

  ```
  huggingface-cli download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./gemma3_4b_npu
  ```

### 在程式裡呼叫：

```python
import ryzers
import onnxruntime_genai as og

session = og.InferenceSession("./gemma3_4b_npu", providers=["ROCMExecutionProvider"])
generator = og.Generator(session)

print(generator.generate("Explain ESOP RAG benchmarks.", max_tokens=200))
```
