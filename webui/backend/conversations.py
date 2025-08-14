from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import uuid4


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    id: str
    title: str
    messages: List[Message] = field(default_factory=list)


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}

    def create(self, title: str = "New Conversation") -> Conversation:
        cid = uuid4().hex
        conv = Conversation(id=cid, title=title)
        self._conversations[cid] = conv
        return conv

    def list(self) -> List[Conversation]:
        return list(self._conversations.values())

    def get(self, cid: str) -> Conversation | None:
        return self._conversations.get(cid)

    def delete(self, cid: str) -> None:
        self._conversations.pop(cid, None)


store = ConversationStore()
