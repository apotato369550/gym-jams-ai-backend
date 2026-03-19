from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.services.llm import load_prompt
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")

@router.post("/generate_gym_chat_completions")
async def generate_gym_chat_completions(request: ChatRequest):
    system_prompt_template = load_prompt("generate_gym_chat_completions")
    system_prompt = system_prompt_template.replace(
        "{user_profile}",
        json.dumps(request.user_profile.model_dump(), indent=2)
    )
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
    return response.json()
