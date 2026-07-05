from aiogram.types import CallbackQuery
from app.utils.logging_config import logger

async def safe_answer(callback: CallbackQuery, *args, **kwargs):
    """
    Safely answers a callback query to prevent TelegramBadRequest or query expiration issues.
    Logs a warning if it fails, but does not raise an exception, preventing dispatcher crashes.
    """
    try:
        await callback.answer(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to answer callback query safely: {e}")
