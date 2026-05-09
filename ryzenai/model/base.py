from abc import ABC, abstractmethod
from typing import Generator

from ryzenai.backend.base import Backend
from ryzenai.conversation import ConversationContext


class Model(ABC):
    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    def __call__(self, context: ConversationContext) -> Generator[str, None, None]:
        return self.generate(context)

    @abstractmethod
    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        ...
