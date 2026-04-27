import os
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (PROMPTS_DIR / f"{name}.txt").read_text()


async def call_llm(system_prompt: str, user_message: str) -> dict:
    """Call OpenRouter with a system prompt and user message. Returns parsed JSON or raw text."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=60.0,
        )
    return response.json()


def extract_json_content(raw: dict) -> dict:
    import re
    try:
        content = raw["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        return {"error": "malformed_envelope", "raw": raw}
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {"raw_text": content}


def extract_text_content(raw: dict) -> str:
    try:
        return raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


def build_response(formatted: dict, raw: dict, debug: bool) -> dict:
    if debug:
        return {"formatted": formatted, "raw": raw}
    return formatted
