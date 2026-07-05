import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import aiohttp
import base64
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

WITANIME_DOMAIN = "witanime.life"

async def test_search(query):
    url = f"https://{WITANIME_DOMAIN}/?search_param=animes&s={quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://{WITANIME_DOMAIN}/"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            print(f"[SEARCH '{query}'] Status: {r.status}")
            text = await r.text()
            soup = BeautifulSoup(text, "html.parser")
            details = soup.select(".cat-post-details h2 a")
            print(f"  Found {len(details)} results")
            
            seen_slugs = set()
            results = []
            for a in details:
                href = a.get("href")
                if "/anime/" in href:
                    slug = href.split("/anime/")[1].strip("/")
                    if slug not in seen_slugs:
                        seen_slugs.add(slug)
                        results.append({"title": a.text.strip(), "slug": slug})
                elif "/episode/" in href:
                    # Try to extract parent slug from episode href
                    match = re.search(r'/anime/([^/"]+)/', text)
                    # For now just show the episode link
                    results.append({"title": a.text.strip(), "slug": f"episode:{href.split('/episode/')[1].strip('/')}"})
            
            for r_item in results[:5]:
                print(f"  -> {r_item['title'][:60]} | slug: {r_item['slug']}")
            return results

async def test_episodes(slug):
    url = f"https://{WITANIME_DOMAIN}/anime/{slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://{WITANIME_DOMAIN}/"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as r:
            print(f"\n[EPISODES '{slug}'] Status: {r.status}")
            html = await r.text()
            
            # Try encodedEpisodeData first
            encoded_match = re.search(r"var encodedEpisodeData = '([^']+)';", html)
            if encoded_match:
                decoded = base64.b64decode(encoded_match.group(1)).decode("utf-8")
                episodes = json.loads(decoded)
                print(f"  encodedEpisodeData: {len(episodes)} episodes")
                if episodes:
                    print(f"  First: ep {episodes[0].get('number')} -> {episodes[0].get('url')[:80]}")
                    print(f"  Last:  ep {episodes[-1].get('number')} -> {episodes[-1].get('url')[:80]}")
                return
            
            # Try processedEpisodeData
            match = re.search(r"var processedEpisodeData = '([^']+)';", html)
            if match:
                print("  processedEpisodeData found (encrypted)")
            else:
                print("  No episode data found at all!")

async def main():
    # Test searches
    await test_search("Frieren")
    await test_search("ONE PIECE")
    await test_search("Naruto")
    
    # Test episode listing for a known slug
    results = await test_search("Frieren")
    if results:
        # Find first /anime/ slug
        for r in results:
            if not r["slug"].startswith("episode:"):
                await test_episodes(r["slug"])
                break

if __name__ == "__main__":
    asyncio.run(main())
