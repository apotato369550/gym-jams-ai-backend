from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import User, WorkoutHistorySummary
from app.db.session import get_db

router = APIRouter()


@router.get("/workout_history_summaries")
async def get_latest_history_summary(
    range: Optional[Literal["week", "month", "3months"]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WorkoutHistorySummary).where(
        WorkoutHistorySummary.user_id == current_user.id
    )
    if range is not None:
        stmt = stmt.where(WorkoutHistorySummary.range_period == range)
    stmt = stmt.order_by(WorkoutHistorySummary.created_at.desc()).limit(1)

    result = await db.execute(stmt)
    summary = result.scalars().first()
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No history summary found")

    return {
        "id": summary.id,
        "range": summary.range_period,
        "consistency_score": float(summary.consistency_score) if summary.consistency_score is not None else None,
        "consistency_note": summary.consistency_note,
        "top_exercises": summary.top_exercises,
        "volume_trend": summary.volume_trend,
        "volume_note": summary.volume_note,
        "plateaus_detected": summary.plateaus_detected,
        "trajectory_suggestion": summary.trajectory_suggestion,
        "thing_youre_doing_well": summary.thing_youre_doing_well,
        "created_at": summary.created_at.isoformat(),
    }
