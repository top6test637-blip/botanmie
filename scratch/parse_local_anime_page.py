from bs4 import BeautifulSoup
import re

with open("scratch/anime_page.html", "r", encoding="utf-8") as f:
    html = f.read()
    
soup = BeautifulSoup(html, "html.parser")
links = soup.find_all("a", href=True)
print(f"Total links: {len(links)}")
ep_links = [l.get("href") for l in links if "/episode/" in l.get("href")]
print(f"Episode links: {len(ep_links)}")
for el in ep_links[:10]:
    print(el)
