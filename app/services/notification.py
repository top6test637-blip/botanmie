import html
from datetime import datetime, timezone
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
from config import config
from app.utils.logging_config import logger
from app.utils.deeplink import encode_deeplink_payload

NOTIFICATION_GROUP_ID = "-1003876536923"

async def broadcast_new_episode_notification(
    bot: Bot,
    anilist_id: int,
    anime_title: str,
    episode_num: str,
    image_url: Optional[str] = None,
    target_chat_id: Optional[str] = None
) -> bool:
    """Broadcasts a new episode notification card to the configured notification group/channel."""
    chat_id = target_chat_id or NOTIFICATION_GROUP_ID
    logger.info(f"Preparing new episode notification for '{anime_title}' Ep {episode_num} to {chat_id}")
    
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username if bot_info else "anime_wrbot"
        
        payload = encode_deeplink_payload(anilist_id, episode_num)
        deeplink_url = f"https://t.me/{bot_username}?start={payload}"
        
        chans = [c.strip() for c in (config.CHANNEL_USERNAME or "").replace(",", " ").split() if c.strip()]
        first_chan = chans[0] if chans else f"@{bot_username}"
        chan_url = f"https://t.me/{first_chan.lstrip('@')}"
        
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        caption_text = (
            f"🔥 <b>حلقة جديدة! | New Episode</b>\n\n"
            f"🎬 <b>{html.escape(anime_title)}</b>\n"
            f"🔢 <b>الحلقة:</b> {episode_num}\n"
            f"📅 <b>تاريخ الإضافة:</b> {today_str}\n\n"
            f"👇 <b>لالمشاهدة والتحميل عبر البوت:</b>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎥 مشاهدة الآن", url=deeplink_url)],
            [InlineKeyboardButton(text="📢 قناة البوت الرسمية", url=chan_url)]
        ])
        
        if image_url and image_url.startswith("http"):
            photo = URLInputFile(image_url)
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        logger.info(f"Successfully sent new episode notification for {anime_title} Ep {episode_num}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send new episode notification: {e}")
        return False
