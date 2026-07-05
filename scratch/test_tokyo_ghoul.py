import asyncio
import sys
from pathlib import Path

# Configure console output encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

project_root = Path("c:/Users/monsm/OneDrive/Desktop/BOT")
sys.path.append(str(project_root))

from app.services.scraper import get_download_links_scraper, get_m3u8_from_embed, decrypt_resource
from config import config
config.PROXY_URL = None
from app.utils.user_agents import get_random_user_agent
from app.services.anilist import get_connector
import aiohttp
import re
from bs4 import BeautifulSoup
import json
import base64

async def test_scraping():
    html_file = "scratch/tokyo_ghoul_page.html"
    print(f"Testing watch page scraping from local file: {html_file}")
    
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
        
    # Find server labels/names inside DOM
    soup = BeautifulSoup(html, "html.parser")
    servers = []
    for sel in [
        "#episode-servers li", ".episode-servers li", "ul.servers-list li", ".servers-list li", 
        "#watch-servers li", "li.server", "#episode-servers a", ".episode-servers a", 
        "#watch-servers a", "ul.servers-list a", ".servers-list a"
    ]:
        found = soup.select(sel)
        if found:
            servers = found
            break
    
    server_names = [s.text.strip().lower() for s in servers]
    print(f"Found {len(servers)} servers: {server_names}")
    
    # Extract player registry keys
    zx_match = re.search(r'var _zX="([^"]+)"', html)
    zk_match = re.search(r'var _zK="([^"]+)"', html)
    
    if not zx_match or not zk_match:
        print("FAILED: var _zX or _zK not found!")
        return
        
    resources = json.loads(base64.b64decode(zx_match.group(1)).decode("utf-8"))
    configs = json.loads(base64.b64decode(zk_match.group(1)).decode("utf-8"))
    print(f"Decoded {len(resources)} resources.")
    
    connector = get_connector()
    async with aiohttp.ClientSession(connector=connector) as session:
        for idx, (res, conf) in enumerate(zip(resources, configs)):
            s_name = server_names[idx] if idx < len(server_names) else f"server-{idx}"
            embed_url = decrypt_resource(res, conf)
            print(f"\n[{idx}] Server: '{s_name}' -> Embed URL: '{embed_url}'")
            if embed_url:
                try:
                    res_m3u8 = await get_m3u8_from_embed(embed_url, session, referer="https://witanime.pics/episode/tokyo-ghoulre-2nd-season-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d8%a9-1/")
                    print(f"    -> Resolved: {res_m3u8}")
                except Exception as e:
                    print(f"    -> Error resolving: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraping())
