from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal
from pathlib import Path
import os
import json
import httpx
from dotenv import load_dotenv

from app.services.llm import load_prompt, extract_text_content, build_response
from app.services.chat_persistence import save_turn
from app.core.auth import get_current_user
from app.db.models import User
from app.db.session import get_db

load_dotenv()

router = APIRouter()

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "chat.json"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatTurn]
    test: bool = False
    debug: bool = False


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if request.test:
        with open(MOCK_PATH) as f:
            return json.load(f)

    system_prompt = load_prompt("chat")
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m.role, "content": m.content} for m in request.messages]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": MODEL, "messages": messages},
            timeout=60.0,
        )
    raw = response.json()
    assistant_text = extract_text_content(raw)
    formatted = {"message": assistant_text}

    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    if last_user is not None:
        await save_turn(db, current_user.id, last_user.content, assistant_text)

    return build_response(formatted, raw, request.debug)
