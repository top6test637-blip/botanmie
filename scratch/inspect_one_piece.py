import asyncio
import aiohttp
import sys
import re
from pathlib import Path

async def main():
    slug = "one-piece"
    url = f"https://witanime.pics/anime/{slug}/page/2/"
    print(f"Requesting page 2: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://witanime.pics/"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                html = await response.text()
                match = re.search(r"var processedEpisodeData = '([^']+)';", html)
                if match:
                    from app.services.scraper import decrypt_episodes
                    episodes = decrypt_episodes(match.group(1))
                    print(f"Decrypted {len(episodes)} episodes from page 2")
                else:
                    print("No processedEpisodeData on page 2")

if __name__ == "__main__":
    asyncio.run(main())
