import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def search_domain(domain):
    url = f"https://{domain}/?search_param=anime&s=Naruto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False, timeout=10) as r:
                print(f"[{domain}] Status: {r.status}")
                text = await r.text()
                soup = BeautifulSoup(text, "html.parser")
                # Look for some anime titles
                anime_cards = soup.select(".anime-card-title a, .anime-title a, a[href*='/anime/']")
                print(f"[{domain}] Found {len(anime_cards)} potential links.")
                for idx, card in enumerate(anime_cards[:3]):
                    print(f"  [{idx}] {card.text.strip()} -> {card.get('href')}")
    except Exception as e:
        print(f"[{domain}] Error: {e}")

async def main():
    await search_domain("witanime.life")
    await search_domain("witanime.net")

if __name__ == "__main__":
    asyncio.run(main())
