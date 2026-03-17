"""Dubai Prod Agency — Branded Email Marketing PDF Template.

Generates professional PDF proposals/marketing emails with:
- Dubai Prod branding (gold + dark)
- Agent avatar/sender info
- Client name/date auto-filled
- Service offerings
- Portfolio showcase
"""

import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak,
)

logger = logging.getLogger("amine-agent")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "img"

GOLD = colors.HexColor("#c9a44e")
DARK_BG = colors.HexColor("#0c0c12")
DARK_CARD = colors.HexColor("#1a1a2e")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#f8f9fa")
GRAY = colors.HexColor("#888888")


def _brand_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle('Brand', fontSize=32, textColor=GOLD, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle('BrandSub', fontSize=12, textColor=GRAY, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle('SectionGold', fontSize=18, textColor=GOLD, fontName='Helvetica-Bold', spaceBefore=25, spaceAfter=10))
    styles.add(ParagraphStyle('BodyDark', fontSize=11, textColor=colors.HexColor("#333333"), leading=16, spaceAfter=8))
    styles.add(ParagraphStyle('BodyBold', fontSize=11, textColor=colors.HexColor("#111111"), fontName='Helvetica-Bold', leading=16, spaceAfter=4))
    styles.add(ParagraphStyle('SmallMuted', fontSize=9, textColor=GRAY, alignment=TA_CENTER))
    styles.add(ParagraphStyle('CTA', fontSize=14, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER))
    styles.add(ParagraphStyle('ClientName', fontSize=22, textColor=colors.HexColor("#111111"), fontName='Helvetica-Bold', spaceAfter=4))
    styles.add(ParagraphStyle('Date', fontSize=11, textColor=GRAY, spaceAfter=20))

    return styles


async def generate_marketing_pdf(
    client_name: str,
    client_company: str = "",
    services: list[str] = None,
    custom_intro: str = "",
    custom_body: str = "",
    sender_name: str = "Amine Damoun",
    sender_title: str = "Founder & CEO",
) -> str:
    """Generate a branded email marketing PDF for a client.

    Returns web path to the PDF.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"proposal_{ts}.pdf"
    filepath = UPLOADS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )

    styles = _brand_styles()
    story = []

    # ============ HEADER ============
    story.append(Spacer(1, 20))
    story.append(Paragraph("DUBAI PROD", styles['Brand']))
    story.append(Paragraph("Digital Marketing Agency", styles['BrandSub']))
    story.append(HRFlowable(width="60%", thickness=2, color=GOLD, spaceAfter=30, hAlign='CENTER'))

    # ============ CLIENT INFO ============
    story.append(Paragraph(f"Prepared for", styles['SmallMuted']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(client_name, styles['ClientName']))
    if client_company:
        story.append(Paragraph(client_company, styles['BodyDark']))
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles['Date']))

    # ============ INTRO ============
    story.append(Paragraph("Dear " + client_name.split()[0] + ",", styles['BodyDark']))

    if custom_intro:
        story.append(Paragraph(custom_intro, styles['BodyDark']))
    else:
        story.append(Paragraph(
            "Thank you for your interest in Dubai Prod. We are a full-service digital marketing agency "
            "based in Dubai, specializing in social media management, content creation, video production, "
            "and brand strategy for luxury and premium brands across the Middle East.",
            styles['BodyDark'],
        ))
    story.append(Spacer(1, 10))

    # ============ WHAT WE DO ============
    story.append(Paragraph("What We Offer", styles['SectionGold']))

    default_services = [
        ("Social Media Management", "Full-service management of Instagram, TikTok, LinkedIn, and more. Content calendar, posting, community management, and growth strategy."),
        ("Content Creation", "Professional copywriting, captions, hashtag strategy, and content pillars tailored to your brand voice and target audience."),
        ("Video Production", "Cinematic short-form video (Reels, TikTok, Shorts) with AI-powered scene generation, voiceover, and motion graphics."),
        ("Visual Design", "Stunning imagery, brand guidelines, and visual assets generated with cutting-edge AI tools and human creative direction."),
        ("Market Research", "In-depth competitor analysis, trend reports, and market intelligence to inform your strategy."),
        ("Email Marketing", "Professional email campaigns, newsletters, and automated sequences to nurture leads and drive conversions."),
        ("Performance Analytics", "Detailed monthly reports with KPIs, engagement metrics, ROI tracking, and actionable recommendations."),
    ]

    if services:
        # Filter to requested services
        svc_list = [s for s in default_services if any(kw.lower() in s[0].lower() for kw in services)]
        if not svc_list:
            svc_list = default_services
    else:
        svc_list = default_services

    for svc_name, svc_desc in svc_list:
        story.append(Paragraph(f"<b>{svc_name}</b>", styles['BodyBold']))
        story.append(Paragraph(svc_desc, styles['BodyDark']))

    # ============ CUSTOM BODY ============
    if custom_body:
        story.append(Paragraph("Our Approach", styles['SectionGold']))
        for para in custom_body.split('\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['BodyDark']))

    # ============ WHY US ============
    story.append(Paragraph("Why Dubai Prod?", styles['SectionGold']))

    why_data = [
        ["AI-Powered", "We use cutting-edge AI tools (DALL-E, Claude, GPT) to produce content 10x faster than traditional agencies."],
        ["Dubai-Based", "Deep understanding of the UAE market, luxury positioning, and regional trends."],
        ["Full-Service Team", "6 specialized AI agents + human oversight ensure quality at every step."],
        ["Results-Driven", "Everything we do is measured. Monthly reports with real KPIs and ROI tracking."],
        ["Fast Delivery", "Most content delivered within 24-48 hours. Videos in under 1 hour."],
    ]

    for title, desc in why_data:
        story.append(Paragraph(f"<b>{title}</b> — {desc}", styles['BodyDark']))

    # ============ CTA ============
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=15))

    cta_table = Table(
        [[Paragraph("Let's Build Something Amazing Together", styles['CTA'])]],
        colWidths=[14*cm],
    )
    cta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(cta_table)
    story.append(Spacer(1, 15))

    # ============ CONTACT / FOOTER ============
    story.append(Paragraph(f"<b>{sender_name}</b>", styles['BodyBold']))
    story.append(Paragraph(f"{sender_title}, Dubai Prod", styles['BodyDark']))
    story.append(Paragraph("Dubai, United Arab Emirates", styles['BodyDark']))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY, spaceAfter=8))
    story.append(Paragraph(
        f"Dubai Prod Agency — Digital Marketing & Content Production — {datetime.now().year}",
        styles['SmallMuted'],
    ))
    story.append(Paragraph("This proposal is confidential and intended for the named recipient only.", styles['SmallMuted']))

    doc.build(story)
    logger.info(f"[template] Marketing PDF generated: {filepath}")
    return f"/uploads/{filename}"
