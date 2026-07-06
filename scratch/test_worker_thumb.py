import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import aiohttp
from aiogram import Bot
from config import config
from app.services.worker import prepare_telegram_thumbnail
from aiogram.types import BufferedInputFile

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    file_id = "AgACAgQAAxkBAAIOnmpLGJvraHFialdG8yDK9GqbEkEWAAJbDWsbVTBRUkfS2Q5sncT-AQADAgADdwADPAQ"
    raw_path = "scratch/test_raw_thumb.jpg"
    optimized_path = "scratch/test_custom_thumb_320.jpg"
    
    if os.path.exists(raw_path): os.remove(raw_path)
    if os.path.exists(optimized_path): os.remove(optimized_path)
    
    try:
        print("Fetching file info from Telegram...")
        file_info = await bot.get_file(file_id)
        if file_info and file_info.file_path:
            file_path = file_info.file_path
            # Extract standard relative path if Bot API server is running in local mode and returns absolute disk path
            if "/" in file_path:
                for prefix in ["photos/", "documents/", "video/", "voice/", "stickers/", "music/"]:
                    if prefix in file_path:
                        file_path = prefix + file_path.split(prefix, 1)[1]
                        break
            
            print("Telegram File Path:", file_path)
            dl_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
            print("Direct Download URL:", dl_url)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(dl_url, timeout=30) as resp:
                    print("Download HTTP Status:", resp.status)
                    if resp.status == 200:
                        with open(raw_path, "wb") as f:
                            f.write(await resp.read())
                        print("Saved raw thumbnail, size:", os.path.getsize(raw_path))
                    else:
                        print("Download failed!")
                        
            if os.path.exists(raw_path) and os.path.getsize(raw_path) > 0:
                success = prepare_telegram_thumbnail(raw_path, optimized_path)
                print("prepare_telegram_thumbnail result:", success)
                if success and os.path.exists(optimized_path):
                    print("Success! Optimized thumbnail size:", os.path.getsize(optimized_path))
                else:
                    print("Thumbnail preparation failed.")
    except Exception as e:
        print("Error:", e)
        
    await bot.session.close()

asyncio.run(main())
