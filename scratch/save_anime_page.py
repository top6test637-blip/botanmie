import asyncio
import aiohttp

async def main():
    url = "https://witanime.life/anime/boruto-naruto-next-generations/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            text = await r.text()
            with open("scratch/anime_page.html", "w", encoding="utf-8") as f:
                f.write(text)
            print("Saved anime page to scratch/anime_page.html")

if __name__ == "__main__":
    asyncio.run(main())
