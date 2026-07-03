from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import BotAdmin
from config import config

async def is_admin(user_id: int, db_session: AsyncSession) -> bool:
    """Checks if a user is the Super Admin or a dynamically added admin in the database."""
    if user_id == config.SUPER_ADMIN_ID:
        return True
    
    stmt = select(BotAdmin).where(BotAdmin.user_id == user_id)
    res = await db_session.execute(stmt)
    return res.scalar_one_or_none() is not None
