from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.schemas.user_profile import UserProfile
from app.services.llm import call_llm, load_prompt, extract_json_content, build_response
from app.core.auth import get_current_user
from app.db.models import User, GymProfile
from app.db.session import get_db
import json

router = APIRouter()

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "generate_gym_profile.json"

class GenerateGymProfileRequest(BaseModel):
    user_profile: UserProfile
    test: bool = False
    debug: bool = False

@router.post("/generate_gym_profile")
async def generate_gym_profile(
    request: GenerateGymProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if request.test:
        with open(MOCK_PATH) as f:
            return json.load(f)
    system_prompt = load_prompt("generate_gym_profile")
    user_message = json.dumps(request.user_profile.model_dump(), indent=2)
    raw = await call_llm(system_prompt, user_message)
    formatted = extract_json_content(raw)

    result = await db.execute(
        select(GymProfile).where(GymProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()
    if profile is None:
        profile = GymProfile(user_id=current_user.id)
        db.add(profile)

    profile.archetype = formatted.get("archetype", "")
    profile.read_description = formatted.get("read_description", "")
    profile.modalities_youll_enjoy = formatted.get("modalities_youll_enjoy", [])
    profile.first_week_suggestion = formatted.get("first_week_suggestion", "")
    profile.watch_out_for = formatted.get("watch_out_for", "")
    await db.commit()

    return build_response(formatted, raw, request.debug)
