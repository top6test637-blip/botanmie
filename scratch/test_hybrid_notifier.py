import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.scraper import fetch_latest_site_episodes

async def main():
    print("Executing fetch_latest_site_episodes...")
    episodes = await fetch_latest_site_episodes()
    print("Results length:", len(episodes))
    for ep in episodes[:5]:
        print("- Title:", ep["anime_title"], "| Ep:", ep["episode_num"])

asyncio.run(main())
