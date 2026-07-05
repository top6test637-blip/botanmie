import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import base64

async def test_episodes():
    slug = "boruto-naruto-next-generations"
    url = f"https://witanime.life/anime/{slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            print(f"Anime Page Status: {r.status}")
            text = await r.text()
            soup = BeautifulSoup(text, "html.parser")
            
            # Find episodes list
            eps = []
            # In WitAnime, it's inside div.episodes-card-title a
            for a in soup.select(".episodes-card-title a"):
                eps.append(a.get("href"))
            print(f"Found {len(eps)} episode links.")
            if eps:
                print(f"Sample ep link: {eps[0]}")
                # Test scraping watch page of first episode
                async with session.get(eps[0], headers=headers, ssl=False) as ep_r:
                    print(f"Episode Page Status: {ep_r.status}")
                    ep_text = await ep_r.text()
                    import re
                    zx_match = re.search(r'var _zX="([^"]+)"', ep_text)
                    zk_match = re.search(r'var _zK="([^"]+)"', ep_text)
                    if zx_match and zk_match:
                        print("Found _zX and _zK registries!")
                        res = json.loads(base64.b64decode(zx_match.group(1)).decode("utf-8"))
                        print(f"Registry length: {len(res)}")
                    else:
                        print("Did not find registries.")

if __name__ == "__main__":
    asyncio.run(test_episodes())
