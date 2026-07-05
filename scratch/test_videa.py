import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

async def main():
    url = "https://videa.hu/player/xml?v=x2WVLBeHDqdE0pP7"
    print(f"Fetching videa XML: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://videa.hu/player?v=x2WVLBeHDqdE0pP7"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            
            # Save XML
            with open("scratch/videa_player.xml", "w", encoding="utf-8") as f:
                f.write(text)
            print("Saved XML to scratch/videa_player.xml")
            
            # Search for MP4 matches
            print("\nSearching for MP4 URLs...")
            mp4_matches = re.findall(r'https?://[^\s"\']+\.mp4[^\s"\']*', text)
            print(f"Found {len(mp4_matches)} raw .mp4 matches:")
            for m in mp4_matches[:5]:
                print(f"  - {m}")
                
            # Search for other video formats
            print("\nSearching for any URLs containing video or stream:")
            matches = re.findall(r'https?://[^\s"\']+(?:video|stream|mp4|m3u8)[^\s"\']*', text)
            print(f"Found {len(matches)} potential stream URLs:")
            for m in matches[:5]:
                print(f"  - {m}")

if __name__ == "__main__":
    asyncio.run(main())
