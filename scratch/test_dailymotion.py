import asyncio
import aiohttp

async def main():
    video_id = "x91nnhq"
    url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.dailymotion.com/"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            print("Error details:", data.get("error"))

asyncio.run(main())
