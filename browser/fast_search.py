"""Fast web research — no browser needed.

Uses DuckDuckGo API (via ddgs package) for instant search results,
then scrapes pages in parallel for contact info.
"""

import re
import json
import logging
import asyncio
from urllib.parse import unquote

import httpx

logger = logging.getLogger("amine-agent")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}


async def search_web(query: str, num_results: int = 10) -> list[dict]:
    """Search the web using DuckDuckGo API. Returns list of {title, url, snippet}."""
    try:
        from ddgs import DDGS
        # Run sync DDGS in a thread to not block async
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
        logger.info(f"[search] {len(out)} results for '{query}'")
        return out

    except Exception as e:
        logger.error(f"[search] Error: {e}")
        return []


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


async def find_companies(query: str, location: str = "", count: int = 20) -> list[dict]:
    """Find companies with contact info. Scrapes in parallel for speed.

    Args:
        count: Target number of companies to find. Will run extra searches to hit the target.
    """
    target = max(count, 5)
    # Use multiple targeted queries to find actual business websites
    loc = location.strip()
    q = query.strip()
    search_queries = [
        f'"{q}" "{loc}" site:.com OR site:.si OR site:.ae -tripadvisor -yelp -booking',
        f'{q} {loc} "contact us" OR "@" OR "email"',
        f'{q} {loc} official website',
        f'{q} company {loc}',
        f'best {q} {loc}',
        f'top {q} near {loc}',
        f'{q} {loc} phone email address',
    ]
    results = []
    for sq in search_queries:
        if len(results) >= target + 15:
            break
        batch = await search_web(sq.strip(), num_results=min(target + 5, 25))
        results += batch

    # Filter aggregator/social/directory sites — we want actual business websites
    skip = {'google', 'facebook', 'linkedin.com', 'twitter', 'youtube', 'wikipedia',
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
            'travel.state', 'wikidata', 'dbpedia'}
    filtered = []
    seen = set()
    for r in results:
        domain = re.search(r'https?://(?:www\.)?([^/]+)', r['url'])
        if domain:
            d = domain.group(1)
            if d in seen or any(x in d for x in skip):
                continue
            seen.add(d)
        filtered.append(r)

    if not filtered:
        return []

    # Scrape ALL pages in parallel
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

    companies = await asyncio.gather(*[extract(r) for r in filtered])
    # Trim to requested count
    companies = list(companies)[:target]
    logger.info(f"[search] Found {len(companies)} companies for '{q} {loc}' (requested {count})")
    return companies
