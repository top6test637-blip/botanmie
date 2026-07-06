import base64
from typing import Optional, Dict, Any
from app.utils.logging_config import logger

def encode_deeplink_payload(anilist_id: int, ep_number: str, quality: str = "720p", anime_title: str = "") -> str:
    """Encodes anilist_id, episode number, quality, and optional anime title into a URL-safe Base64 payload string."""
    raw_str = f"{anilist_id}:{ep_number}:{quality}:{anime_title}"
    b64_bytes = base64.urlsafe_b64encode(raw_str.encode('utf-8'))
    b64_str = b64_bytes.decode('utf-8').rstrip('=')
    return f"ep_{b64_str}"

def decode_deeplink_payload(payload: str) -> Optional[Dict[str, Any]]:
    """Decodes a start payload string into anilist_id, ep_number, quality, and anime_title."""
    if not payload:
        return None
    try:
        clean_payload = payload.strip()
        if clean_payload.startswith("ep_"):
            clean_payload = clean_payload[3:]
        
        # Add padding back if missing
        padding = 4 - (len(clean_payload) % 4)
        if padding != 4:
            clean_payload += "=" * padding
            
        decoded_bytes = base64.urlsafe_b64decode(clean_payload.encode('utf-8'))
        decoded_str = decoded_bytes.decode('utf-8')
        parts = decoded_str.split(":")
        
        if len(parts) >= 2:
            anilist_id = int(parts[0])
            ep_number = parts[1]
            quality = parts[2] if len(parts) >= 3 else "720p"
            anime_title = parts[3] if len(parts) >= 4 else f"الأنمي رقم #{anilist_id}"
            return {
                "anilist_id": anilist_id,
                "ep_number": ep_number,
                "quality": quality,
                "anime_title": anime_title
            }
    except Exception as e:
        logger.warning(f"Failed to decode deeplink payload '{payload}': {e}")
    return None
