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

# 載入模型
model = og.Model("./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu")

# 建立生成器
generator = og.Generator(model)

# 建立輸入序列
tokenizer = og.Tokenizer(model)
input_ids = tokenizer.encode("Explain ESOP RAG benchmarks.")

# 執行推論
params = og.GeneratorParams(model)
params.set_search_options(max_length=200)

generator.generate(input_ids, params)

# 取出結果
output_text = tokenizer.decode(generator.get_output())
print(output_text)
```
```
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv run .\test.py   
Traceback (most recent call last):
  File "C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent\test.py", line 9, in <module>
    session = og.InferenceSession(model_dir, providers=providers)
              ^^^^^^^^^^^^^^^^^^^
AttributeError: module 'onnxruntime_genai' has no attribute 'InferenceSession'
```
