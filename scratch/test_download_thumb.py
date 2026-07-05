import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import aiohttp
from aiogram import Bot
from config import config

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    file_id = "AgACAgQAAxkBAAIIp2pKIpnZzFqw8HMq1mIW2ORAox17AAL0DmsbSHRQUq2_ZldCSYfGAQADAgADeQADPAQ"
    try:
        print("Getting file info...")
        file_info = await bot.get_file(file_id)
        print(f"File Path: {file_info.file_path}")
        
        # Test 1: Download via api.telegram.org
        telegram_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_info.file_path}"
        print(f"Testing api.telegram.org download URL: {telegram_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(telegram_url) as resp:
                print(f"api.telegram.org status: {resp.status}")
                if resp.status == 200:
                    data = await resp.read()
                    print(f"Success! Downloaded {len(data)} bytes.")
                    
        # Test 2: Download via local Bot API
        local_url = f"http://telegram-bot-api.railway.internal:8081/file/bot{config.BOT_TOKEN}/{file_info.file_path}"
        print(f"Testing local Bot API download URL: {local_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(local_url) as resp:
                print(f"local Bot API status: {resp.status}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

asyncio.run(main())
