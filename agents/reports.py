"""Report generation — Creates professional PDF reports from agency data."""

import io
import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger("amine-agent")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"

# Brand colors
GOLD = colors.HexColor("#c9a44e")
DARK = colors.HexColor("#0c0c12")
GRAY = colors.HexColor("#888888")
WHITE = colors.white
BG_CARD = colors.HexColor("#1a1a2e")


def _styles():
    """Create custom styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=28, textColor=GOLD, spaceAfter=6,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'],
        fontSize=12, textColor=GRAY, spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=16, textColor=GOLD, spaceBefore=20, spaceAfter=10,
        fontName='Helvetica-Bold',
        borderWidth=1, borderColor=GOLD, borderPadding=4,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor("#333333"),
        spaceAfter=6, leading=14,
    ))
    styles.add(ParagraphStyle(
        'SmallGray', parent=styles['Normal'],
        fontSize=8, textColor=GRAY,
    ))
    return styles


async def generate_full_report(
    title: str = "Agency Report",
    include_clients: bool = True,
    include_tasks: bool = True,
    include_content: bool = True,
    include_activity: bool = True,
    custom_sections: list[dict] = None,
) -> str:
    """Generate a comprehensive PDF report.

    Args:
        title: Report title
        include_*: Which sections to include
        custom_sections: List of {"title": str, "body": str} for custom content

    Returns:
        Web path to the generated PDF (/uploads/report_xxx.pdf)
    """
    from app.database import get_db

    db = await get_db()

    # Gather data
    clients = []
    tasks = []
    content = []
    logs = []

    if include_clients:
        rows = await db.execute_fetchall("SELECT * FROM clients ORDER BY status, name")
        clients = [dict(r) for r in rows]

    if include_tasks:
        rows = await db.execute_fetchall(
            "SELECT t.*, c.name as client_name FROM tasks t "
            "LEFT JOIN clients c ON t.client_id = c.id "
            "ORDER BY CASE t.status WHEN 'in_progress' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END, t.created_at DESC"
        )
        tasks = [dict(r) for r in rows]

    if include_content:
        rows = await db.execute_fetchall(
            "SELECT co.*, c.name as client_name FROM content co "
            "LEFT JOIN clients c ON co.client_id = c.id "
            "ORDER BY co.created_at DESC LIMIT 20"
        )
        content = [dict(r) for r in rows]

    if include_activity:
        rows = await db.execute_fetchall(
            "SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT 30"
        )
        logs = [dict(r) for r in rows]

    # Dashboard stats
    stats_rows = await db.execute_fetchall("SELECT COUNT(*) as c FROM clients WHERE status='active'")
    active_clients = stats_rows[0]["c"]
    rev_rows = await db.execute_fetchall("SELECT COALESCE(SUM(monthly_fee),0) as t FROM clients WHERE status='active'")
    revenue = rev_rows[0]["t"]
    pend_rows = await db.execute_fetchall("SELECT COUNT(*) as c FROM tasks WHERE status='pending'")
    pending = pend_rows[0]["c"]
    prog_rows = await db.execute_fetchall("SELECT COUNT(*) as c FROM tasks WHERE status='in_progress'")
    in_progress = prog_rows[0]["c"]
    done_rows = await db.execute_fetchall("SELECT COUNT(*) as c FROM tasks WHERE status='completed'")
    completed = done_rows[0]["c"]

    await db.close()

    # Build PDF
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{ts}.pdf"
    filepath = UPLOADS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )

    styles = _styles()
    story = []

    # --- Header ---
    story.append(Paragraph("DUBAI PROD AGENCY", styles['ReportTitle']))
    story.append(Paragraph(f"{title} — {datetime.now().strftime('%B %d, %Y')}", styles['ReportSubtitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=20))

    # --- Executive Summary ---
    story.append(Paragraph("Executive Summary", styles['SectionHead']))

    summary_data = [
        ["Active Clients", str(active_clients), "Monthly Revenue", f"${revenue:,.0f}"],
        ["Pending Tasks", str(pending), "In Progress", str(in_progress)],
        ["Completed Tasks", str(completed), "Total Tasks", str(pending + in_progress + completed)],
    ]
    summary_table = Table(summary_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#333333")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, -1), GOLD),
        ('TEXTCOLOR', (3, 0), (3, -1), GOLD),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # --- Custom Sections (research results, etc.) ---
    if custom_sections:
        for sec in custom_sections:
            story.append(Paragraph(sec.get("title", "Section"), styles['SectionHead']))
            body = sec.get("body", "").replace("\n", "<br/>")
            story.append(Paragraph(body, styles['BodyText2']))
            story.append(Spacer(1, 10))

    # --- Clients ---
    if include_clients and clients:
        story.append(Paragraph("Client Portfolio", styles['SectionHead']))
        client_data = [["Name", "Company", "Platform", "Monthly Fee", "Status"]]
        for c in clients:
            client_data.append([
                c.get("name", ""),
                c.get("company", "—"),
                c.get("platform", "—"),
                f"${c.get('monthly_fee', 0):,.0f}",
                c.get("status", ""),
            ])

        client_table = Table(client_data, colWidths=[3.5*cm, 3.5*cm, 3*cm, 2.5*cm, 2*cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GOLD),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 15))

    # --- Tasks ---
    if include_tasks and tasks:
        story.append(Paragraph("Task Overview", styles['SectionHead']))
        task_data = [["Task", "Agent", "Priority", "Status"]]
        for t in tasks[:15]:
            task_data.append([
                Paragraph(t.get("title", "")[:50], styles['BodyText2']),
                t.get("assigned_agent", ""),
                t.get("priority", ""),
                t.get("status", "").replace("_", " "),
            ])

        task_table = Table(task_data, colWidths=[7*cm, 2.5*cm, 2*cm, 3*cm])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GOLD),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(task_table)
        story.append(Spacer(1, 15))

    # --- Content ---
    if include_content and content:
        story.append(Paragraph("Content Pipeline", styles['SectionHead']))
        for c in content[:10]:
            platform = c.get("platform", "").upper()
            ctype = c.get("content_type", "")
            status = c.get("status", "").replace("_", " ")
            caption = c.get("caption", "")[:200]
            client_name = c.get("client_name", "No client")

            story.append(Paragraph(
                f"<b>{platform} — {ctype}</b> [{status}] — {client_name}",
                styles['BodyText2']
            ))
            if caption:
                story.append(Paragraph(
                    f"<i>{caption}</i>",
                    styles['SmallGray']
                ))
            story.append(Spacer(1, 4))

    # --- Agent Activity ---
    if include_activity and logs:
        story.append(Paragraph("Recent Agent Activity", styles['SectionHead']))
        log_data = [["Agent", "Action", "Time"]]
        for l in logs[:15]:
            log_data.append([
                l.get("agent", ""),
                l.get("action", "").replace("_", " "),
                l.get("created_at", "")[:19],
            ])

        log_table = Table(log_data, colWidths=[3*cm, 6*cm, 5.5*cm])
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(log_table)

    # --- Footer ---
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY, spaceAfter=10))
    story.append(Paragraph(
        f"Generated by Dubai Prod Agency AI Platform — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['SmallGray']
    ))

    # Build PDF
    doc.build(story)
    logger.info(f"[report] Generated: {filepath}")

    return f"/uploads/{filename}"
