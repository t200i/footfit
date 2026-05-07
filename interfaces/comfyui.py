"""
interfaces/comfyui.py — Generic ComfyUI custom node
=====================================================
Copy (or symlink) this file to:  ComfyUI/custom_nodes/ryzen_ai_llm.py

Set the environment variable MODEL_NAME to choose which model to load:
  MODEL_NAME=gemma4

The node appears in ComfyUI under the category "Ryzen AI / LLM".
"""

from __future__ import annotations

import os

# Lazy singleton — model loads on first node execution
_service = None


def _get_service():
    global _service
    if _service is None:
        import sys
        # Allow importing from the project root when placed in custom_nodes/
        project_root = os.environ.get("RYZEN_AI_PROJECT_ROOT", os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from serve import load_model  # noqa: PLC0415
        model_name = os.environ.get("MODEL_NAME", "gemma4")
        _service = load_model(model_name)
    return _service


class RyzenAILLMNode:
    CATEGORY = "Ryzen AI/LLM"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "你好！"}),
                "max_new_tokens": ("INT", {"default": 200, "min": 1, "max": 2048}),
            }
        }

    def run(self, prompt: str, max_new_tokens: int) -> tuple[str]:
        svc = _get_service()
        messages = [{"role": "user", "content": prompt}]
        response = svc.generate(messages, max_new_tokens=max_new_tokens)
        return (response,)


NODE_CLASS_MAPPINGS = {"RyzenAILLMNode": RyzenAILLMNode}
NODE_DISPLAY_NAME_MAPPINGS = {"RyzenAILLMNode": "Ryzen AI LLM"}
