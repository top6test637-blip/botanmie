import re
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from config import config
from app.utils.user_agents import get_random_user_agent
from app.services.anilist import get_connector
from app.utils.logging_config import logger

class ScraperError(Exception):
    """Base exception for scraping operations."""
    pass

async def get_html(url: str, session: aiohttp.ClientSession) -> str:
    """Fetches HTML content with custom headers and optional proxy."""
    headers = {"User-Agent": get_random_user_agent()}
    proxy_str = f" via proxy {config.PROXY_URL}" if config.PROXY_URL else ""
    logger.info(f"Scraping page: {url}{proxy_str}")
    
    # Log proxy details separately to meet requirement
    if config.PROXY_URL:
        logger.info(f"Proxy used for request: {config.PROXY_URL}")
        
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                return await response.text()
            raise ScraperError(f"HTTP error {response.status} fetching {url}")
    except Exception as e:
        logger.exception(f"Error in process while fetching HTML from {url}")
        if not isinstance(e, ScraperError):
            raise ScraperError(f"Connection failed: {e}") from e
        raise

async def get_m3u8_from_embed(embed_url: str, session: aiohttp.ClientSession) -> Optional[str]:
    """Fetches the player embed page and extracts the .m3u8 playlist URL."""
    headers = {"User-Agent": get_random_user_agent(), "Referer": "https://anineko.to/"}
    proxy_str = f" via proxy {config.PROXY_URL}" if config.PROXY_URL else ""
    logger.info(f"Scraping page: {embed_url}{proxy_str}")
    
    if config.PROXY_URL:
        logger.info(f"Proxy used for request: {config.PROXY_URL}")
        
    try:
        async with session.get(embed_url, headers=headers, timeout=10) as response:
            if response.status != 200:
                logger.error(f"Error in process: embed page returned status {response.status}")
                return None
            text = await response.text()
            
            # Match first .m3u8 link in script variables or elements
            match = re.search(r'const\s+src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', text)
            if not match:
                match = re.search(r'src\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', text)
            if not match:
                match = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', text)
                
            if match:
                m3u8_url = match.group(1)
                logger.info(f"Resolved master .m3u8 playlist: {m3u8_url}")
                return m3u8_url
    except Exception:
        logger.exception(f"Error in process while resolving embed URL {embed_url}")
    return None

async def parse_m3u8_qualities(master_url: str, session: aiohttp.ClientSession) -> Dict[str, str]:
    """Parses master .m3u8 playlist to extract quality variant URLs."""
    headers = {"User-Agent": get_random_user_agent(), "Referer": "https://vivibebe.site/"}
    proxy_str = f" via proxy {config.PROXY_URL}" if config.PROXY_URL else ""
    logger.info(f"Scraping page: {master_url}{proxy_str}")
    
    if config.PROXY_URL:
        logger.info(f"Proxy used for request: {config.PROXY_URL}")
        
    qualities = {}
    try:
        async with session.get(master_url, headers=headers, timeout=10) as response:
            if response.status != 200:
                logger.error(f"Error in process: master playlist returned status {response.status}")
                return {}
            # Read as raw bytes to safely handle potential PNG wrapping
            data = await response.read()
            if data.startswith(b"\x89PNG"):
                data = data[252:]
            text = data.decode("utf-8")
            
            if "#EXTINF:" in text:
                # Direct playlist, not master
                logger.info("Playlist is a direct single-quality variant HLS stream.")
                return {"720p": master_url}
                
            from urllib.parse import urljoin
            lines = text.splitlines()
            current_info = None
            for line in lines:
                line = line.strip()
                if line.startswith("#EXT-X-STREAM-INF:"):
                    # Resolve RESOLUTION or NAME attribute
                    match_res = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    match_name = re.search(r'NAME="([^"]+)"', line)
                    if match_name:
                        current_info = match_name.group(1).lower()
                    elif match_res:
                        height = match_res.group(1).split("x")[1]
                        current_info = f"{height}p"
                elif line and not line.startswith("#"):
                    if current_info:
                        variant_url = urljoin(master_url, line)
                        qualities[current_info] = variant_url
                        current_info = None
                        
            logger.info(f"Parsed qualities from master playlist: {list(qualities.keys())}")
    except Exception:
        logger.exception(f"Error in process while parsing master playlist {master_url}")
    return qualities

async def search_anime_scraper(title: str) -> List[Dict[str, Any]]:
    """
    Searches for anime on AniNeko.
    Returns a list of dictionaries with title and slug.
    """
    logger.info(f"Starting search for anime: {title}")
    if config.MOCK_MODE:
        logger.info("[MOCK MODE] Simulating search result on Gogoanime.")
        return [
            {
                "title": f"{title} (TV)",
                "slug": "one-piece-tv" if "piece" in title.lower() or "luffy" in title.lower() else "mock-anime-slug"
            }
        ]

    search_url = f"{config.GOGOANIME_BASE_URL}/browser?keyword={title}"
    connector = get_connector()
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            html = await get_html(search_url, session)
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all watch links that are not episodes
            links = soup.find_all("a", href=lambda h: h and h.startswith("/watch/") and "/ep-" not in h)
            results = []
            seen = set()
            for link in links:
                href = link.get("href")
                slug = href.replace("/watch/", "").strip("/")
                if slug in seen or not slug:
                    continue
                title_text = link.text.strip()
                if not title_text or "CC" in title_text:
                    # Look for other links with same href to get a clean title
                    other_links = [l.text.strip() for l in links if l.get("href") == href and l.text.strip() and "CC" not in l.text]
                    if other_links:
                        title_text = other_links[0]
                    else:
                        continue
                seen.add(slug)
                results.append({"title": title_text, "slug": slug})
                
            logger.info(f"Found {len(results)} search results on AniNeko.")
            return results
        except Exception:
            logger.exception("Error in process while searching anime scraper")
            return []

async def get_episodes_scraper(anime_slug: str) -> List[Dict[str, Any]]:
    """
    Retrieves the list of episodes for an anime slug from AniNeko details page.
    """
    logger.info(f"Fetching episodes list for anime slug: {anime_slug}")
    if config.MOCK_MODE:
        logger.info("[MOCK MODE] Generating mock episodes list.")
        return [
            {
                "ep_number": str(i),
                "play_url": f"https://mock-play-page.com/{anime_slug}-episode-{i}"
            }
            for i in range(1, 13)
        ]

    anime_url = f"{config.GOGOANIME_BASE_URL}/watch/{anime_slug}"
    connector = get_connector()
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            html = await get_html(anime_url, session)
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all episode watch links: /watch/anime_slug/ep-X
            prefix = f"/watch/{anime_slug}/ep-"
            links = soup.find_all("a", href=lambda h: h and h.startswith(prefix))
            
            episodes = []
            seen_eps = set()
            for link in links:
                href = link.get("href")
                ep_str = href.replace(prefix, "").strip("/")
                if ep_str in seen_eps:
                    continue
                seen_eps.add(ep_str)
                full_play_url = f"{config.GOGOANIME_BASE_URL}{href}" if href.startswith("/") else href
                episodes.append({
                    "ep_number": ep_str,
                    "play_url": full_play_url
                })
                
            # Numeric sort key
            def get_ep_num(ep):
                try:
                    return float(ep["ep_number"])
                except ValueError:
                    return 999999.0
            episodes.sort(key=get_ep_num)
            
            logger.info(f"Parsed {len(episodes)} episodes for anime slug: {anime_slug}")
            return episodes
        except Exception:
            logger.exception(f"Error in process while getting episodes for {anime_slug}")
            return []

async def get_download_links_scraper(play_url: str) -> Dict[str, str]:
    """
    Parses the watch page, extracts the server embed links,
    resolves the master playlists, and returns variant playlist URLs for qualities.
    """
    logger.info(f"Scraping download links from watch page: {play_url}")
    if config.MOCK_MODE:
        logger.info("[MOCK MODE] Returning mock direct download video paths.")
        return {
            "1080p": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_30MB.mp4?mock_size=2500000000",
            "720p": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_10MB.mp4?mock_size=2200000000",
            "480p": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_5MB.mp4?mock_size=45000000",
            "360p": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_2MB.mp4?mock_size=2000000"
        }

    connector = get_connector()
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            html = await get_html(play_url, session)
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all video buttons with class server-video or inside .server-items
            buttons = soup.select("button.server-video") or soup.select(".server-items button")
            
            embed_urls = []
            for btn in buttons:
                video_url = btn.get("data-video")
                if video_url:
                    if video_url.startswith("//"):
                        video_url = "https:" + video_url
                    embed_urls.append(video_url)
            
            if not embed_urls:
                raise ScraperError("No streaming embed URLs found on watch page")
                
            resolved_links = {}
            # Check the first 2 servers (usually HD-1 and HD-2 represent the main HLS feeds)
            for embed_url in embed_urls[:2]:
                m3u8_master = await get_m3u8_from_embed(embed_url, session)
                if m3u8_master:
                    qualities = await parse_m3u8_qualities(m3u8_master, session)
                    resolved_links.update(qualities)
                    
            if not resolved_links:
                # If HD-1 and HD-2 failed, try other embed servers as fallback
                for embed_url in embed_urls[2:4]:
                    m3u8_master = await get_m3u8_from_embed(embed_url, session)
                    if m3u8_master:
                        qualities = await parse_m3u8_qualities(m3u8_master, session)
                        resolved_links.update(qualities)
                        
            if not resolved_links:
                raise ScraperError("Failed to parse HLS streams from embed players")
                
            logger.info(f"Resolved {len(resolved_links)} download link qualities: {list(resolved_links.keys())}")
            return resolved_links
        except Exception:
            logger.exception("Error in process while scraping download links")
            return {}
