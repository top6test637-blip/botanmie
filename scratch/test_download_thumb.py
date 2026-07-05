import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from aiogram import Bot
from config import config

async def main():
    # Simulate a local bot (uses local API server if configured)
    from aiogram.client.telegram import TelegramAPIServer
    local_api = TelegramAPIServer.from_base("http://telegram-bot-api.railway.internal:8081")
    
    # We initialize local_bot like the main bot inside the container
    local_bot = Bot(token=config.BOT_TOKEN, api_server=local_api)
    file_id = "AgACAgQAAxkBAAIIp2pKIpnZzFqw8HMq1mIW2ORAox17AAL0DmsbSHRQUq2_ZldCSYfGAQADAgADeQADPAQ"
    
    try:
        print("Getting file info from local bot...")
        # In a real environment, this might return a local path or fail/timeout on local machine
        # But we want to see if we can get file info using a temporary cloud Bot instead:
        print("Initializing temporary cloud Bot...")
        async with Bot(token=config.BOT_TOKEN) as cloud_bot:
            print("Getting file info from cloud bot...")
            file_info = await cloud_bot.get_file(file_id)
            print(f"Cloud File Path: {file_info.file_path}")
            
            # Download file using cloud bot
            dest_path = "scratch/temp_thumb.jpg"
            if os.path.exists(dest_path):
                os.remove(dest_path)
            print("Downloading file using cloud_bot.download_file...")
            await cloud_bot.download_file(file_info.file_path, destination=dest_path)
            print(f"Download complete! File exists: {os.path.exists(dest_path)}, size: {os.path.getsize(dest_path) if os.path.exists(dest_path) else 0} bytes")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await local_bot.session.close()

asyncio.run(main())
