
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gemma4",
  "prompt": "Hello!"
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
