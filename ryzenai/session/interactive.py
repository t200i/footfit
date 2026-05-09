from typing import Generator, Union

from ryzenai.model import Model
from ryzenai.conversation import Message, ConversationContext
from ryzenai.conversation._utils import _now


class InteractiveSession:
    """互動式對話：跨輪次持有 ConversationContext，每輪追加 user/assistant 訊息。"""

    def __init__(self, model: Model) -> None:
        self._model = model
        self._context = ConversationContext()

    def send(self, user_input: Union[str, list]) -> Generator[str, None, None]:
        self._context.messages.append(
            Message(role="user", content=user_input, timestamp=_now())
        )
        chunks: list[str] = []
        for token in self._model(self._context):
            chunks.append(token)
            yield token
        self._context.messages.append(
            Message(role="assistant", content="".join(chunks), timestamp=_now())
        )
