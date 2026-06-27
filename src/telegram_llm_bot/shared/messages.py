from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BaseMessage:
    content: str
    additional_kwargs: dict = field(default_factory=dict)
    type: str = ""

    def dict(self) -> dict:
        return {
            "content": self.content,
            "additional_kwargs": self.additional_kwargs,
            "type": self.type,
        }


class HumanMessage(BaseMessage):
    def __init__(self, content: str, additional_kwargs: Optional[dict] = None):
        super().__init__(content, additional_kwargs or {}, "human")


class AIMessage(BaseMessage):
    def __init__(self, content: str, additional_kwargs: Optional[dict] = None):
        super().__init__(content, additional_kwargs or {}, "ai")


class SystemMessage(BaseMessage):
    def __init__(self, content: str, additional_kwargs: Optional[dict] = None):
        super().__init__(content, additional_kwargs or {}, "system")


def messages_from_dict(items: list[dict]) -> list[BaseMessage]:
    messages = []
    for item in items:
        message_type = item.get("type")
        data = item.get("data", {})
        content = data.get("content", "")
        additional_kwargs = data.get("additional_kwargs") or {}
        if message_type == "human":
            messages.append(HumanMessage(content=content, additional_kwargs=additional_kwargs))
        elif message_type == "ai":
            messages.append(AIMessage(content=content, additional_kwargs=additional_kwargs))
        elif message_type == "system":
            messages.append(SystemMessage(content=content, additional_kwargs=additional_kwargs))
        else:
            messages.append(
                BaseMessage(content=content, additional_kwargs=additional_kwargs, type=message_type)
            )
    return messages
