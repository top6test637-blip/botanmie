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
    print(f"Testing segment URL: {url}...")
    headers = {"User-Agent": get_random_user_agent()}
    connector = get_connector()
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.head(url, headers=headers, timeout=10) as response:
                print(f"HEAD Status: {response.status}")
                print(f"HEAD Headers: {dict(response.headers)}")
                
            async with session.get(url, headers=headers, timeout=10) as response:
                print(f"GET Status: {response.status}")
                data = await response.read()
                print(f"Downloaded: {len(data)} bytes")
                # Print first 20 bytes in hex
                print(f"First 20 bytes (hex): {data[:20].hex()}")
                # TS files always start with 0x47 (sync byte)
                if data and data[0] == 0x47:
                    print("🎉 SUCCESS: Valid MPEG-TS sync byte (0x47) found!")
                else:
                    print("⚠️ WARNING: Unexpected file header (not 0x47)")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
