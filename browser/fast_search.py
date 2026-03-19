"""Fast web research — multi-engine company search.

Engines (in priority order):
1. Serper.dev — Google search results (if SERPER_API_KEY set and valid)
2. DuckDuckGo — Free fallback (always available)

Set SERPER_API_KEY in .env for Google-quality results.
"""

import re
import os
import json
import logging
import asyncio

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
    'elliott.org', 'idahoan', 'mariani', 'shutterstock',
    'community.ricksteves', 'mgmresorts', 'aman.com', 'broadmoor',
}


# ═══════════════════════════════════════════════════════
# SEARCH ENGINES
# ═══════════════════════════════════════════════════════

async def search_serper(query: str, count: int = 10) -> list[dict]:
    """Search via Serper.dev (Google search API)."""
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("https://google.serper.dev/search", json={
                "q": query, "num": min(count, 30)
            }, headers={"X-API-KEY": api_key, "Content-Type": "application/json"})
            data = resp.json()
        if "message" in data:  # API error
            logger.warning(f"[serper] API error: {data.get('message')}")
            return []
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


async def search_ddg(query: str, num_results: int = 10) -> list[dict]:
    """Search using DuckDuckGo."""
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


async def search_web(query: str, num_results: int = 10) -> list[dict]:
    """Search web — tries Serper first, falls back to DuckDuckGo."""
    results = await search_serper(query, num_results)
    if results:
        return results
    return await search_ddg(query, num_results)


# ═══════════════════════════════════════════════════════
# PAGE SCRAPER
# ═══════════════════════════════════════════════════════

async def scrape_page(url: str, max_chars: int = 5000) -> str:
    """Fetch a web page and extract clean text content."""
    try:
        async with httpx.AsyncClient(timeout=8, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text
        html = re.sub(r'<(script|style|nav|footer|header|aside)[^>]*>[\s\S]*?</\1>', '', html, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        return text[:max_chars]
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════
# MAIN: find_companies
# ═══════════════════════════════════════════════════════

async def find_companies(query: str, location: str = "", count: int = 20) -> list[dict]:
    """Find companies with contact info. Uses multiple search queries + parallel scraping."""
    target = max(count, 5)
    loc = location.strip()
    q = query.strip()

    # Build multiple search queries to maximize results
    search_queries = [
        f'{q} {loc} contact email',
        f'{q} {loc} company',
        f'best {q} {loc}',
        f'{q} {loc} official website',
        f'top {q} in {loc}',
        f'{q} near {loc} phone',
        f'{q} {loc} services',
    ]

    # Run searches and collect unique results
    all_results = []
    seen_domains = set()

    for sq in search_queries:
        if len(all_results) >= target * 2:
            break
        batch = await search_web(sq.strip(), num_results=min(target + 5, 20))
        for r in batch:
            url = r.get("url", "")
            domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if not domain:
                continue
            d = domain.group(1)
            if d in seen_domains or any(x in d for x in SKIP_DOMAINS):
                continue
            seen_domains.add(d)
            all_results.append(r)

    if not all_results:
        logger.warning(f"[find] No results for '{q} {loc}'")
        return []

    # Scrape all pages in parallel — check homepage + contact page for emails
    _bad_emails = {'example', 'test', 'noreply', 'sentry', 'cloudflare',
                   'wixpress', 'googleapis', 'schema.org', 'w3.org',
                   'your-email', 'email@', 'name@', 'user@', 'support@wix',
                   'wordpress', 'developer', 'webmaster', 'localhost'}

    def _extract_emails(text):
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return [e for e in emails if not any(x in e.lower() for x in _bad_emails)]

    def _extract_phones(text):
        phones = re.findall(r'(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}', text)
        return [p.strip() for p in phones if 8 <= len(p.strip()) <= 20]

    async def extract(r):
        url = r['url']
        company = r['title'].split(' - ')[0].split(' | ')[0].split(' — ')[0].strip()[:60]
        emails = []
        phones = []

        try:
            # 1. Scrape homepage
            page = await scrape_page(url, 5000)
            emails = _extract_emails(page)
            phones = _extract_phones(page)

            # 2. If no email found, scrape contact/about pages
            if not emails:
                base = re.match(r'(https?://[^/]+)', url)
                if base:
                    base_url = base.group(1)
                    contact_paths = [
                        '/contact', '/contact-us', '/kontakt', '/about',
                        '/about-us', '/impressum', '/o-nas', '/kontakti',
                    ]
                    # Also try to find contact link in page
                    contact_links = re.findall(
                        r'href=["\']([^"\']*(?:contact|kontakt|about|impressum|o-nas)[^"\']*)["\']',
                        page, re.IGNORECASE
                    )
                    for link in contact_links[:2]:
                        if link.startswith('/'):
                            contact_paths.insert(0, link)
                        elif link.startswith('http'):
                            contact_paths.insert(0, link)

                    # Scrape up to 3 contact pages in parallel
                    async def try_page(path):
                        u = path if path.startswith('http') else base_url + path
                        return await scrape_page(u, 3000)

                    pages = await asyncio.gather(
                        *[try_page(p) for p in contact_paths[:3]],
                        return_exceptions=True
                    )
                    for pg in pages:
                        if isinstance(pg, str) and not pg.startswith("Error"):
                            emails += _extract_emails(pg)
                            phones += _extract_phones(pg)
                        if emails:
                            break

            # 3. If STILL no email, guess common patterns from domain
            if not emails:
                domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                if domain_match:
                    domain = domain_match.group(1)
                    # Only guess for non-generic domains
                    if '.' in domain and len(domain) < 40:
                        emails = [f"info@{domain}"]

        except Exception:
            pass

        return {
            "company": company,
            "website": url,
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "description": r.get('snippet', '')[:200],
        }

    companies = await asyncio.gather(*[extract(r) for r in all_results[:target * 2]])
    companies = [c for c in companies if c.get("company")]

    # Sort: companies with real email first, then guessed, then none
    def _email_score(c):
        e = c.get("email", "")
        if not e:
            return 2
        if e.startswith("info@") and e.split("@")[1] in c.get("website", ""):
            return 1  # guessed
        return 0  # found on page

    companies.sort(key=_email_score)
    logger.info(f"[find] Found {len(companies)} companies for '{q} {loc}' "
                f"({sum(1 for c in companies if c['email'])} with email, requested {count})")
    return companies[:target]


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

    scrape_tasks = [scrape_page(r['url'], 1500) for r in results[:3]]
    pages = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    output.append("\n**Details from top results:**\n")
    for i, page in enumerate(pages):
        if isinstance(page, str) and not page.startswith("Error") and len(page) > 100:
            output.append(f"--- {results[i]['title']} ---")
            output.append(page[:1200])
            output.append("")

    return "\n".join(output)
