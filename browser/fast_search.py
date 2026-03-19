"""Fast web research — multi-engine company search.

Engines (in priority order):
1. SerpAPI Google Maps — Best for local businesses (name, phone, website, address)
2. Serper.dev — Google search results (if SERPER_API_KEY set)
3. DuckDuckGo — Free fallback

Set SERPAPI_KEY or SERPER_API_KEY in .env for best results.
"""

import re
import os
import json
import logging
import asyncio
from urllib.parse import unquote

import httpx

logger = logging.getLogger("amine-agent")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

# Sites that are NOT actual businesses — skip these
SKIP_DOMAINS = {
    'google', 'facebook', 'linkedin.com', 'twitter', 'youtube', 'wikipedia',
    'yelp.com', 'tripadvisor', 'booking.com', 'amazon', 'reddit',
    'michelin', 'fodors.com', 'viamichelin', 'timeout.com', 'thefork',
    'opentable', 'zomato', 'justeat', 'deliveroo', 'uber', 'glassdoor',
    'indeed.com', 'yellowpages', 'whitepages', 'crunchbase', 'bloomberg',
    'jacadatravel', 'lonelyplanet', 'theculturetrip', 'travelandleisure',
    'cntraveler', 'afar.com', 'skyscanner', 'kayak', 'expedia', 'hotels.com',
    'airbnb', 'vrbo', 'agoda', 'trivago', 'wikitravel', 'wikivoyage',
    'pinterest', 'instagram', 'tiktok', 'medium.com', 'quora.com',
    'trustpilot', 'capterra', 'g2.com', 'clutch.co', 'behance',
    'dribbble', 'fiverr', 'upwork', 'thumbtack', 'angi.com',
    'slovenia.info', 'travelslovenia', 'visitslovenia', 'myguideslovenia',
    'tasteatlas', 'inyourpocket', '2foodtrippers', 'sloveniaholidays',
    'talesmag', 'theinfatuation', 'eater.com', 'thrillist',
    'travel.state', 'wikidata', 'dbpedia', 'nytimes', 'bbc',
    'forbes', 'businessinsider', 'cnbc', 'reuters', 'makemytrip',
    'ricksteves', 'wa.me', 'epicgames', 'buyereviews',
    'community.ricksteves', 'elliott.org', 'idahoan', 'mariani',
}


# ═══════════════════════════════════════════════════════
# ENGINE 1: SerpAPI Google Maps (BEST for local business)
# ═══════════════════════════════════════════════════════

async def search_google_maps(query: str, location: str, count: int = 20) -> list[dict]:
    """Search Google Maps via SerpAPI. Returns actual businesses with phone, website, address."""
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://serpapi.com/search.json", params={
                "engine": "google_maps",
                "q": f"{query} in {location}",
                "type": "search",
                "api_key": api_key,
                "num": str(min(count + 5, 40)),
            })
            data = resp.json()

        results = data.get("local_results", [])
        companies = []
        for r in results[:count]:
            companies.append({
                "company": r.get("title", "")[:60],
                "website": r.get("website", ""),
                "email": "",  # Maps doesn't give emails, we'll scrape
                "phone": r.get("phone", ""),
                "description": r.get("type", "") + " — " + r.get("address", ""),
                "rating": r.get("rating", 0),
                "reviews": r.get("reviews", 0),
            })

        # Scrape websites in parallel for emails
        if companies:
            async def get_email(c):
                if not c["website"]:
                    return c
                try:
                    page = await scrape_page(c["website"], 3000)
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page)
                    emails = [e for e in emails if not any(x in e.lower() for x in
                              ['example', 'test', 'noreply', 'sentry', 'cloudflare', 'wixpress', 'googleapis', 'schema.org'])]
                    if emails:
                        c["email"] = emails[0]
                except Exception:
                    pass
                return c

            companies = await asyncio.gather(*[get_email(c) for c in companies])

        logger.info(f"[serpapi-maps] Found {len(companies)} businesses for '{query}' in {location}")
        return list(companies)

    except Exception as e:
        logger.error(f"[serpapi-maps] Error: {e}")
        return []


# ═══════════════════════════════════════════════════════
# ENGINE 2: Serper.dev Google Search
# ═══════════════════════════════════════════════════════

async def search_serper(query: str, count: int = 10) -> list[dict]:
    """Search via Serper.dev (Google search API)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("https://google.serper.dev/search", json={
                "q": query, "num": min(count, 30)
            }, headers={"X-API-KEY": api_key, "Content-Type": "application/json"})
            data = resp.json()

        results = []
        for r in data.get("organic", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            })
        logger.info(f"[serper] {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.error(f"[serper] Error: {e}")
        return []


# ═══════════════════════════════════════════════════════
# ENGINE 3: DuckDuckGo (free fallback)
# ═══════════════════════════════════════════════════════

async def search_ddg(query: str, num_results: int = 10) -> list[dict]:
    """Search the web using DuckDuckGo API."""
    try:
        from ddgs import DDGS
        def _search():
            return DDGS().text(query, max_results=num_results)

        results = await asyncio.to_thread(_search)
        out = []
        for r in results:
            out.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            })
        logger.info(f"[ddg] {len(out)} results for '{query}'")
        return out

    except Exception as e:
        logger.error(f"[ddg] Error: {e}")
        return []


# Keep backward compatibility
async def search_web(query: str, num_results: int = 10) -> list[dict]:
    """Search web — tries Serper first, falls back to DuckDuckGo."""
    # Try Serper first (Google quality)
    results = await search_serper(query, num_results)
    if results:
        return results
    # Fallback to DuckDuckGo
    return await search_ddg(query, num_results)


# ═══════════════════════════════════════════════════════
# SCRAPER
# ═══════════════════════════════════════════════════════

async def scrape_page(url: str, max_chars: int = 5000) -> str:
    """Fetch a web page and extract clean text content."""
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text

        # Remove junk
        html = re.sub(r'<(script|style|nav|footer|header|aside)[^>]*>[\s\S]*?</\1>', '', html, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

        return text[:max_chars]
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════
# MAIN: find_companies (multi-engine)
# ═══════════════════════════════════════════════════════

async def find_companies(query: str, location: str = "", count: int = 20) -> list[dict]:
    """Find companies with contact info using best available engine.

    Priority:
    1. SerpAPI Google Maps — actual local businesses with phones
    2. Serper/DDG web search + page scraping
    """
    target = max(count, 5)
    loc = location.strip()
    q = query.strip()

    # ── Try Google Maps first (best for local businesses) ──
    maps_results = await search_google_maps(q, loc, target)
    if len(maps_results) >= target * 0.6:  # Got enough from Maps
        logger.info(f"[find] Google Maps returned {len(maps_results)} results — using those")
        return maps_results[:target]

    # ── Fall back to web search + scraping ──
    all_companies = list(maps_results)  # start with any Maps results
    seen_domains = set()
    for c in all_companies:
        if c.get("website"):
            d = re.search(r'https?://(?:www\.)?([^/]+)', c["website"])
            if d:
                seen_domains.add(d.group(1))

    # Run multiple search queries
    search_queries = [
        f'{q} {loc} "contact" OR "email" OR "phone"',
        f'{q} company {loc}',
        f'best {q} {loc}',
        f'{q} {loc} official website',
        f'top {q} near {loc}',
        f'{q} {loc} phone email address',
        f'{q} services {loc}',
    ]

    all_results = []
    for sq in search_queries:
        if len(all_results) >= target * 3:
            break
        batch = await search_web(sq.strip(), num_results=min(target + 5, 25))
        all_results += batch

    # Filter aggregators and deduplicate
    filtered = []
    for r in all_results:
        domain = re.search(r'https?://(?:www\.)?([^/]+)', r['url'])
        if domain:
            d = domain.group(1)
            if d in seen_domains or any(x in d for x in SKIP_DOMAINS):
                continue
            seen_domains.add(d)
        filtered.append(r)

    if not filtered and not all_companies:
        return []

    # Scrape pages in parallel for contact info
    async def extract(r):
        try:
            page = await scrape_page(r['url'], 3000)
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page)
            emails = [e for e in emails if not any(x in e.lower() for x in
                      ['example', 'test', 'noreply', 'sentry', 'cloudflare', 'wixpress', 'googleapis', 'schema.org'])]
            phones = re.findall(r'(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}', page)
            phones = [p.strip() for p in phones if 8 <= len(p.strip()) <= 20]
            return {
                "company": r['title'].split(' - ')[0].split(' | ')[0].split(' — ')[0].strip()[:60],
                "website": r['url'],
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
                "description": r.get('snippet', '')[:200],
            }
        except Exception:
            return {
                "company": r['title'].split(' - ')[0].split(' | ')[0].strip()[:60],
                "website": r['url'], "email": "", "phone": "",
                "description": r.get('snippet', '')[:200],
            }

    scraped = await asyncio.gather(*[extract(r) for r in filtered[:target * 2]])
    all_companies += list(scraped)

    # Deduplicate by domain
    final = []
    seen = set()
    for c in all_companies:
        domain = re.search(r'https?://(?:www\.)?([^/]+)', c.get("website", ""))
        key = domain.group(1) if domain else c.get("company", "")
        if key not in seen:
            seen.add(key)
            final.append(c)

    logger.info(f"[find] Found {len(final)} companies for '{q} {loc}' (requested {count})")
    return final[:target]


# ═══════════════════════════════════════════════════════
# RESEARCH
# ═══════════════════════════════════════════════════════

async def fast_research(query: str) -> str:
    """Full research: search + scrape top results."""
    logger.info(f"[research] Searching: {query}")

    results = await search_web(query, num_results=8)
    if not results:
        return f"No results found for: {query}"

    output = [f"**Search results for: {query}**\n"]
    for i, r in enumerate(results):
        output.append(f"**{i+1}. {r['title']}**")
        output.append(f"URL: {r['url']}")
        if r['snippet']:
            output.append(f"{r['snippet']}")
        output.append("")

    # Scrape top 3 in parallel
    scrape_tasks = [scrape_page(r['url'], 1500) for r in results[:3]]
    pages = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    output.append("\n**Details from top results:**\n")
    for i, page in enumerate(pages):
        if isinstance(page, str) and not page.startswith("Error") and len(page) > 100:
            output.append(f"--- {results[i]['title']} ---")
            output.append(page[:1200])
            output.append("")

    return "\n".join(output)
