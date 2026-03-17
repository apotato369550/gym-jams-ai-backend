import os
from fastapi import FastAPI
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"service": "alive"}


@app.post("/chat")
async def chat(prompt: str):
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
                    {"role": "user", "content": prompt}
                ],
            },
            timeout=30.0
        )

    return response.json()