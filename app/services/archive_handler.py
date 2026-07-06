import html
from typing import Optional, Dict, Any
from aiogram import Bot
from sqlalchemy.future import select
from app.database.models import TelegramFileCache
from app.utils.logging_config import logger
from config import config

LIBRARY_GROUP_ID = "-1003757034229"

async def get_archived_telegram_file(
    db_session_factory,
    anilist_id: int,
    ep_number: str,
    quality: str
) -> Optional[Dict[str, Any]]:
    """Checks the persistent TelegramFileCache for a pre-indexed archived file_id."""
    async with db_session_factory() as session:
        stmt = select(TelegramFileCache).where(
            TelegramFileCache.anilist_id == anilist_id,
            TelegramFileCache.ep_number == ep_number,
            TelegramFileCache.quality == quality
        )
        res = await session.execute(stmt)
        cached = res.scalar_one_or_none()
        if cached:
            logger.info(f"Archive Hit: Resolved anilist_id={anilist_id}, ep={ep_number}, quality={quality} -> file_id={cached.file_id}")
            return {
                "file_id": cached.file_id,
                "file_size": cached.file_size
            }
    return None

async def mirror_to_archive_library(
    bot: Bot,
    db_session_factory,
    anilist_id: int,
    anime_title: str,
    ep_number: str,
    quality: str,
    file_id: str,
    library_group_id: str = LIBRARY_GROUP_ID
) -> bool:
    """Mirrors a newly uploaded video file to the library group and indexes it into TelegramFileCache."""
    try:
        caption = (
            f"📦 <b>أرشيف المكتبة | Library Archive</b>\n\n"
            f"🎬 <b>{html.escape(anime_title)}</b>\n"
            f"🔢 <b>الحلقة:</b> {ep_number}\n"
            f"⚙️ <b>الجودة:</b> {quality}\n"
            f"🆔 <b>AniList ID:</b> {anilist_id}"
        )
        
        sent_msg = await bot.send_video(
            chat_id=library_group_id,
            video=file_id,
            caption=caption,
            parse_mode="HTML"
        )
        
        archived_file_id = sent_msg.video.file_id if sent_msg and sent_msg.video else file_id
        
        async with db_session_factory() as session:
            stmt = select(TelegramFileCache).where(
                TelegramFileCache.anilist_id == anilist_id,
                TelegramFileCache.ep_number == ep_number,
                TelegramFileCache.quality == quality
            )
            res = await session.execute(stmt)
            entry = res.scalar_one_or_none()
            
            if not entry:
                entry = TelegramFileCache(
                    anilist_id=anilist_id,
                    ep_number=ep_number,
                    quality=quality,
                    file_id=archived_file_id,
                    file_size=sent_msg.video.file_size / (1024 * 1024) if sent_msg and sent_msg.video and sent_msg.video.file_size else 0.0
                )
                session.add(entry)
            else:
                entry.file_id = archived_file_id
            await session.commit()
            
        logger.info(f"Successfully archived & indexed {anime_title} Ep {ep_number} [{quality}] in library group")
        return True
    except Exception as e:
        logger.warning(f"Failed to mirror video to archive library group: {e}")
        return False
