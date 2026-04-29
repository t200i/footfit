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

```
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv init -p 3.12
Initialized project `fy115-bci-agent`
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv add Ryzers
Using CPython 3.12.13
Creating virtual environment at: .venv
  × No solution found when resolving dependencies:
  ╰─▶ Because ryzers was not found in the package registry and your project depends on ryzers, we can conclude that your
      project's requirements are unsatisfiable.
  help: If you want to add the package regardless of the failed resolution, provide the `--frozen` flag to skip locking and
        syncing.
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv add ryzers
  × No solution found when resolving dependencies:
  ╰─▶ Because ryzers was not found in the package registry and your project depends on ryzers, we can conclude that your
      project's requirements are unsatisfiable.
  help: If you want 
```
