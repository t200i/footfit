# transformers, accelerate
from transformers import AutoProcessor, AutoModelForImageTextToText, TextStreamer
import torch

print('GPU Available:', torch.cuda.is_available())

model_id = "google/gemma-4-E4B-it"

print(f"Loading model: {model_id}")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(model_id, dtype=torch.bfloat16, device_map="auto")
print(f"Model device: {next(model.parameters()).device}")
model.eval()

# Demo conversation
messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "你好！請用繁體中文介紹你自己。"}],
    }
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_tensors="pt",
    return_dict=True,
)

# Move inputs to the same device as the model
device = model.device
inputs = {k: v.to(device) for k, v in inputs.items()}

streamer = TextStreamer(processor.tokenizer, skip_prompt=True, skip_special_tokens=True)

print("\n=== Demo Conversation ===")
print(f"User: {messages[0]['content'][0]['text']}")
print("Assistant: ", end="", flush=True)
with torch.inference_mode():
    model.generate(**inputs, max_new_tokens=200, streamer=streamer)
print()
