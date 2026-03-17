"""Vibe Prospecting — Automated lead generation pipeline.

Full workflow:
1. DISCOVER — Kai searches multiple industries/locations for companies
2. ENRICH — Scrape websites for emails, phones, contacts
3. QUALIFY — Score leads based on data completeness + criteria
4. OUTREACH — Generate personalized proposals + send via Elena

Runs as a campaign: define target → run → get qualified leads → auto-pitch.
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("amine-agent")

# Industries to search across for diverse results
# Industries that NEED social media marketing (our target clients)
DEFAULT_INDUSTRIES = [
    "restaurants cafes food",
    "hotels resorts hospitality",
    "real estate property agency",
    "fashion boutique clothing store",
    "beauty salon spa wellness center",
    "fitness gym personal trainer",
    "interior design architecture studio",
    "photography videography studio",
    "retail shop ecommerce",
    "event planning wedding planner",
    "travel tourism agency",
    "luxury jewelry watches brand",
    "medical clinic dental aesthetic",
    "law firm legal services",
    "automotive car dealership showroom",
    "education training academy",
    "catering food delivery",
    "nightclub bar lounge",
    "art gallery museum",
    "pet shop veterinary grooming",
]


async def run_prospecting_campaign(
    location: str,
    target_count: int = 50,
    industries: list[str] = None,
    exclude_industries: list[str] = None,
    project_name: str = None,
    require_email: bool = True,
    require_phone: bool = False,
    require_website: bool = True,
) -> dict:
    """Run a full prospecting campaign.

    1. Creates a research project
    2. Searches multiple industries in the location
    3. Scrapes each company for contact info
    4. Saves all leads to the project
    5. Scores and qualifies them

    Returns campaign results.
    """
    from browser.fast_search import find_companies
    from app.database import get_db

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = project_name or f"Prospecting {location} {ts}"

    # Create research project
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO research_projects (name, description) VALUES (?, ?)",
        (name, f"Auto-prospecting campaign: {target_count} companies in {location}"),
    )
    await db.commit()
    project_id = cursor.lastrowid
    await db.close()

    logger.info(f"[prospect] Campaign started: {name} (project {project_id})")

    # Filter industries
    search_industries = industries or DEFAULT_INDUSTRIES
    if exclude_industries:
        exclude_lower = [x.lower() for x in exclude_industries]
        search_industries = [ind for ind in search_industries
                            if not any(ex in ind.lower() for ex in exclude_lower)]

    all_leads = []
    seen_domains = set()
    search_count = 0

    async def save_companies(companies, industry_label):
        """Save found companies to DB, returns number added."""
        nonlocal all_leads, seen_domains
        added = 0
        db = await get_db()
        for c in companies:
            if len(all_leads) >= target_count:
                break
            domain = c.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
            if domain in seen_domains or not domain:
                continue
            if require_email and not c.get("email"):
                continue
            if require_phone and not c.get("phone"):
                continue
            if require_website and not c.get("website"):
                continue
            seen_domains.add(domain)

            score = 0
            if c.get("email"): score += 40
            if c.get("phone"): score += 20
            if c.get("website"): score += 20
            if c.get("description"): score += 10
            if len(c.get("company", "")) > 3: score += 10
            status = "qualified" if score >= 60 else "new"

            await db.execute(
                "INSERT INTO leads (project_id, company_name, contact_name, email, phone, "
                "website, industry, location, source, notes, status, tags, found_by) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (project_id, c.get("company", "Unknown"), c.get("contact_name", ""),
                 c.get("email", ""), c.get("phone", ""), c.get("website", ""),
                 industry_label.split()[0], location, "vibe_prospecting",
                 f"Score: {score}/100. {c.get('description', '')[:200]}",
                 status, f"{industry_label.split()[0]},{location.lower()}", "auto"),
            )
            all_leads.append({**c, "score": score, "status": status})
            added += 1
        await db.commit()
        await db.close()
        return added

    # Pass 1: search all industries
    for industry in search_industries:
        if len(all_leads) >= target_count:
            break
        search_count += 1
        logger.info(f"[prospect] Search {search_count}: '{industry}' in {location} ({len(all_leads)}/{target_count})")
        try:
            companies = await asyncio.wait_for(find_companies(industry, location), timeout=20)
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"[prospect] Search failed for '{industry}': {e}")
            continue
        await save_companies(companies, industry)
        await asyncio.sleep(0.3)

    # Pass 2: if still under target, retry with more specific queries
    if len(all_leads) < target_count:
        logger.info(f"[prospect] Pass 2: {len(all_leads)}/{target_count}, trying specific queries")
        extra_queries = [
            f"best {ind} in {location} contact email" for ind in search_industries[:10]
        ] + [
            f"{location} {ind} company phone email website" for ind in search_industries[10:]
        ] + [
            f"top {location} businesses directory",
            f"{location} small business listings contact",
            f"new companies {location} marketing",
        ]
        for q in extra_queries:
            if len(all_leads) >= target_count:
                break
            search_count += 1
            try:
                companies = await asyncio.wait_for(find_companies(q, ""), timeout=20)
            except (asyncio.TimeoutError, Exception) as e:
                continue
            await save_companies(companies, q.split()[0])
            await asyncio.sleep(0.3)

    # Pass 3: if still under target, relax email requirement and try again
    if len(all_leads) < target_count and require_email:
        logger.info(f"[prospect] Pass 3: relaxing email requirement ({len(all_leads)}/{target_count})")
        require_email = False
        for industry in search_industries:
            if len(all_leads) >= target_count:
                break
            try:
                companies = await asyncio.wait_for(find_companies(industry, location), timeout=20)
            except (asyncio.TimeoutError, Exception):
                continue
            await save_companies(companies, industry)
            await asyncio.sleep(0.3)

    # Summary
    qualified = sum(1 for l in all_leads if l["status"] == "qualified")
    with_email = sum(1 for l in all_leads if l.get("email"))
    with_phone = sum(1 for l in all_leads if l.get("phone"))

    logger.info(f"[prospect] Campaign done: {len(all_leads)} leads, {qualified} qualified, {with_email} emails")

    # Send notification
    from agents.notify import notify
    await notify(
        "Prospecting Complete 🎯",
        f"Found {len(all_leads)} companies in {location}.\n"
        f"{qualified} qualified, {with_email} with email, {with_phone} with phone.\n"
        f"Project: {name}",
        "high", "dart"
    )

    return {
        "project_id": project_id,
        "project_name": name,
        "total_found": len(all_leads),
        "qualified": qualified,
        "with_email": with_email,
        "with_phone": with_phone,
        "searches_run": search_count,
    }


async def auto_outreach(project_id: int, max_sends: int = 10) -> dict:
    """Auto-generate proposals and queue emails for qualified leads.

    Only targets leads with emails and status='qualified'.
    Generates a personalized PDF for each.
    """
    from app.database import get_db
    from agents.email_template import generate_marketing_pdf

    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM leads WHERE project_id=? AND status='qualified' AND email != '' LIMIT ?",
        (project_id, max_sends),
    )
    await db.close()
    leads = [dict(r) for r in rows]

    if not leads:
        return {"sent": 0, "message": "No qualified leads with emails found"}

    results = []
    for lead in leads:
        try:
            # Generate personalized proposal
            pdf_path = await generate_marketing_pdf(
                client_name=lead["contact_name"] or lead["company_name"],
                client_company=lead["company_name"],
            )
            results.append({
                "company": lead["company_name"],
                "email": lead["email"],
                "proposal": pdf_path,
                "status": "ready",
            })

            # Update lead status
            db = await get_db()
            await db.execute(
                "UPDATE leads SET status='contacted', notes=notes||? WHERE id=?",
                (f"\nProposal sent: {pdf_path}", lead["id"]),
            )
            await db.commit()
            await db.close()

        except Exception as e:
            logger.error(f"[prospect] Outreach error for {lead['company_name']}: {e}")
            results.append({"company": lead["company_name"], "status": "error", "error": str(e)})

    return {"processed": len(results), "results": results}
