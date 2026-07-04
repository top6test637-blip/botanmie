def get_best_slug_match(scraper_results, search_title: str) -> str:
    """Selects the best matching anime slug from scraper results, prioritizing TV series over movies/OVAs/specials."""
    if not scraper_results:
        return ""
        
    search_title_lower = search_title.lower()
    
    # 1. Look for exact title match (case-insensitive)
    for r in scraper_results:
        if r["title"].lower() == search_title_lower:
            return r["slug"]
            
    # 2. Look for title that contains search title (or vice-versa) and isn't a movie/special/OVA
    non_tv_keywords = ["movie", "فيلم", "ova", "أوفا", "special", "خاصة", "ونا", "ona", "more"]
    # Sort scraper results by length of title to match shorter/purer titles first
    sorted_results = sorted(scraper_results, key=lambda x: len(x["title"]))
    
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
            
    # 4. Fallback to first result
    return scraper_results[0]["slug"]


def sanitize_search_query(title: str) -> str:
    """Cleans the anime title by removing subtitles, special characters, and bullets."""
    if not title:
        return ""
    
    # Split by colons (:) or dashes ( - ) and take only the first part
    for splitter in [":", " - "]:
        if splitter in title:
            title = title.split(splitter)[0]
            
    # Remove special bullets like ● and symbols, punctuation
    import re
    title = re.sub(r"[●⚫⚪■□◆◇▲▼★☆✦✧♦♣♠♥🃏#@$^*&_+|~`{}[\];\"'<>]", " ", title)
    
    # Replace multiple spaces with a single space
    title = " ".join(title.split())
    return title.strip()
