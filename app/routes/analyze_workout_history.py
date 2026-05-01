from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_profile import UserProfile
from app.schemas.workout import WorkoutHistory
from app.services.llm import call_llm, load_prompt, extract_json_content, build_response
from app.core.auth import get_current_user
from app.db.models import User, WorkoutHistorySummary
from app.db.session import get_db
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
async def analyze_workout_history(
    request: AnalyzeHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    summary = WorkoutHistorySummary(
        user_id=current_user.id,
        range_period=request.history.range,
        consistency_score=formatted.get("consistency_score"),
        consistency_note=formatted.get("consistency_note"),
        top_exercises=formatted.get("top_exercises", []),
        volume_trend=formatted.get("volume_trend"),
        volume_note=formatted.get("volume_note"),
        plateaus_detected=formatted.get("plateaus_detected") if isinstance(formatted.get("plateaus_detected"), str) else json.dumps(formatted.get("plateaus_detected")) if formatted.get("plateaus_detected") is not None else None,
        trajectory_suggestion=formatted.get("trajectory_suggestion"),
        thing_youre_doing_well=formatted.get("thing_youre_doing_well"),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    formatted = {**formatted, "summary_id": summary.id}
    return build_response(formatted, raw, request.debug)
