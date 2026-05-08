與Open AI Python SDK整合
```
from openai import OpenAI
response = ollama.chat(
  model='gemma4', 
  messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response['message']['content'])
```
