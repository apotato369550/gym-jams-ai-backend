from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import User, UserProfile as UserProfileModel
from app.db.session import get_db
from app.schemas.user_profile import UserProfile

router = APIRouter()


@router.get("/user_profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalars().first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return {
        "name": current_user.name,
        "age_range": profile.age_range,
        "height_cm": float(profile.height_cm),
        "weight_kg": float(profile.weight_kg),
        "location": profile.location,
        "activity_level": profile.activity_level,
        "goal": profile.goal,
        "intent": profile.intent,
        "constraints": profile.constraints,
    }


@router.post("/user_profile", status_code=status.HTTP_200_OK)
async def save_user_profile(
    body: UserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalars().first()

    if profile is None:
        profile = UserProfileModel(user_id=current_user.id)
        db.add(profile)

    profile.age_range = body.age_range
    profile.height_cm = body.height_cm
    profile.weight_kg = body.weight_kg
    profile.location = body.location
    profile.activity_level = body.activity_level
    profile.goal = body.goal
    profile.intent = body.intent
    profile.constraints = body.constraints

    await db.commit()
    await db.refresh(profile)
    return {"message": "Profile saved", "user_id": current_user.id}
