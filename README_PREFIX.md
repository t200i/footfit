
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gemma4", "prompt": "Hello!"
}'
```
與Open AI Python SDK整合
```python
from openai import OpenAI
response = ollama.chat(
  model='gemma4', 
  messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response['message']['content'])
```
```bash
docker pull ryzen-ai-benchmark:latest
docker run -d -p 8080:80 ryzen-ai-benchmark
```
Then open `http://localhost:8080`.
