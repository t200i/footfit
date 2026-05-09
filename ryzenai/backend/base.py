import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Backend(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self) -> None:
        """驗證執行環境可用性，不可用時拋出 RuntimeError；成功時輸出 log 說明計算提供者。"""
        ...
