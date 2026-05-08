"""
models/npu/base.py — NPU generic drivers
=========================================
Provides two ChatModel drivers for AMD Ryzen AI NPU inference via the
official Ryzen AI 1.7.1 subprocess scripts:

  NpuTextLm    — delegates to AMD's model_chat.py   (text-only)
  NpuVisionLm  — delegates to AMD's vlm_run.py      (text + image)

Both drivers use Pattern A (yield once): the subprocess produces the full
response, which is yielded as a single chunk.

Environment: ryzen-ai-1.7.1 conda env
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import ClassVar, Iterator

from core.module import ChatModel


# ── Shared helpers ────────────────────────────────────────────────────────────

def _ryzen_ai_path() -> Path:
    root = os.environ.get("RYZEN_AI_INSTALLATION_PATH", r"C:\Program Files\RyzenAI\1.7.1")
    return Path(root)


def _setup_env() -> None:
    """Add Ryzen AI deployment DLLs to PATH if not already present."""
    dll_path = _ryzen_ai_path() / "deployment"
    if dll_path.exists():
        current = os.environ.get("PATH", "")
        if str(dll_path) not in current:
            os.environ["PATH"] = f"{dll_path};{current}"


def _find_script(name: str) -> Path | None:
    candidates = [
        _ryzen_ai_path() / "LLM" / "example" / name,
        _ryzen_ai_path() / "LLM" / "example" / "vlm" / name,
    ]
    return next((p for p in candidates if p.exists()), None)


def _messages_to_prompt(messages: list[dict]) -> str:
    """Flatten OpenAI-style messages to a plain prompt string."""
    parts = []
    for m in messages:
        content = m["content"]
        if isinstance(content, list):
            content = " ".join(
                c["text"] for c in content if c.get("type") == "text"
            )
        parts.append(f"{m['role'].capitalize()}: {content}")
    return "\n".join(parts)


# ── NpuTextLm ─────────────────────────────────────────────────────────────────

class NpuTextLm(ChatModel):
    """
    NPU text-only LLM driver for AMD Ryzen AI.

    Delegates inference to AMD's model_chat.py script via subprocess.
    model_id must be the local path to the cloned ONNX model directory,
    e.g. "./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K".

    Usage:
        svc = NpuTextLm("./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K")
        serve(svc)
    """

    description:     ClassVar[str]  = "NPU TextLM via AMD Ryzen AI (model_chat.py)"
    supports_vision: ClassVar[bool] = False

    def __init__(self, model_id: str) -> None:
        _setup_env()
        model_path = Path(model_id).resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        script = _find_script("model_chat.py") or _find_script("run_model.py")
        if script is None:
            raise RuntimeError(
                "AMD Ryzen AI LLM script not found. "
                "Ensure Ryzen AI Software 1.7.1 is installed."
            )

        self.model_id    = str(model_path)
        self.device      = "NPU"
        self._model_path = model_path
        self._script     = script
        print(f"[NpuTextLm] Ready — {model_path.name} via {script.name}")

    def create(self, messages: list[dict], max_tokens: int = 200) -> Iterator[str]:
        prompt = _messages_to_prompt(messages)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(prompt)
            prompt_file = f.name

        cmd = self._build_cmd(prompt_file, max_tokens)
        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            ) as proc:
                for line in proc.stdout:
                    stripped = line.rstrip("\n")
                    if stripped:
                        yield stripped + "\n"
        finally:
            Path(prompt_file).unlink(missing_ok=True)

    def _build_cmd(self, prompt_file: str, max_tokens: int) -> list[str]:
        cmd = ["python", str(self._script), "-m", str(self._model_path)]
        if self._script.name == "model_chat.py":
            cmd += ["-pr", prompt_file, "-mpt", str(max_tokens)]
        else:
            cmd += ["-l", str(max_tokens)]
        return cmd


# ── NpuVisionLm ───────────────────────────────────────────────────────────────

class NpuVisionLm(ChatModel):
    """
    NPU vision-language model driver for AMD Ryzen AI.

    Delegates inference to AMD's vlm_run.py script via subprocess.
    Must be run from within the model directory (vlm_run.py expects it).

    model_id must be the local path to the cloned ONNX-VLM model directory,
    e.g. "./Gemma-3-4b-it-mm-onnx-ryzenai-npu".

    Usage:
        svc = NpuVisionLm("./Gemma-3-4b-it-mm-onnx-ryzenai-npu")
        serve(svc)
    """

    description:     ClassVar[str]  = "NPU VisionLM via AMD Ryzen AI (vlm_run.py)"
    supports_vision: ClassVar[bool] = True

    def __init__(self, model_id: str) -> None:
        _setup_env()
        model_path = Path(model_id).resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        script = _find_script("vlm_run.py")
        if script is None:
            raise RuntimeError(
                "AMD Ryzen AI VLM script not found. "
                "Ensure Ryzen AI Software 1.7.1 is installed."
            )

        self.model_id    = str(model_path)
        self.device      = "NPU"
        self._model_path = model_path
        self._script     = script
        print(f"[NpuVisionLm] Ready — {model_path.name} via {script.name}")

    def create(self, messages: list[dict], max_tokens: int = 256) -> Iterator[str]:
        # Extract text prompt and the first image from messages
        text, images = "", []
        for m in messages:
            t, imgs = self.parse_content(m["content"])
            if t:
                text = t
            images.extend(imgs)

        if not images:
            raise ValueError("NpuVisionLm.create(): no image found in messages")

        # Save the first image to a temp file next to the model directory
        import tempfile as _tf
        img = images[0]
        with _tf.NamedTemporaryFile(
            delete=False, suffix=".jpg", dir=self._model_path
        ) as tmp:
            img.save(tmp.name, format="JPEG")
            img_path = Path(tmp.name)

        # vlm_run.py expects relative paths and must be run from model_dir
        cmd = [
            "python", str(self._script),
            "-m", ".",
            "-i", img_path.name,   # relative to model_dir
            "-p", text,
            "--max_tokens", str(max_tokens),
        ]

        original_dir = Path.cwd()
        try:
            os.chdir(self._model_path)
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            ) as proc:
                output = proc.stdout.read()
            if output.strip():
                yield output.strip()
        finally:
            os.chdir(original_dir)
            img_path.unlink(missing_ok=True)
