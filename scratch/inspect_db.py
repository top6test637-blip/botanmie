import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.database.models import SearchCache

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(SearchCache).where(SearchCache.query_text == "بلاك كلوفر")
        res = await session.execute(stmt)
        entries = res.scalars().all()
        print(f"Total entries for 'بلاك كلوفر' in SearchCache: {len(entries)}")
        for i, entry in enumerate(entries):
            print(f"{i+1}. ID: {entry.anilist_id}, Title (EN): {entry.title_english}, Title (Romaji): {entry.title_romaji}")

if __name__ == "__main__":
    asyncio.run(main())
