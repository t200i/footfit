"""
interfaces/comfyui.py — Generic ComfyUI custom node factory
=============================================================
Copy (or symlink) to: ComfyUI/custom_nodes/ryzen_ai_llm.py

Set environment variables before starting ComfyUI:
  RYZEN_AI_PROJECT_ROOT  — absolute path to this repo (for sys.path)
  RYZEN_AI_MODEL_CLASS   — dotted import path of the ChatModel subclass,
                           e.g. "models.igpu.base.IgpuVisionLm"
  RYZEN_AI_MODEL_ID      — model_id string passed to the class constructor,
                           e.g. "google/gemma-4-E4B-it"

The node appears in ComfyUI under "Ryzen AI / LLM".
"""

from __future__ import annotations

import importlib
import os
import sys

from core.module import ChatModel

# ── Lazy singleton ─────────────────────────────────────────────────────────────
_service: ChatModel | None = None


def _get_service() -> ChatModel:
    global _service
    if _service is None:
        project_root = os.environ.get("RYZEN_AI_PROJECT_ROOT", os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        class_path = os.environ.get("RYZEN_AI_MODEL_CLASS", "models.igpu.base.IgpuVisionLm")
        model_id   = os.environ.get("RYZEN_AI_MODEL_ID",    "google/gemma-4-E4B-it")

        module_path, class_name = class_path.rsplit(".", 1)
        module  = importlib.import_module(module_path)
        cls     = getattr(module, class_name)
        _service = cls(model_id)

    return _service


class RyzenAILLMNode:
    CATEGORY     = "Ryzen AI/LLM"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION     = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":     ("STRING", {"multiline": True, "default": "你好！"}),
                "max_tokens": ("INT",    {"default": 200, "min": 1, "max": 2048}),
            }
        }

    def run(self, prompt: str, max_tokens: int) -> tuple[str]:
        svc      = _get_service()
        messages = [{"role": "user", "content": prompt}]
        response = "".join(svc.create(messages, max_tokens=max_tokens))
        return (response,)


NODE_CLASS_MAPPINGS        = {"RyzenAILLMNode": RyzenAILLMNode}
NODE_DISPLAY_NAME_MAPPINGS = {"RyzenAILLMNode": "Ryzen AI LLM"}
