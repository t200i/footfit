from typing import Generator, Union

from ryzenai.model import Model
from ryzenai.conversation import Message, ConversationContext
from ryzenai.conversation._utils import _now


class SingleSession:
    """一次性推論：每次呼叫建立獨立 ConversationContext，不保留任何會話狀態。"""

    def __init__(self, model: Model) -> None:
        self._model = model

    def run(self, user_input: Union[str, list]) -> Generator[str, None, None]:
        context = ConversationContext(
            messages=[Message(role="user", content=user_input, timestamp=_now())]
        )
        return self._model(context)
