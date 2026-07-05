import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def search_domain(domain, param):
    url = f"https://{domain}/?search_param={param}&s=Naruto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False, timeout=10) as r:
                print(f"[{domain}] Param: {param} -> Status: {r.status}")
                text = await r.text()
                soup = BeautifulSoup(text, "html.parser")
                anime_cards = soup.select(".anime-card-title a, .anime-title a, a[href*='/anime/']")
                print(f"[{domain}] Found {len(anime_cards)} potential links.")
                for idx, card in enumerate(anime_cards[:3]):
                    print(f"  [{idx}] {card.text.strip()} -> {card.get('href')}")
    except Exception as e:
        print(f"[{domain}] Param: {param} -> Error: {e}")

async def main():
    await search_domain("witanime.pics", "anime")
    await search_domain("witanime.pics", "animes")
    await search_domain("witanime.life", "anime")
    await search_domain("witanime.life", "animes")

if __name__ == "__main__":
    asyncio.run(main())
