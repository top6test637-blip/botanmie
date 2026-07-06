import asyncio
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup

DOMAINS = ['gogoanime3.cc', 'gogoanime.bz', 'gogoanime.ar', 'gogoanime.tel', 'gogoanime3.co', 'gogoanime.ws']

async def test_domain(domain):
    url = f"https://{domain}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with AsyncSession(impersonate="chrome120") as session:
            resp = await session.get(url, headers=headers, timeout=10)
            print(f"[{domain}] Status: {resp.status_code} | Length: {len(resp.text)}")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Check for recent release items
                items = soup.select("ul.items li")
                print(f"[{domain}] ul.items li count: {len(items)}")
                if len(items) > 0:
                    return domain, items
    except Exception as e:
        print(f"[{domain}] Error: {e}")
    return None, None

async def main():
    tasks = [test_domain(dom) for dom in DOMAINS]
    results = await asyncio.gather(*tasks)
    for dom, items in results:
        if items:
            print(f"SUCCESS on domain: {dom}")
            for item in items[:3]:
                name_tag = item.select_one("p.name a")
                print("  -", name_tag.text.strip() if name_tag else "N/A")

asyncio.run(main())
