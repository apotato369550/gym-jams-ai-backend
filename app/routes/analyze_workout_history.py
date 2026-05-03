from datetime import date, timedelta
from typing import Literal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_profile import UserProfile
from app.services.llm import call_llm, load_prompt, extract_json_content, build_response
from app.core.auth import get_current_user
from app.db.models import (
    User,
    WorkoutSession as WorkoutSessionModel,
    WorkoutExercise,
    WorkoutHistorySummary,
)
from app.db.session import get_db
from pydantic import BaseModel
import json
from pathlib import Path

MOCK_PATH = Path(__file__).parent.parent.parent / "data" / "mock" / "analyze_workout_history.json"

RANGE_DAYS = {"week": 7, "month": 30, "3months": 90}

EMPTY_SUMMARY = {
    "consistency_score": 0,
    "consistency_note": "No sessions logged in this range yet.",
    "top_exercises": [],
    "volume_trend": None,
    "volume_note": None,
    "plateaus_detected": None,
    "trajectory_suggestion": None,
    "thing_youre_doing_well": None,
}

router = APIRouter()


class AnalyzeHistoryRequest(BaseModel):
    range: Literal["week", "month", "3months"]
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

    cutoff = date.today() - timedelta(days=RANGE_DAYS[request.range])
    sessions_result = await db.execute(
        select(WorkoutSessionModel)
        .where(
            WorkoutSessionModel.user_id == current_user.id,
            WorkoutSessionModel.date >= cutoff,
        )
        .order_by(WorkoutSessionModel.date.asc())
    )
    sessions = sessions_result.scalars().all()

    if not sessions:
        return build_response({**EMPTY_SUMMARY, "summary_id": None}, None, request.debug)

    session_ids = [s.id for s in sessions]
    ex_result = await db.execute(
        select(WorkoutExercise).where(WorkoutExercise.session_id.in_(session_ids))
    )
    by_session: dict[int, list[WorkoutExercise]] = {sid: [] for sid in session_ids}
    for ex in ex_result.scalars().all():
        by_session[ex.session_id].append(ex)

    history_payload = {
        "range": request.range,
        "sessions": [
            {
                "date": s.date.isoformat(),
                "notes": s.notes,
                "exercises": [
                    {
                        "name": e.name,
                        "sets": e.sets,
                        "reps": e.reps,
                        "weight_kg": float(e.weight_kg) if e.weight_kg is not None else None,
                        "duration_mins": float(e.duration_mins) if e.duration_mins is not None else None,
                    }
                    for e in by_session[s.id]
                ],
            }
            for s in sessions
        ],
    }

    system_prompt = load_prompt("analyze_workout_history")
    user_message = json.dumps({
        "history": history_payload,
        "user_profile": request.user_profile.model_dump(),
    }, indent=2)
    raw = await call_llm(system_prompt, user_message)
    formatted = extract_json_content(raw)

    plateaus = formatted.get("plateaus_detected")
    if plateaus is not None and not isinstance(plateaus, str):
        plateaus = json.dumps(plateaus)

    summary = WorkoutHistorySummary(
        user_id=current_user.id,
        range_period=request.range,
        consistency_score=formatted.get("consistency_score"),
        consistency_note=formatted.get("consistency_note"),
        top_exercises=formatted.get("top_exercises", []),
        volume_trend=formatted.get("volume_trend"),
        volume_note=formatted.get("volume_note"),
        plateaus_detected=plateaus,
        trajectory_suggestion=formatted.get("trajectory_suggestion"),
        thing_youre_doing_well=formatted.get("thing_youre_doing_well"),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    formatted = {**formatted, "summary_id": summary.id}
    return build_response(formatted, raw, request.debug)
