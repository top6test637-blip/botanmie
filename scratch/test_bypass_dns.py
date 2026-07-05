import asyncio
import aiohttp
import json

async def main():
    domain = "witanime.pics"
    dns_url = f"https://dns.google/resolve?name={domain}"
    print(f"Resolving {domain} via Google HTTP DNS: {dns_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(dns_url) as resp:
            data = await resp.json()
            ips = []
            if "Answer" in data:
                for answer in data["Answer"]:
                    if answer["type"] == 1: # A record
                        ips.append(answer["data"])
            
            print(f"Resolved IPs: {ips}")
            if not ips:
                print("No A records found.")
                return
            target_ip = ips[0]
                
    class CustomResolver:
        async def resolve(self, host, port=0, family=0):
            if "witanime" in host:
                return [{
                    "hostname": host,
                    "host": target_ip,
                    "port": port,
                    "family": family,
                    "proto": 0,
                    "flags": 0
                }]
            resolver = aiohttp.DefaultResolver()
            return await resolver.resolve(host, port, family)

        def close(self):
            pass

    connector = aiohttp.TCPConnector(resolver=CustomResolver())
    async with aiohttp.ClientSession(connector=connector) as session:
        url = "https://witanime.pics/episode/tokyo-ghoulre-2nd-season-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d8%a9-1/"
        print(f"Requesting watch page via custom resolver: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with session.get(url, headers=headers, ssl=False, timeout=10) as page_resp:
                print(f"Response Status: {page_resp.status}")
                text = await page_resp.text()
                print(f"HTML Length: {len(text)}")
                with open("scratch/tokyo_ghoul_page.html", "w", encoding="utf-8") as f:
                    f.write(text)
                print("Saved page to scratch/tokyo_ghoul_page.html")

if __name__ == "__main__":
    asyncio.run(main())
