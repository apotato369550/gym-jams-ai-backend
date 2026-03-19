from fastapi import APIRouter
from app.schemas.user_profile import UserProfile
from app.services.llm import call_llm, load_prompt
import json

router = APIRouter()

@router.post("/generate_gym_profile")
async def generate_gym_profile(user_profile: UserProfile):
    system_prompt = load_prompt("generate_gym_profile")
    user_message = json.dumps(user_profile.model_dump(), indent=2)
    return await call_llm(system_prompt, user_message)
