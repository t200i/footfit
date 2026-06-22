from abc import ABC, abstractmethod
from typing import Any

from ryzenai.backend.base import Backend


class SegmentationModel(ABC):
    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    @property
    def backend(self) -> Backend:
        return self._backend

    def __call__(self, image: Any, *args: Any, **kwargs: Any) -> Any:
        return self.predict(image, *args, **kwargs)

    @abstractmethod
    def predict(self, image: Any, *args: Any, **kwargs: Any) -> Any:
        ...