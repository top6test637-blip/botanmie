import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open("scratch/anime_page.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
for idx, s in enumerate(soup.find_all("script")):
    src = s.get("src")
    text = s.text.strip()
    print(f"Script [{idx}]: src={src}, text_length={len(text)}")
    if text and len(text) > 50:
        print(f"  Snippet: {text[:200]}")
