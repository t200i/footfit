# AMD Ryzen AI NPU 程式開發指南

本指南提供完整的程式開發參考，協助您將 AMD Ryzen AI NPU 整合到您的應用程式中。

---

## 📚 目錄

1. [基礎概念](#基礎概念)
2. [核心 API](#核心-api)
3. [實作範例](#實作範例)
4. [整合指南](#整合指南)
5. [最佳實踐](#最佳實踐)

---

## 🎓 基礎概念

### ONNX Runtime GenAI 架構

```
您的應用程式
    ↓
onnxruntime-genai (Python API)
    ↓
ONNX Runtime
    ↓
Ryzen AI Execution Provider
    ↓
AMD NPU 硬體
```

### 核心組件

1. **Model**: ONNX 模型載入器
2. **Tokenizer**: 文本編碼/解碼器
3. **GeneratorParams**: 生成參數配置
4. **Generator**: 文本生成引擎

---

## 🔧 核心 API

### 1. 模型載入

```python
import onnxruntime_genai as og

# 載入模型
model_dir = "./Qwen2-1.5B-onnx-ryzenai-npu"
model = og.Model(model_dir)

# 創建 tokenizer
tokenizer = og.Tokenizer(model)
```

### 2. 文本編碼

```python
# 編碼文本為 token IDs
text = "Hello, world!"
input_tokens = tokenizer.encode(text)

# input_tokens 是一個整數序列
print(type(input_tokens))  # <class 'onnxruntime_genai.Sequences'>
```

### 3. 生成參數設定

```python
# 創建生成參數
params = og.GeneratorParams(model)

# 設定搜尋選項
params.set_search_options(
    max_length=200,           # 最大生成長度
    min_length=10,            # 最小生成長度
    do_sample=False,          # 是否採樣（False = greedy）
    top_p=0.9,                # Nucleus sampling
    top_k=50,                 # Top-K sampling
    temperature=1.0,          # 溫度係數
    repetition_penalty=1.0    # 重複懲罰
)

# 設定輸入 tokens
params.input_ids = input_tokens
```

### 4. 生成文本

#### 方式 A: 一次性生成（阻塞）

```python
# 創建生成器
generator = og.Generator(model, params)

# 生成所有 tokens
while not generator.is_done():
    generator.compute_logits()
    generator.generate_next_token()

# 取得完整輸出
output_tokens = generator.get_sequence(0)
output_text = tokenizer.decode(output_tokens)
print(output_text)
```

#### 方式 B: 串流生成（逐 token）

```python
generator = og.Generator(model, params)

# 逐 token 生成並顯示
while not generator.is_done():
    generator.compute_logits()
    generator.generate_next_token()
    
    # 取得最新生成的 token
    new_token = generator.get_next_tokens()[0]
    new_text = tokenizer.decode([new_token])
    
    # 即時顯示
    print(new_text, end='', flush=True)

print()  # 換行
```

---

## 💻 實作範例

### 範例 1: 基礎推論函數

```python
import onnxruntime_genai as og

def simple_inference(model_dir, prompt, max_length=200):
    """
    簡單的推論函數
    
    Args:
        model_dir: 模型目錄路徑
        prompt: 輸入文本
        max_length: 最大生成長度
    
    Returns:
        生成的文本
    """
    # 載入模型
    model = og.Model(model_dir)
    tokenizer = og.Tokenizer(model)
    
    # 編碼輸入
    input_tokens = tokenizer.encode(prompt)
    
    # 設定參數
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=max_length)
    params.input_ids = input_tokens
    
    # 生成
    generator = og.Generator(model, params)
    while not generator.is_done():
        generator.compute_logits()
        generator.generate_next_token()
    
    # 解碼輸出
    output_tokens = generator.get_sequence(0)
    output_text = tokenizer.decode(output_tokens)
    
    return output_text


# 使用
result = simple_inference(
    "./Qwen2-1.5B-onnx-ryzenai-npu",
    "什麼是人工智慧？"
)
print(result)
```

### 範例 2: 帶 Chat Template 的推論

```python
def chat_inference(model_dir, prompt, chat_template="qwen", max_length=200):
    """
    使用 chat template 的推論函數
    
    Args:
        model_dir: 模型目錄
        prompt: 用戶輸入
        chat_template: chat template 類型
        max_length: 最大生成長度
    
    Returns:
        AI 回應文本
    """
    # Chat templates
    templates = {
        'qwen': '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n',
        'llama3': '<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n',
        'phi3': '<|user|>\n{prompt}<|end|>\n<|assistant|>\n',
    }
    
    # 格式化 prompt
    template = templates.get(chat_template, '{prompt}')
    formatted_prompt = template.format(prompt=prompt)
    
    # 載入模型
    model = og.Model(model_dir)
    tokenizer = og.Tokenizer(model)
    
    # 編碼並生成
    input_tokens = tokenizer.encode(formatted_prompt)
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=max_length)
    params.input_ids = input_tokens
    
    generator = og.Generator(model, params)
    while not generator.is_done():
        generator.compute_logits()
        generator.generate_next_token()
    
    # 解碼並移除 prompt
    output_tokens = generator.get_sequence(0)
    full_output = tokenizer.decode(output_tokens)
    
    # 移除輸入部分，只返回 AI 回應
    response = full_output.replace(formatted_prompt, '').strip()
    
    return response


# 使用
response = chat_inference(
    "./Qwen2-1.5B-onnx-ryzenai-npu",
    "解釋一下機器學習",
    chat_template="qwen"
)
print(response)
```

### 範例 3: 串流生成 (適合 Web 應用)

```python
def streaming_inference(model_dir, prompt, callback=None):
    """
    串流生成，適合實時顯示
    
    Args:
        model_dir: 模型目錄
        prompt: 輸入文本
        callback: 回調函數，接收每個新生成的 token
    
    Yields:
        逐個生成的 token 文本
    """
    model = og.Model(model_dir)
    tokenizer = og.Tokenizer(model)
    
    input_tokens = tokenizer.encode(prompt)
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=512)
    params.input_ids = input_tokens
    
    generator = og.Generator(model, params)
    
    while not generator.is_done():
        generator.compute_logits()
        generator.generate_next_token()
        
        new_token = generator.get_next_tokens()[0]
        new_text = tokenizer.decode([new_token])
        
        # 呼叫回調（如果有）
        if callback:
            callback(new_text)
        
        # yield 給調用者
        yield new_text


# 使用範例 1: 簡單打印
for token in streaming_inference("./model", "Hello"):
    print(token, end='', flush=True)

# 使用範例 2: 收集到列表
tokens = list(streaming_inference("./model", "Hello"))
full_text = ''.join(tokens)

# 使用範例 3: 與回調函數
def my_callback(token):
    # 可以發送到 WebSocket, 更新 UI 等
    websocket.send(token)

for token in streaming_inference("./model", "Hello", callback=my_callback):
    pass
```

### 範例 4: 批次推論

```python
def batch_inference(model_dir, prompts, max_length=200):
    """
    批次處理多個 prompts
    
    Args:
        model_dir: 模型目錄
        prompts: prompt 列表
        max_length: 最大生成長度
    
    Returns:
        結果列表
    """
    # 載入模型（只載入一次）
    model = og.Model(model_dir)
    tokenizer = og.Tokenizer(model)
    
    results = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"處理 {i}/{len(prompts)}: {prompt[:50]}...")
        
        # 推論
        input_tokens = tokenizer.encode(prompt)
        params = og.GeneratorParams(model)
        params.set_search_options(max_length=max_length)
        params.input_ids = input_tokens
        
        generator = og.Generator(model, params)
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
        
        output_tokens = generator.get_sequence(0)
        output_text = tokenizer.decode(output_tokens)
        
        results.append({
            'prompt': prompt,
            'response': output_text
        })
    
    return results


# 使用
prompts = [
    "什麼是 AI？",
    "解釋深度學習",
    "NPU 的優勢"
]

results = batch_inference("./model", prompts)

for r in results:
    print(f"Q: {r['prompt']}")
    print(f"A: {r['response']}\n")
```

### 範例 5: 封裝成類別

```python
class NPUInference:
    """NPU 推論類別，方便重複使用"""
    
    def __init__(self, model_dir, chat_template='qwen'):
        """
        初始化
        
        Args:
            model_dir: 模型目錄
            chat_template: chat template 類型
        """
        self.model_dir = model_dir
        self.chat_template = chat_template
        
        # 載入模型（初始化時載入一次）
        self.model = og.Model(model_dir)
        self.tokenizer = og.Tokenizer(self.model)
        
        # Chat templates
        self.templates = {
            'qwen': '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n',
            'llama3': '<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n',
            'phi3': '<|user|>\n{prompt}<|end|>\n<|assistant|>\n',
        }
    
    def format_prompt(self, prompt):
        """格式化 prompt"""
        template = self.templates.get(self.chat_template, '{prompt}')
        return template.format(prompt=prompt)
    
    def generate(self, prompt, max_length=200, stream=False):
        """
        生成文本
        
        Args:
            prompt: 輸入 prompt
            max_length: 最大生成長度
            stream: 是否串流輸出
        
        Returns:
            生成的文本（或 generator）
        """
        # 格式化 prompt
        formatted_prompt = self.format_prompt(prompt)
        
        # 編碼
        input_tokens = self.tokenizer.encode(formatted_prompt)
        
        # 設定參數
        params = og.GeneratorParams(self.model)
        params.set_search_options(max_length=max_length)
        params.input_ids = input_tokens
        
        # 生成
        generator = og.Generator(self.model, params)
        
        if stream:
            # 串流模式
            return self._stream_generate(generator)
        else:
            # 阻塞模式
            while not generator.is_done():
                generator.compute_logits()
                generator.generate_next_token()
            
            output_tokens = generator.get_sequence(0)
            output_text = self.tokenizer.decode(output_tokens)
            
            # 移除 prompt
            response = output_text.replace(formatted_prompt, '').strip()
            return response
    
    def _stream_generate(self, generator):
        """內部串流生成器"""
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
            
            new_token = generator.get_next_tokens()[0]
            new_text = self.tokenizer.decode([new_token])
            yield new_text
    
    def chat(self, max_length=200):
        """互動式對話"""
        print("開始對話（輸入 'exit' 離開）\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("再見！")
                break
            
            if not user_input:
                continue
            
            print("AI: ", end='', flush=True)
            
            for token in self.generate(user_input, max_length, stream=True):
                print(token, end='', flush=True)
            
            print("\n")


# 使用範例
if __name__ == '__main__':
    # 初始化
    ai = NPUInference("./Qwen2-1.5B-onnx-ryzenai-npu", chat_template='qwen')
    
    # 單次生成
    response = ai.generate("什麼是人工智慧？")
    print(response)
    
    # 串流生成
    for token in ai.generate("解釋機器學習", stream=True):
        print(token, end='', flush=True)
    print()
    
    # 互動對話
    ai.chat()
```

---

## 🔌 整合指南

### 整合到 Flask Web 應用

```python
from flask import Flask, request, jsonify, Response
import onnxruntime_genai as og
import json

app = Flask(__name__)

# 全域模型（應用啟動時載入）
MODEL_DIR = "./Qwen2-1.5B-onnx-ryzenai-npu"
model = og.Model(MODEL_DIR)
tokenizer = og.Tokenizer(model)

@app.route('/api/generate', methods=['POST'])
def generate():
    """生成文本 API"""
    data = request.json
    prompt = data.get('prompt', '')
    max_length = data.get('max_length', 200)
    
    # 編碼
    input_tokens = tokenizer.encode(prompt)
    
    # 生成
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=max_length)
    params.input_ids = input_tokens
    
    generator = og.Generator(model, params)
    while not generator.is_done():
        generator.compute_logits()
        generator.generate_next_token()
    
    output_tokens = generator.get_sequence(0)
    output_text = tokenizer.decode(output_tokens)
    
    return jsonify({'response': output_text})


@app.route('/api/stream', methods=['POST'])
def stream():
    """串流生成 API"""
    data = request.json
    prompt = data.get('prompt', '')
    
    def generate_stream():
        input_tokens = tokenizer.encode(prompt)
        params = og.GeneratorParams(model)
        params.set_search_options(max_length=512)
        params.input_ids = input_tokens
        
        generator = og.Generator(model, params)
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
            
            new_token = generator.get_next_tokens()[0]
            new_text = tokenizer.decode([new_token])
            
            # Server-Sent Events 格式
            yield f"data: {json.dumps({'token': new_text})}\n\n"
    
    return Response(generate_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(port=5000)
```

### 整合到 FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import onnxruntime_genai as og
import json

app = FastAPI()

# 載入模型
MODEL_DIR = "./Qwen2-1.5B-onnx-ryzenai-npu"
model = og.Model(MODEL_DIR)
tokenizer = og.Tokenizer(model)

class GenerateRequest(BaseModel):
    prompt: str
    max_length: int = 200

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    """生成 API"""
    input_tokens = tokenizer.encode(req.prompt)
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=req.max_length)
    params.input_ids = input_tokens
    
    generator = og.Generator(model, params)
    while not generator.is_done():
        generator.compute_logits()
        generator.generate_next_token()
    
    output_tokens = generator.get_sequence(0)
    output_text = tokenizer.decode(output_tokens)
    
    return {"response": output_text}

@app.post("/api/stream")
async def stream(req: GenerateRequest):
    """串流 API"""
    async def generate_stream():
        input_tokens = tokenizer.encode(req.prompt)
        params = og.GeneratorParams(model)
        params.set_search_options(max_length=req.max_length)
        params.input_ids = input_tokens
        
        generator = og.Generator(model, params)
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
            
            new_token = generator.get_next_tokens()[0]
            new_text = tokenizer.decode([new_token])
            
            yield f"data: {json.dumps({'token': new_text})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

---

## 💡 最佳實踐

### 1. 模型管理

```python
# ✅ 好：載入一次，重複使用
model = og.Model(model_dir)
for prompt in prompts:
    # 使用同一個 model
    pass

# ❌ 壞：每次都重新載入
for prompt in prompts:
    model = og.Model(model_dir)  # 效能差！
    pass
```

### 2. 錯誤處理

```python
try:
    model = og.Model(model_dir)
except Exception as e:
    print(f"模型載入失敗: {e}")
    # 處理錯誤
```

### 3. 資源清理

```python
# Python 會自動處理，但可以明確刪除
del model
del tokenizer
```

### 4. 參數調整

```python
# 高品質（慢）
params.set_search_options(
    temperature=0.7,
    top_p=0.95,
    top_k=50
)

# 快速（可能重複）
params.set_search_options(
    temperature=0.0,  # Greedy
    do_sample=False
)
```

---

## 📚 參考資源

- [ONNX Runtime GenAI API 文件](https://onnxruntime.ai/docs/genai/)
- [AMD Ryzen AI 文件](https://www.amd.com/ryzen-ai)
- [範例程式碼](../run_npu_inference.py)
