from abc import ABC, abstractmethod
from typing import Generator, Union

from ryzenai.backend.base import Backend
from ryzenai.conversation import ConversationContext, ToolCall

# generate() 逐段產出文字；若 context.metadata["tools"] 有工具定義且模型支援，
# 也可能產出 ToolCall。
Chunk = Union[str, ToolCall]


class Model(ABC):
    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    def __call__(self, context: ConversationContext) -> Generator[Chunk, None, None]:
        return self.generate(context)

    @abstractmethod
    def generate(self, context: ConversationContext) -> Generator[Chunk, None, None]:
        ...
