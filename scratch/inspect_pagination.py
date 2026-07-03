import asyncio
import aiohttp
import sys
import re
from pathlib import Path

project_root = Path("c:/Users/monsm/OneDrive/Desktop/BOT")
sys.path.append(str(project_root))

from app.services.scraper import decrypt_episodes

async def fetch_page(url, page_num):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://witanime.pics/"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Page {page_num} returned status {response.status}")
                return None
            html = await response.text()
            match = re.search(r"var processedEpisodeData = '([^']+)';", html)
            if match:
                episodes = decrypt_episodes(match.group(1))
                print(f"Page {page_num} ({url}): found {len(episodes)} episodes")
                if episodes:
                    print(f"  First ep: {episodes[0].get('number')} | Last ep: {episodes[-1].get('number')}")
                return episodes
            else:
                print(f"Page {page_num} ({url}): no processedEpisodeData found")
                return []

async def main():
    # Let's try pages 1, 2, 3, 4, 5 for one-piece
    tasks = []
    # page 1 is the main URL
    tasks.append(fetch_page("https://witanime.pics/anime/one-piece/", 1))
    for p in range(2, 6):
        tasks.append(fetch_page(f"https://witanime.pics/anime/one-piece/page/{p}/", p))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
