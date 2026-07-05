import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def inspect(domain):
    url = f"https://{domain}/?search_param=anime&s=Naruto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            text = await r.text()
            soup = BeautifulSoup(text, "html.parser")
            print(f"[{domain}] Title: {soup.title.text if soup.title else 'No Title'}")
            print(f"[{domain}] Snippet: {text[:400]}")

async def main():
    await inspect("witanime.life")
    await inspect("witanime.net")

if __name__ == "__main__":
    asyncio.run(main())
