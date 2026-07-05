import asyncio
import aiohttp
import json

async def test_domain(session, domain):
    dns_url = f"https://dns.google/resolve?name={domain}"
    try:
        async with session.get(dns_url, timeout=5) as resp:
            data = await resp.json()
            ips = []
            if "Answer" in data:
                for answer in data["Answer"]:
                    if answer["type"] == 1:
                        ips.append(answer["data"])
            if not ips:
                print(f"[{domain}] Failed to resolve IP")
                return None
            
            ip = ips[0]
            # Try requesting via IP or domain
            url = f"https://{domain}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
            async with session.get(url, headers=headers, ssl=False, timeout=8) as r:
                print(f"[{domain}] Status: {r.status}, HTML Length: {len(await r.text())}")
                return r.status
    except Exception as e:
        print(f"[{domain}] Error: {e}")
        return None

async def main():
    domains = ["witanime.pics", "witanime.xyz", "witanime.you", "witanime.life", "witanime.co", "witanime.net", "witanime.me", "witanime.cyou"]
    async with aiohttp.ClientSession() as session:
        tasks = [test_domain(session, d) for d in domains]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
