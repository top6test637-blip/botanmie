import asyncio
import aiohttp

async def save_html(domain):
    url = f"https://{domain}/?search_param=anime&s=Naruto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            text = await r.text()
            filename = f"scratch/{domain}_search.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved {domain} to {filename}")

async def main():
    await save_html("witanime.life")

if __name__ == "__main__":
    asyncio.run(main())
