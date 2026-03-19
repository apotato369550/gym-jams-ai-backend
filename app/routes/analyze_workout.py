from fastapi import APIRouter
from app.schemas.user_profile import UserProfile
from app.schemas.workout import WorkoutSession
from app.services.llm import call_llm, load_prompt
from pydantic import BaseModel
import json

router = APIRouter()

class AnalyzeWorkoutRequest(BaseModel):
    workout: WorkoutSession
    user_profile: UserProfile

@router.post("/analyze_workout")
async def analyze_workout(request: AnalyzeWorkoutRequest):
    system_prompt = load_prompt("analyze_workout")
    user_message = json.dumps({
        "workout": request.workout.model_dump(),
        "user_profile": request.user_profile.model_dump()
    }, indent=2)
    return await call_llm(system_prompt, user_message)
