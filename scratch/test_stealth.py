import asyncio
from playwright.async_api import async_playwright

async def test():
    url = "https://witanime.pics/?search_param=animes&s=Suterare"
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        await page.add_init_script("delete navigator.__proto__.webdriver;")
        
        print("Navigating...")
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        title = await page.title()
        print("Page Title:", title)
        print("HTML length:", len(html))
        if "Cloudflare" in html or "Just a moment" in html:
            print("Blocked by Cloudflare!")
        else:
            print("Successfully bypassed Cloudflare!")
            
        await browser.close()

asyncio.run(test())
