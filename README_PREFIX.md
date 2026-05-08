
```bash
curl http://localhost:8080/api/generate -d '{
  "model": "gemma4", "prompt": "Hello!"
}'
```
與Open AI Python SDK整合
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080", api_key="local")

for chunk in client.chat.completions.create(
  model='gemma4', stream=True,
  messages=[{'role': 'user', 'content': 'Hello!'}]
):
  print(chunk.choices[0]delta.content, end="", flush=True)
```
```bash
docker pull ryzen-ai-gemma4:latest
docker run -d -p 8080:80 ryzen-ai-gemma4
```
Then open `http://localhost:8080`.
