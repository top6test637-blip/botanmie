import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def main():
    url = "https://subsplease.org/rss/?r=1080"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://gogoanime3.cc/"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print("Status:", resp.status)
            html_text = await resp.text()
            print("Length of HTML:", len(html_text))
            print("HTML Content:")
            print(html_text)
            
            soup = BeautifulSoup(html_text, "html.parser")
            items = soup.select("item")
            print("Number of items found:", len(items))
            for item in items[:5]:
                title_tag = item.select_one("title")
                link_tag = item.select_one("link")
                
                title = title_tag.text.strip() if title_tag else "N/A"
                play_url = link_tag.text.strip() if link_tag else "N/A"
                
                print(f"- Title: {title} | URL: {play_url}")

asyncio.run(main())
