from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.services.llm import load_prompt, extract_text_content, build_response
import os
import json
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

router = APIRouter()

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "generate_gym_chat_completions.json"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")

@router.post("/generate_gym_chat_completions")
async def generate_gym_chat_completions(request: ChatRequest):
    if request.test:
        with open(MOCK_PATH) as f:
            return json.load(f)

    system_prompt_template = load_prompt("generate_gym_chat_completions")
    system_prompt = system_prompt_template.replace(
        "{user_profile}",
        json.dumps(request.user_profile.model_dump(), indent=2)
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m.role, "content": m.content} for m in request.messages]

    async with httpx.AsyncClient() as client:
        raw = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": MODEL, "messages": messages},
            timeout=60.0,
        )
    formatted = {"message": extract_text_content(raw)}
    return build_response(formatted, raw, request.debug)
