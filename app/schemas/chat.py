from pydantic import BaseModel
from typing import Literal
from app.schemas.user_profile import UserProfile


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_profile: UserProfile
    test: bool = False
    debug: bool = False
