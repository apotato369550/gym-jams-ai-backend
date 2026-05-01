from datetime import datetime, timedelta
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage

CHAT_TTL_HOURS = 24


async def expire_old_messages(db: AsyncSession, user_id: int) -> None:
    cutoff = datetime.utcnow() - timedelta(hours=CHAT_TTL_HOURS)
    await db.execute(
        update(ChatMessage)
        .where(
            ChatMessage.user_id == user_id,
            ChatMessage.deleted_at.is_(None),
            ChatMessage.created_at < cutoff,
        )
        .values(deleted_at=datetime.utcnow())
    )


async def save_turn(db: AsyncSession, user_id: int, user_content: str, assistant_content: str) -> None:
    await expire_old_messages(db, user_id)
    db.add(ChatMessage(user_id=user_id, role="user", content=user_content))
    db.add(ChatMessage(user_id=user_id, role="assistant", content=assistant_content))
    await db.commit()
