import os
from fastapi import FastAPI
from dotenv import load_dotenv
import httpx

from app.db.session import engine
from app.db.models import Base
from app.routes.example import router as example_router
from app.routes.analyze_workout import router as analyze_workout_router
from app.routes.generate_gym_profile import router as generate_gym_profile_router
from app.routes.analyze_workout_history import router as analyze_workout_history_router
from app.routes.generate_gym_chat_completions import router as gym_chat_router
from app.routes.chat import router as chat_router
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from app.db.session import get_db
from app.db.models import User

load_dotenv()

app = FastAPI()
app.include_router(example_router)
app.include_router(analyze_workout_router)
app.include_router(generate_gym_profile_router)
app.include_router(analyze_workout_history_router)
app.include_router(gym_chat_router)
app.include_router(chat_router)

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# get api keys, urls ,and models
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
print("API KEY:", os.getenv("OPENROUTER_API_KEY"))
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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

@app.post("/register_user")
async def register_user(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    hashed = pwd_context.hash(request.password)
    user = User(email=request.email, password_hash=hashed, name=request.name)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    return {"user_id": user.id, "email": user.email}


@app.post("/login_user")
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": str(user.id), "email": user.email, "exp": datetime.utcnow() + timedelta(hours=24)},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"user_id": user.id, "email": user.email, "token": token}


