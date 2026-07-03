import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to path
project_root = Path("c:/Users/monsm/OneDrive/Desktop/BOT")
sys.path.append(str(project_root))

from config import config
from app.utils.user_agents import get_random_user_agent
from app.services.anilist import get_connector

async def main():
    url = "https://p16-ad-sg.ibyteimg.com/obj/ad-site-i18n/202603235d0d4c701c0efcd54d97b6d1"
    headers = {"User-Agent": get_random_user_agent()}
    connector = get_connector()
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                data = await response.read()
                print(f"Downloaded: {len(data)} bytes")
                
                # Search for 0x47 sync bytes that repeat every 188 bytes
                for offset in range(len(data) - 188 * 3):
                    if data[offset] == 0x47:
                        # Check if next 3 segments also align at 188 byte boundaries
                        if data[offset + 188] == 0x47 and data[offset + 188 * 2] == 0x47 and data[offset + 188 * 3] == 0x47:
                            print(f"FOUND ALIGNMENT AT OFFSET: {offset}")
                            print(f"First 10 bytes: {data[offset:offset+10].hex()}")
                            cleaned_path = Path("c:/Users/monsm/OneDrive/Desktop/BOT/scratch/segment_cleaned.ts")
                            with open(cleaned_path, "wb") as f:
                                f.write(data[offset:])
                            print(f"Saved: {cleaned_path}")
                            break
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
