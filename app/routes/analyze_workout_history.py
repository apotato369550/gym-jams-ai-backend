from fastapi import APIRouter
from app.schemas.user_profile import UserProfile
from app.schemas.workout import WorkoutHistory
from app.services.llm import call_llm, load_prompt
from pydantic import BaseModel
import json

router = APIRouter()

class AnalyzeHistoryRequest(BaseModel):
    history: WorkoutHistory
    user_profile: UserProfile

@router.post("/analyze_workout_history")
async def analyze_workout_history(request: AnalyzeHistoryRequest):
    system_prompt = load_prompt("analyze_workout_history")
    user_message = json.dumps({
        "history": request.history.model_dump(),
        "user_profile": request.user_profile.model_dump()
    }, indent=2)
    return await call_llm(system_prompt, user_message)
