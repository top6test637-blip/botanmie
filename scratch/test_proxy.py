import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector

async def test():
    proxy = "socks5://yzjbjptm:mxykfsyptk4x@38.154.203.95:5863"
    connector = ProxyConnector.from_url(proxy)
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("https://httpbin.org/ip", timeout=5) as resp:
                print("Status:", resp.status)
                print("JSON:", await resp.json())
    except Exception as e:
        print("Failed:", e)

asyncio.run(test())
