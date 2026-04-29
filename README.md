# FY115-BCI-Agent

### 安裝 Python 套件：

  ```
  uv init -p 3.12
  uv add git+https://github.com/AMDResearch/Ryzers.git
  uv add onnxruntime-genai huggingface_hub
  ```

### 2. 下載模型：

  ```
  uv run hf download amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu --local-dir ./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu --include "*"
  ```

### 在程式裡呼叫：

```python
import onnxruntime_genai as og

model_dir = "./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu"

# 載入模型
model = og.Model(model_dir)

# 建立 tokenizer
tokenizer = og.Tokenizer(model)

# 建立生成器
generator = og.Generator(model)

# 編碼輸入
input_ids = tokenizer.encode("Explain ESOP RAG benchmarks.")

# 設定生成參數
params = og.GeneratorParams(model)
params.set_search_options(max_length=200)

# 執行生成
generator.generate(input_ids, params)

# 解碼輸出
output_text = tokenizer.decode(generator.get_output())
print(output_text)
```
```
PS C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent> uv run .\test.py
Traceback (most recent call last):
  File "C:\Users\ITRI-EOSL\Documents\GitHub\FY115-BCI-Agent\test.py", line 4, in <module>
    model = og.Model("./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: Error opening ./amd_Gemma-3-4b-it-mm-onnx-ryzenai-npu\genai_config.json
```
