from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_profile import UserProfile
from app.schemas.workout import WorkoutSession
from pathlib import Path
from app.services.llm import call_llm, load_prompt, extract_json_content, build_response
from app.core.auth import get_current_user
from app.db.models import (
    User,
    WorkoutSession as WorkoutSessionModel,
    WorkoutExercise as WorkoutExerciseModel,
    WorkoutAnalysisResult,
)
from app.db.session import get_db
from pydantic import BaseModel
from datetime import date as date_cls
import json

router = APIRouter()

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "analyze_workout.json"

class AnalyzeWorkoutRequest(BaseModel):
    workout: WorkoutSession
    user_profile: UserProfile
    test: bool = False
    debug: bool = False

@router.post("/analyze_workout")
async def analyze_workout(
    request: AnalyzeWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if request.test:
        with open(MOCK_PATH) as f:
            return json.load(f)
    system_prompt = load_prompt("analyze_workout")
    user_message = json.dumps({
        "workout": request.workout.model_dump(),
        "user_profile": request.user_profile.model_dump()
    }, indent=2)
    raw = await call_llm(system_prompt, user_message)
    formatted = extract_json_content(raw)

    session = WorkoutSessionModel(
        user_id=current_user.id,
        date=date_cls.fromisoformat(request.workout.date),
        notes=request.workout.notes,
    )
    db.add(session)
    await db.flush()

    for ex in request.workout.exercises:
        db.add(WorkoutExerciseModel(
            session_id=session.id,
            name=ex.name,
            sets=ex.sets,
            reps=ex.reps,
            weight_kg=ex.weight_kg,
            duration_mins=ex.duration_mins,
        ))

    db.add(WorkoutAnalysisResult(
        session_id=session.id,
        total_volume_kg=formatted.get("total_volume_kg"),
        total_reps=formatted.get("total_reps"),
        muscle_groups_targeted=formatted.get("muscle_groups_targeted", []),
        estimated_calories_burned=formatted.get("estimated_calories_burned"),
        intensity_rating=formatted.get("intensity_rating"),
        observation=formatted.get("observation"),
    ))
    await db.commit()

    formatted = {**formatted, "session_id": session.id}
    return build_response(formatted, raw, request.debug)
