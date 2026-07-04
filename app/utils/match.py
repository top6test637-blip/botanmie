def get_best_slug_match(scraper_results, search_title: str) -> str:
    """Selects the best matching anime slug from scraper results, prioritizing TV series over movies/OVAs."""
    if not scraper_results:
        return ""
        
    search_title_lower = search_title.lower()
    
    # 1. Look for exact title match (case-insensitive)
    for r in scraper_results:
        if r["title"].lower() == search_title_lower:
            return r["slug"]
            
    # 2. Look for title that contains the search title and doesn't indicate a movie/OVA/special
    non_tv_keywords = ["movie", "فيلم", "ova", "أوفا", "special", "خاصة", "ونا", "ona"]
    for r in scraper_results:
        title_lower = r["title"].lower()
        slug_lower = r["slug"].lower()
        if not any(kw in title_lower or kw in slug_lower for kw in non_tv_keywords):
            return r["slug"]
            
    # 3. Fallback to first result
    return scraper_results[0]["slug"]
