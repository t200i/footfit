from transformers import AutoProcessor, AutoModelForImageTextToText
import torch

model_id = "google/gemma-4-E2B-it"

print(f"Loading model: {model_id}")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(model_id, torch_dtype=torch.bfloat16)
model.eval()

# Demo conversation
messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "你好！請用繁體中文簡短介紹你自己。"}],
    }
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_tensors="pt",
    return_dict=True,
)

print("Generating response...")
with torch.inference_mode():
    output_ids = model.generate(**inputs, max_new_tokens=200)

# Decode only the newly generated tokens
input_len = inputs["input_ids"].shape[-1]
generated_ids = output_ids[:, input_len:]
response = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("\n=== Demo Conversation ===")
print(f"User: {messages[0]['content'][0]['text']}")
print(f"Assistant: {response}")
