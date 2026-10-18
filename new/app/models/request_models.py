from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    session_id: str
    messages: list
    top_k: int = 20

    attachment_ids: List[str] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"