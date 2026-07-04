from difflib import SequenceMatcher
import re

def validate_title_match(original_title: str, matched_title: str) -> bool:
    """Verifies that the matched title shares significant keyword containment or a high fuzzy match ratio with the original title."""
    orig_lower = original_title.lower().strip()
    match_lower = matched_title.lower().strip()
    
    # 1. Fuzzy match ratio
    ratio = SequenceMatcher(None, orig_lower, match_lower).ratio()
    if ratio >= 0.55:
        return True
        
    # 2. Check substring containment (e.g., "Attack on Titan" is inside "Attack on Titan Season 3")
    if orig_lower in match_lower or match_lower in orig_lower:
        return True
        
    # 3. Check keyword overlap
    orig_words = set(re.findall(r"\w+", orig_lower))
    match_words = set(re.findall(r"\w+", match_lower))
    
    # Common helper words / stop words that shouldn't dictate uniqueness
    stop_words = {"the", "of", "and", "a", "in", "to", "for", "with", "on", "at", "by", "an", "is", "season", "part", "shippuden", "specials", "ova", "movie", "فيلم", "أوفا", "خاصة"}
    orig_keywords = {w for w in orig_words if len(w) > 2 and w not in stop_words}
    match_keywords = {w for w in match_words if len(w) > 2 and w not in stop_words}
    
    if not orig_keywords:
        return True
        
    overlap = orig_keywords.intersection(match_keywords)
    # If original title has important keywords, at least 60% of them must be present in the matched title
    if len(overlap) / len(orig_keywords) >= 0.60:
        return True
        
    return False

def get_best_slug_match(scraper_results, search_title: str) -> str:
    """Selects the best matching anime slug from scraper results, prioritizing TV series over movies/OVAs/specials."""
    if not scraper_results:
        return ""
        
    # Filter scraper results using strict title validation to prevent the "Nonsense" wrong anime bug
    valid_results = []
    for r in scraper_results:
        if validate_title_match(search_title, r["title"]):
            valid_results.append(r)
            
    if not valid_results:
        # Discard wrong anime structures and return empty string
        return ""
        
    search_title_lower = search_title.lower()
    
    # 1. Look for exact title match (case-insensitive)
    for r in valid_results:
        if r["title"].lower() == search_title_lower:
            return r["slug"]
            
    # 2. Look for title that contains search title (or vice-versa) and isn't a movie/special/OVA
    non_tv_keywords = ["movie", "فيلم", "ova", "أوفا", "special", "خاصة", "ونا", "ona", "more"]
    # Sort scraper results by length of title to match shorter/purer titles first
    sorted_results = sorted(valid_results, key=lambda x: len(x["title"]))
    
    for r in sorted_results:
        title_lower = r["title"].lower()
        slug_lower = r["slug"].lower()
        if search_title_lower in title_lower or title_lower in search_title_lower:
            if not any(kw in title_lower or kw in slug_lower for kw in non_tv_keywords):
                return r["slug"]
                
    # 3. Fallback to any result matching search title
    for r in sorted_results:
        title_lower = r["title"].lower()
        if search_title_lower in title_lower or title_lower in search_title_lower:
            return r["slug"]
            
    # 4. Fallback to first valid result
    return valid_results[0]["slug"]

def sanitize_search_query(title: str) -> str:
    """Cleans the anime title by removing subtitles, special characters, and bullets."""
    if not title:
        return ""
    
    # Split by colons (:) or dashes ( - ) and take only the first part
    for splitter in [":", " - "]:
        if splitter in title:
            title = title.split(splitter)[0]
            
    # Remove special bullets like ● and symbols, punctuation
    title = re.sub(r"[●⚫⚪■□◆◇▲▼★☆✦✧♦♣♠♥🃏#@$^*&_+|~`{}[\];\"'<>]", " ", title)
    
    # Replace multiple spaces with a single space
    title = " ".join(title.split())
    return title.strip()
