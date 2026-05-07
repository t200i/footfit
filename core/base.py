"""
core/base.py — LLMService contract
===================================
Every model in models/ MUST subclass LLMService and implement all abstract
methods. The interface layer (interfaces/) only depends on this file — it
never imports a concrete model directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelInfo:
    model_id: str       # e.g. "google/gemma-4-E4B-it"
    name: str           # short key used in serve.py registry, e.g. "gemma4"
    description: str    # one-line description for /v1/models
    device: str         # resolved at load time, e.g. "cuda:0", "cpu"


class LLMService(ABC):
    """
    Abstract base for all LLM inference services.

    Subclasses must:
      1. Call super().__init__() or set self.info: ModelInfo after loading.
      2. Implement generate() — returns full response text.
      3. Implement generate_stream() — yields text chunks incrementally.

    The interface layer only calls these two methods (+ self.info).
    """

    info: ModelInfo

    @abstractmethod
    def generate(self, messages: list[dict], max_new_tokens: int = 200) -> str:
        """
        Generate a full response and return it as a string.

        Args:
            messages: OpenAI-style message list.
                      [{"role": "user", "content": "你好"}]
            max_new_tokens: Token budget for the generated response.

        Returns:
            The assistant's response as a plain string.
        """

    @abstractmethod
    def generate_stream(
        self, messages: list[dict], max_new_tokens: int = 200
    ):
        """
        Generate a response incrementally.

        Args:
            messages: OpenAI-style message list.
            max_new_tokens: Token budget for the generated response.

        Yields:
            str: Text chunks as they are generated.
        """
