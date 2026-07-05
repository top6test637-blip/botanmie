import asyncio
import aiohttp
import re
import json
import base64
import random
import string
import struct
import xml.etree.ElementTree as ET

_STATIC_SECRET = 'xHb0ZvME5q8CBcoQi6AngerDu3FGO9fkUlwPmLVY_RTzj2hJIS4NasXWKy1td7p'

def rc4(cipher_text, key):
    res = b''
    key_len = len(key)
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + ord(key[i % key_len])) % 256
        S[i], S[j] = S[j], S[i]
    i = 0
    j = 0
    for m in range(len(cipher_text)):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        res += struct.pack('B', k ^ cipher_text[m])
    try:
        return res.decode('utf-8')
    except Exception:
        return res.decode('latin-1')

async def main():
    embed_url = "https://videa.hu/player?v=x2WVLBeHDqdE0pP7"
    video_id = "x2WVLBeHDqdE0pP7"
    
    print(f"Requesting player page: {embed_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(embed_url, headers=headers, ssl=False) as resp:
            if resp.status != 200:
                print(f"Failed to get player page: status {resp.status}")
                return
            html = await resp.text()
            
            # Find _xt
            xt_match = re.search(r'_xt\s*=\s*"([^"]+)"', html)
            if not xt_match:
                print("Failed to find _xt nonce in html!")
                return
            nonce = xt_match.group(1)
            print(f"Found _xt: {nonce}")
            
            l = nonce[:32]
            s = nonce[32:]
            result = ''
            for i in range(32):
                idx = l[i]
                sec_idx = _STATIC_SECRET.index(idx)
                shift = sec_idx - 31
                char_idx = i - shift
                result += s[char_idx]
            
            print(f"Computed result: {result}")
            
            random_seed = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            t_param = result[:16]
            
            xml_url = f"https://videa.hu/player/xml?v={video_id}&_s={random_seed}&_t={t_param}"
            print(f"Requesting XML: {xml_url}")
            
            # We must pass Referer and User-Agent
            xml_headers = {
                "User-Agent": headers["User-Agent"],
                "Referer": embed_url
            }
            
            async with session.get(xml_url, headers=xml_headers, ssl=False) as xml_resp:
                print(f"XML Response Status: {xml_resp.status}")
                if xml_resp.status != 200:
                    print("Failed to get XML.")
                    return
                
                content_type = xml_resp.headers.get("Content-Type", "")
                print(f"Content-Type: {content_type}")
                
                body = await xml_resp.read()
                print(f"Body length: {len(body)}")
                
                x_videa_xs = xml_resp.headers.get("x-videa-xs")
                print(f"x-videa-xs header: {x_videa_xs}")
                
                # Check if it starts with <?xml
                if body.startswith(b'<?xml'):
                    xml_text = body.decode('utf-8')
                else:
                    if not x_videa_xs:
                        print("Missing x-videa-xs header for decryption!")
                        return
                    key = result[16:] + random_seed + x_videa_xs
                    print(f"Decrypting with key: {key}")
                    xml_text = rc4(base64.b64decode(body), key)
                
                print(f"XML text snippet: {xml_text[:500]}")
                
                # Parse XML
                root = ET.fromstring(xml_text)
                
                video_sources = root.find('./video_sources')
                hash_values = root.find('./hash_values')
                
                if video_sources is not None:
                    for source in video_sources.findall('./video_source'):
                        name = source.get('name')
                        exp = source.get('exp')
                        url = source.text
                        
                        hash_value = None
                        if hash_values is not None:
                            hash_el = hash_values.find(f'hash_value_{name}')
                            if hash_el is not None:
                                hash_value = hash_el.text
                                
                        if hash_value and exp:
                            url = f"{url}?md5={hash_value}&expires={exp}"
                            
                        print(f"Found source: {name} -> {url}")

if __name__ == "__main__":
    asyncio.run(main())
