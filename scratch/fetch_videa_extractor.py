import urllib.request

url = "https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/videa.py"
print(f"Downloading {url}...")
try:
    with urllib.request.urlopen(url) as response:
        code = response.read().decode('utf-8')
        with open("scratch/videa_extractor.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("Success! Saved to scratch/videa_extractor.py")
except Exception as e:
    print(f"Failed to download: {e}")
