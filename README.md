# FY115-BCI-Agent

### 安裝 Python 套件：

  ```
  uv init -p 3.12
  uv add git+https://github.com/AMDResearch/Ryzers.git
  uv add onnxruntime-genai huggingface_hub
  ```

### 2. 下載模型：

  ```
  uv run huggingface-cli download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu
  ```

### 在程式裡呼叫：

```python
import onnxruntime_genai as og

# 指向你下載的目錄
model_dir = "./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu"

# 同時提供 Windows 與 Linux 的 provider
providers = ["DmlExecutionProvider", "ROCMExecutionProvider", "CPUExecutionProvider"]

session = og.InferenceSession(model_dir, providers=providers)
generator = og.Generator(session)

prompt = "Explain ESOP RAG benchmarks."
output = generator.generate(prompt, max_tokens=200)
print(output)
```
```
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv run .\test.py   
Traceback (most recent call last):
  File "C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent\test.py", line 9, in <module>
    session = og.InferenceSession(model_dir, providers=providers)
              ^^^^^^^^^^^^^^^^^^^
AttributeError: module 'onnxruntime_genai' has no attribute 'InferenceSession'
```
