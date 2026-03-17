import os
from fastapi import FastAPI
from dotenv import load_dotenv
import httpx

from app.db.session import engine
from app.db.models import Base
from app.routes.example import router as example_router

load_dotenv()

app = FastAPI()
app.include_router(example_router)

# get api keys, urls ,and models
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
print("API KEY:", os.getenv("OPENROUTER_API_KEY"))
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")

# connect to database
@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database connected.")
    except Exception as e:
        print("Database unavailable. Running without Database")
        print(e)

# root 
@app.get("/")
def root():
    return {"status": "ok"}

# health check
@app.get("/health")
def health():
    return {"service": "alive"}

# basic chat endpoint
@app.post("/chat")
async def chat(prompt: str):
    print("API KEY:", os.getenv("OPENROUTER_API_KEY"))
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