from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import (
    User,
    WorkoutSession as WorkoutSessionModel,
    WorkoutExercise,
    WorkoutAnalysisResult,
)
from app.db.session import get_db

router = APIRouter()


@router.get("/workout_sessions")
async def list_workout_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutSessionModel)
        .where(WorkoutSessionModel.user_id == current_user.id)
        .order_by(WorkoutSessionModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    return {
        "limit": limit,
        "offset": offset,
        "sessions": [
            {
                "id": s.id,
                "date": s.date.isoformat(),
                "notes": s.notes,
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ],
    }


@router.get("/workout_sessions/{session_id}")
async def get_workout_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutSessionModel).where(
            WorkoutSessionModel.id == session_id,
            WorkoutSessionModel.user_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    ex_result = await db.execute(
        select(WorkoutExercise).where(WorkoutExercise.session_id == session.id)
    )
    exercises = ex_result.scalars().all()

    an_result = await db.execute(
        select(WorkoutAnalysisResult).where(WorkoutAnalysisResult.session_id == session.id)
    )
    analysis = an_result.scalars().first()

    return {
        "id": session.id,
        "date": session.date.isoformat(),
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "exercises": [
            {
                "name": e.name,
                "sets": e.sets,
                "reps": e.reps,
                "weight_kg": float(e.weight_kg) if e.weight_kg is not None else None,
                "duration_mins": float(e.duration_mins) if e.duration_mins is not None else None,
            }
            for e in exercises
        ],
        "analysis": None if analysis is None else {
            "total_volume_kg": float(analysis.total_volume_kg) if analysis.total_volume_kg is not None else None,
            "total_reps": analysis.total_reps,
            "muscle_groups_targeted": analysis.muscle_groups_targeted,
            "estimated_calories_burned": analysis.estimated_calories_burned,
            "intensity_rating": analysis.intensity_rating,
            "observation": analysis.observation,
        },
    }
