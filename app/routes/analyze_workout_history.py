from fastapi import APIRouter
from app.schemas.user_profile import UserProfile
from app.schemas.workout import WorkoutHistory
from app.services.llm import call_llm, load_prompt, extract_json_content, build_response
from pydantic import BaseModel
import json
from pathlib import Path

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "analyze_workout_history.json"

router = APIRouter()

class AnalyzeHistoryRequest(BaseModel):
    history: WorkoutHistory
    user_profile: UserProfile
    test: bool = False
    debug: bool = False

@router.post("/analyze_workout_history")
async def analyze_workout_history(request: AnalyzeHistoryRequest):
    if request.test:
        with open(MOCK_PATH) as f:
            return json.load(f)

    system_prompt = load_prompt("analyze_workout_history")
    user_message = json.dumps({
        "history": request.history.model_dump(),
        "user_profile": request.user_profile.model_dump()
    }, indent=2)
    raw = await call_llm(system_prompt, user_message)
    formatted = extract_json_content(raw)
    return build_response(formatted, raw, request.debug)
