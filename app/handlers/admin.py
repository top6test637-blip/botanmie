from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from config import config
from app.database.models import BotAdmin
from app.utils.auth import is_admin
from app.utils.logging_config import logger

router = Router(name="admin")

@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message, db_session: AsyncSession):
    if message.from_user.id != config.SUPER_ADMIN_ID:
        await message.answer("❌ عذراً، هذا الأمر مخصص للمالك (Super Admin) فقط.")
        return
    
    target_user_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            target_user_id = int(args[1])
        except ValueError:
            await message.answer("❌ يرجى كتابة معرف المستخدم بشكل صحيح. مثال: `/addadmin 123456`", parse_mode="Markdown")
            return
    elif message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    else:
        await message.answer("❌ يرجى تحديد معرف المستخدم أو الرد على رسالة المستخدم باستخدام الأمر `/addadmin`", parse_mode="Markdown")
        return
    
    if target_user_id == config.SUPER_ADMIN_ID:
        await message.answer("⚠️ هذا المستخدم هو المالك بالفعل.")
        return
        
    stmt = select(BotAdmin).where(BotAdmin.user_id == target_user_id)
    res = await db_session.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        await message.answer("⚠️ هذا المستخدم مسؤول بالفعل في قاعدة البيانات.")
        return
        
    try:
        new_admin = BotAdmin(user_id=target_user_id, added_by=message.from_user.id)
        db_session.add(new_admin)
        await db_session.commit()
        logger.info(f"Admin added dynamically: User ID {target_user_id} by Super Admin")
        await message.answer(f"✅ تم إضافة المستخدم `{target_user_id}` كمسؤول بنجاح.", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error adding admin to database")
        await db_session.rollback()
        await message.answer(f"❌ فشل إضافة المسؤول إلى قاعدة البيانات: {e}")

@router.message(Command("deladmin"))
async def cmd_deladmin(message: Message, db_session: AsyncSession):
    if message.from_user.id != config.SUPER_ADMIN_ID:
        await message.answer("❌ عذراً، هذا الأمر مخصص للمالك (Super Admin) فقط.")
        return
        
    target_user_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            target_user_id = int(args[1])
        except ValueError:
            await message.answer("❌ يرجى كتابة معرف المستخدم بشكل صحيح. مثال: `/deladmin 123456`", parse_mode="Markdown")
            return
    elif message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    else:
        await message.answer("❌ يرجى تحديد معرف المستخدم أو الرد على رسالة المستخدم باستخدام الأمر `/deladmin`", parse_mode="Markdown")
        return
        
    stmt = select(BotAdmin).where(BotAdmin.user_id == target_user_id)
    res = await db_session.execute(stmt)
    admin_entry = res.scalar_one_or_none()
    if not admin_entry:
        await message.answer("⚠️ هذا المستخدم ليس مسؤولاً في قاعدة البيانات.")
        return
        
    try:
        await db_session.delete(admin_entry)
        await db_session.commit()
        logger.info(f"Admin removed dynamically: User ID {target_user_id} by Super Admin")
        await message.answer(f"✅ تم إزالة المستخدم `{target_user_id}` من قائمة المسؤولين.", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error removing admin from database")
        await db_session.rollback()
        await message.answer(f"❌ فشل إزالة المسؤول من قاعدة البيانات: {e}")

@router.message(F.photo)
async def handle_custom_thumbnail(message: Message, db_session: AsyncSession):
    authorized = await is_admin(message.from_user.id, db_session)
    if not authorized:
        await message.answer("❌ عذراً، لا تملك الصلاحية لتغيير الصورة المصغرة للفيديو.")
        return
        
    photo = message.photo[-1]
    
    # Ensure app/data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    thumb_path = data_dir / "custom_thumb.jpg"
    
    try:
        bot = message.bot
        file_info = await bot.get_file(photo.file_id)
        
        # Download from official Telegram servers directly to bypass local Bot API 404 issues
        import aiohttp
        public_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        logger.info(f"Downloading custom thumbnail from public Telegram API: {public_url}")
        
        success = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(public_url, ssl=False, timeout=30) as resp:
                    if resp.status == 200:
                        with open(thumb_path, "wb") as f:
                            f.write(await resp.read())
                        success = True
                    else:
                        logger.warning(f"Public thumbnail download returned status {resp.status}")
        except Exception as e:
            logger.warning(f"Failed downloading from public API: {e}")
            
        if not success:
            logger.info("Falling back to standard Bot API download_file method...")
            await bot.download_file(file_info.file_path, destination=str(thumb_path))
            
        logger.info(f"Custom video thumbnail updated by Admin (User ID: {message.from_user.id})")
        await message.answer("✅ تم تحديث الصورة المصغرة الافتراضية للفيديوهات بنجاح.")
    except Exception as e:
        logger.exception("Error downloading and saving custom thumbnail")
        await message.answer(f"❌ فشل تحديث الصورة المصغرة: {e}")
