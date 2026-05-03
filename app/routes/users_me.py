from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import User
from app.db.session import get_db

router = APIRouter()


class UpdateNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get("/users/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/users/me", status_code=status.HTTP_200_OK)
async def update_me(
    body: UpdateNameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.name = body.name
    db.add(current_user)
    await db.commit()
    return {"user_id": current_user.id, "name": current_user.name}
