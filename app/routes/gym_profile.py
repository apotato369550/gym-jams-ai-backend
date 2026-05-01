from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import User, GymProfile
from app.db.session import get_db

router = APIRouter()


@router.get("/gym_profile")
async def get_gym_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GymProfile).where(GymProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gym profile not found")
    return {
        "archetype": profile.archetype,
        "read_description": profile.read_description,
        "modalities_youll_enjoy": profile.modalities_youll_enjoy,
        "first_week_suggestion": profile.first_week_suggestion,
        "watch_out_for": profile.watch_out_for,
        "created_at": profile.created_at.isoformat(),
    }
