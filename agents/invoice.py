"""Invoice generator — matches Dubai Prod / CLIPIFLY FZC LLC official invoice format."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

logger = logging.getLogger("amine-agent")

UPLOADS_DIR  = Path(__file__).resolve().parent.parent / "uploads"
INVOICES_DIR = UPLOADS_DIR / "invoices"
LOGO_PATH    = UPLOADS_DIR / "dubai_prod_logo.png"

# ── Company details (from official invoices) ─────────────────────────────────
COMPANY = {
    "name":     "CLIPIFLY FZC LLC.",
    "address1": "AMBER GEM TOWER",
    "address2": "AJMAN • UNITED ARAB EMIRATES",
    "phone":    "+971 5256 16853",
    "email":    "info@dubaiprod.com",
    "website":  "www.dubaiprod.com",
    "trn":      "104786984500001",
    "bank_name":   "MASHREQ NEO",
    "bank_account":"019101579762",
    "iban":        "AE21 0330 0000 1910 1579 762",
    "swift":       "BOMLAEAD",
}

# ── Colors ────────────────────────────────────────────────────────────────────
BLACK  = colors.HexColor("#0F0F0F")
GOLD   = colors.HexColor("#C8A84B")
GREY   = colors.HexColor("#666666")
LGREY  = colors.HexColor("#F2F2F2")
DGREY  = colors.HexColor("#333333")
WHITE  = colors.white
BLUE   = colors.HexColor("#1a3a5c")


def _s(name, **kw):
    return ParagraphStyle(name=name, **kw)


def _next_invoice_number() -> str:
    """Auto-increment invoice number stored in a small counter file."""
    counter_file = INVOICES_DIR / ".counter"
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    year = datetime.now().year
    if counter_file.exists():
        try:
            data = counter_file.read_text().strip().split(":")
            if data[0] == str(year):
                n = int(data[1]) + 1
            else:
                n = 1001
        except Exception:
            n = 1001
    else:
        n = 1001
    counter_file.write_text(f"{year}:{n}")
    return f"{year}-{n}"


async def generate_invoice(
    client: dict,
    items: list,          # [{"description": "...", "qty": 1, "price": 5000}]
    invoice_number: str = None,
    due_days: int = 15,
    notes: str = "",
) -> str:
    """Generate a PDF invoice matching Dubai Prod official format. Returns web path."""

    INVOICES_DIR.mkdir(parents=True, exist_ok=True)

    today    = datetime.now()
    inv_num  = invoice_number or _next_invoice_number()
    safe     = client.get("name", "client").replace(" ", "_").replace("/", "-")
    filename = f"{inv_num}_{safe}.pdf"
    out_path = INVOICES_DIR / filename

    W, H = A4  # 595 x 842 pts
    MARGIN = 18 * mm

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=12 * mm, bottomMargin=16 * mm,
    )
    UW = W - 2 * MARGIN  # usable width ≈ 559 pts

    story = []

    # ══════════════════════════════════════════════════════════════════════
    # HEADER — logo left, invoice date+number right
    # ══════════════════════════════════════════════════════════════════════
    if LOGO_PATH.exists():
        logo = RLImage(str(LOGO_PATH), width=22*mm, height=22*mm)
    else:
        logo = Paragraph(
            '<font size="18"><b>Dubai Prod</b></font>',
            _s("lf", fontName="Helvetica-Bold")
        )

    company_block = Paragraph(
        f'<font size="13"><b>{COMPANY["name"]}</b></font><br/>'
        f'<font size="8" color="#666666">{COMPANY["address1"]}<br/>'
        f'{COMPANY["address2"]}<br/>'
        f'PHONE: {COMPANY["phone"]}<br/>'
        f'EMAIL: {COMPANY["email"]}<br/>'
        f'WEBSITE: {COMPANY["website"]}<br/>'
        f'TRN: {COMPANY["trn"]}</font>',
        _s("cb", fontName="Helvetica", leading=13)
    )

    inv_details = Paragraph(
        f'<font size="9"><b>Invoice Date:</b>  {today.strftime("%d.%m.%Y")}<br/>'
        f'<b>Invoice No.:</b>  {inv_num}</font>',
        _s("id", fontName="Helvetica", alignment=TA_RIGHT, leading=16)
    )

    header_table = Table(
        [[logo, company_block, inv_details]],
        colWidths=[26*mm, UW * 0.55, UW * 0.32],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (1,0), (1,0),   6),
        ("RIGHTPADDING",  (-1,0),(-1,0),  0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)

    # Gold divider
    story.append(HRFlowable(width=UW, thickness=1.5, color=GOLD, spaceAfter=4*mm))

    # ══════════════════════════════════════════════════════════════════════
    # CLIENT INFO — "Company Info"
    # ══════════════════════════════════════════════════════════════════════
    story.append(Paragraph(
        '<font size="9" color="#666666"><b>Company Info</b></font>',
        _s("ci_lbl", fontName="Helvetica-Bold")
    ))
    story.append(Spacer(1, 2*mm))

    client_name    = client.get("name", "")
    client_company = client.get("company", "")
    client_trn     = client.get("trn", "")
    client_tl      = client.get("tl_number", "")
    client_address = client.get("address", "")

    client_lines = f'<font size="11"><b>{client_name}</b></font>'
    if client_company:
        client_lines += f'<br/><font size="10">{client_company}</font>'
    if client_address:
        client_lines += f'<br/><font size="9" color="#555555">{client_address}</font>'
    if client_tl:
        client_lines += f'<br/><font size="9" color="#555555">TL number: {client_tl}</font>'
    if client_trn:
        client_lines += f'<br/><font size="9" color="#555555">TRN: {client_trn}</font>'

    story.append(Paragraph(client_lines, _s("cl", fontName="Helvetica", leading=15)))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width=UW, thickness=0.5, color=LGREY, spaceAfter=3*mm))

    # ══════════════════════════════════════════════════════════════════════
    # ITEMS TABLE
    # ══════════════════════════════════════════════════════════════════════
    def _cell(txt, bold=False, align=TA_LEFT, size=10, color=BLACK):
        return Paragraph(
            f'<font size="{size}" color="{"#0f0f0f" if color==BLACK else "#ffffff"}">'
            f'{"<b>" if bold else ""}{txt}{"</b>" if bold else ""}</font>',
            _s("tc", fontName="Helvetica-Bold" if bold else "Helvetica",
               alignment=align, leading=14)
        )

    # Column headers
    rows = [[
        _cell("Particulars",      bold=True, color=WHITE),
        _cell("Amount in\nAED",   bold=True, align=TA_CENTER, color=WHITE),
        _cell("Total in\nAED",    bold=True, align=TA_RIGHT, color=WHITE),
    ]]

    # Project Name row (like in original)
    rows.append([
        _cell("Project Name", bold=True, size=9),
        _cell("", size=9),
        _cell("", size=9),
    ])

    total_amount = 0
    for item in items:
        qty   = item.get("qty", 1)
        price = float(item.get("price", 0))
        line  = qty * price
        total_amount += line
        rows.append([
            _cell(item.get("description", ""), size=10),
            _cell(f"{price:,.2f}".replace(",", " ").replace(".", ","), align=TA_CENTER, size=10),
            _cell(f"{line:,.2f}".replace(",", " ").replace(".", ","), align=TA_RIGHT, size=10),
        ])

    # Total row
    rows.append([
        _cell("TOTAL AMOUNT    AMOUNT", bold=True, size=10),
        _cell(f"AED: AMOUNT", bold=True, align=TA_CENTER, size=9),
        _cell(f"{total_amount:,.2f}".replace(",", " ").replace(".", ","), bold=True, align=TA_RIGHT, size=10),
    ])

    n = len(rows)
    item_table = Table(rows, colWidths=[UW * 0.58, UW * 0.22, UW * 0.20])
    item_table.setStyle(TableStyle([
        # Header bg
        ("BACKGROUND",    (0,0),  (-1,0),  BLUE),
        ("TEXTCOLOR",     (0,0),  (-1,0),  WHITE),
        ("TOPPADDING",    (0,0),  (-1,0),  8),
        ("BOTTOMPADDING", (0,0),  (-1,0),  8),
        # Project Name row
        ("BACKGROUND",    (0,1),  (-1,1),  LGREY),
        ("TOPPADDING",    (0,1),  (-1,1),  5),
        ("BOTTOMPADDING", (0,1),  (-1,1),  5),
        # Data rows
        ("TOPPADDING",    (0,2),  (-1,n-2), 7),
        ("BOTTOMPADDING", (0,2),  (-1,n-2), 7),
        ("ROWBACKGROUNDS",(0,2),  (-1,n-2), [WHITE, LGREY]),
        # Total row
        ("BACKGROUND",    (0,n-1),(-1,n-1), colors.HexColor("#E8E0C8")),
        ("TOPPADDING",    (0,n-1),(-1,n-1), 9),
        ("BOTTOMPADDING", (0,n-1),(-1,n-1), 9),
        # Grid
        ("GRID",          (0,0),  (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("LINEBELOW",     (0,0),  (-1,0),  1.0, GOLD),
        ("LINEBELOW",     (0,n-1),(-1,n-1),1.5, GOLD),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 6*mm))

    # ══════════════════════════════════════════════════════════════════════
    # PAYMENT DETAILS
    # ══════════════════════════════════════════════════════════════════════
    payment_data = [
        [
            Paragraph('<font size="10"><b>Payment Mode:</b>  Received in Bank</font>',
                      _s("pm", fontName="Helvetica")),
            "",
        ],
        [
            Paragraph(
                f'<font size="10"><b>Bank Account Details -AED</b><br/>'
                f'{COMPANY["name"]}<br/>'
                f'ACCOUNT NO: {COMPANY["bank_account"]}<br/>'
                f'IBAN # {COMPANY["iban"]}<br/>'
                f'{COMPANY["bank_name"]}<br/>'
                f'SWIFT CODE: {COMPANY["swift"]}</font>',
                _s("bd", fontName="Helvetica", leading=14)
            ),
            "",
        ],
    ]
    pay_table = Table(payment_data, colWidths=[UW * 0.65, UW * 0.35])
    pay_table.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("BACKGROUND",   (0,0), (-1,-1), LGREY),
        ("BOX",          (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
    ]))
    story.append(pay_table)

    if notes:
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(
            f'<font size="9" color="#666666">Note: {notes}</font>',
            _s("nt", fontName="Helvetica")
        ))

    # ══════════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=UW, thickness=0.5, color=GOLD))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<font size="8" color="#888888">This is a Computer Generated Invoice does not require signature</font>',
        _s("footer", fontName="Helvetica", alignment=TA_CENTER)
    ))

    doc.build(story)
    logger.info(f"[invoice] Generated: {out_path.name}")
    return f"/uploads/invoices/{filename}"


# Owner's WhatsApp number — always receives a copy
OWNER_PHONE = "+971543333587"


def _format_whatsapp_number(phone: str) -> str:
    """Normalize phone number for wa.me links — digits only, no leading +."""
    import re
    digits = re.sub(r'\D', '', phone)
    # If starts with 00, replace with nothing (international prefix)
    if digits.startswith("00"):
        digits = digits[2:]
    # UAE local numbers starting with 0 → replace 0 with 971
    if digits.startswith("0") and len(digits) <= 10:
        digits = "971" + digits[1:]
    return digits


def build_whatsapp_links(client: dict, invoice_number: str, amount: float, drive_link: str = "") -> dict:
    """
    Build WhatsApp deep links for client + owner copy.
    Returns {"client_url": ..., "owner_url": ..., "message": ...}
    """
    import urllib.parse

    client_name = client.get("name", "")
    asset_line  = f"\n📎 Invoice PDF: {drive_link}" if drive_link else ""

    # Message to client
    client_msg = (
        f"Hello {client_name} 👋\n\n"
        f"Please find your invoice from *Dubai Prod*:\n\n"
        f"🧾 *Invoice #:* {invoice_number}\n"
        f"💰 *Amount:* AED {amount:,.2f}\n"
        f"📅 *Due:* within 15 days{asset_line}\n\n"
        f"*Bank Transfer:*\n"
        f"CLIPIFLY FZC LLC.\n"
        f"IBAN: {COMPANY['iban']}\n"
        f"MASHREQ NEO | SWIFT: {COMPANY['swift']}\n\n"
        f"Thank you! 🙏\n"
        f"Dubai Prod — {COMPANY['website']}"
    )

    # Copy message to owner
    owner_msg = (
        f"📋 *Invoice Sent — Copy for you*\n\n"
        f"Client: *{client_name}*\n"
        f"Invoice #: {invoice_number}\n"
        f"Amount: *AED {amount:,.2f}*\n"
        f"Phone: {client.get('phone', 'N/A')}{asset_line}"
    )

    client_phone = _format_whatsapp_number(client.get("phone", ""))
    owner_phone  = _format_whatsapp_number(OWNER_PHONE)

    client_url = f"https://wa.me/{client_phone}?text={urllib.parse.quote(client_msg)}" if client_phone else None
    owner_url  = f"https://wa.me/{owner_phone}?text={urllib.parse.quote(owner_msg)}"

    return {
        "client_url":   client_url,
        "owner_url":    owner_url,
        "message":      client_msg,
        "client_phone": client_phone,
    }


async def _upload_media_to_meta(file_path: str) -> str:
    """Upload a file to Meta's servers and return the media ID."""
    import os, httpx
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        return ""
    url = f"https://graph.facebook.com/v22.0/{phone_id}/media"
    try:
        from pathlib import Path
        fp = Path(file_path)
        if not fp.exists():
            logger.error(f"[invoice] File not found for upload: {file_path}")
            return ""
        async with httpx.AsyncClient(timeout=30) as c:
            res = await c.post(url,
                data={"messaging_product": "whatsapp", "type": "application/pdf"},
                files={"file": (fp.name, open(fp, "rb"), "application/pdf")},
                headers={"Authorization": f"Bearer {token}"},
            )
            if res.status_code == 200:
                media_id = res.json().get("id", "")
                logger.info(f"[invoice] Uploaded to Meta: {fp.name} → {media_id}")
                return media_id
            else:
                logger.error(f"[invoice] Media upload failed: {res.text}")
                return ""
    except Exception as e:
        logger.error(f"[invoice] Media upload error: {e}")
        return ""


async def _send_whatsapp_cloud(phone: str, message: str, document_path: str = "") -> bool:
    """Send a WhatsApp message (with optional PDF attachment) via Meta Cloud API."""
    import os, httpx
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        return False
    digits = _format_whatsapp_number(phone)
    if not digits:
        return False
    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as c:
            # Send document if path provided
            if document_path:
                media_id = await _upload_media_to_meta(document_path)
                if media_id:
                    from pathlib import Path as _P
                    res = await c.post(url, json={
                        "messaging_product": "whatsapp",
                        "to": digits,
                        "type": "document",
                        "document": {
                            "id": media_id,
                            "caption": message,
                            "filename": _P(document_path).name,
                        },
                    }, headers=headers)
                    return res.status_code == 200

            # Fallback: send text only
            res = await c.post(url, json={
                "messaging_product": "whatsapp",
                "to": digits,
                "type": "text",
                "text": {"body": message},
            }, headers=headers)
            return res.status_code == 200
    except Exception as e:
        logger.error(f"[invoice] WhatsApp Cloud API failed: {e}")
        return False


async def send_invoice_whatsapp(client: dict, invoice_number: str, amount: float, drive_link: str = "", pdf_path: str = "") -> dict:
    """
    Send invoice via WhatsApp Cloud API (works on Railway, no local browser needed).
    Falls back to wa.me links if Cloud API not configured.
    """
    import os, asyncio
    from pathlib import Path as _P

    links = build_whatsapp_links(client, invoice_number, amount, drive_link)
    sent_to = []

    # Resolve PDF path
    doc_path = ""
    if pdf_path:
        local = _P(__file__).resolve().parent.parent / "uploads" / "invoices" / _P(pdf_path).name
        if local.exists():
            doc_path = str(local)
        elif _P(pdf_path).exists():
            doc_path = pdf_path

    # Try Cloud API first (works on Railway 24/7)
    if os.getenv("WHATSAPP_TOKEN"):
        # Send to client (with PDF)
        client_phone = client.get("phone", "")
        if client_phone:
            ok = await _send_whatsapp_cloud(client_phone, links["message"], document_path=doc_path)
            if ok:
                sent_to.append(f"Client ({client.get('name')}) — {client_phone}")
                logger.info(f"[invoice] WhatsApp sent to client: {client.get('name')}")

        # Send owner copy (with PDF)
        owner_msg = (
            f"📋 *Invoice Sent — Copy for you*\n\n"
            f"Client: *{client.get('name', '')}*\n"
            f"Invoice #: {invoice_number}\n"
            f"Amount: *AED {amount:,.2f}*\n"
            f"Phone: {client.get('phone', 'N/A')}"
            + (f"\n📎 Drive: {drive_link}" if drive_link else "")
        )
        ok = await _send_whatsapp_cloud(OWNER_PHONE, owner_msg, document_path=doc_path)
        if ok:
            sent_to.append(f"You (owner copy) — {OWNER_PHONE}")
            logger.info(f"[invoice] WhatsApp owner copy sent")
    else:
        # Fallback: open wa.me links in browser (local only)
        import webbrowser
        if links["client_url"] and client.get("phone"):
            await asyncio.to_thread(webbrowser.open, links["client_url"])
            sent_to.append(f"Client ({client.get('name')}) — {client.get('phone')}")
            await asyncio.sleep(1.5)
        await asyncio.to_thread(webbrowser.open, links["owner_url"])
        sent_to.append(f"You (owner copy) — {OWNER_PHONE}")

    # Update sheet to Sent
    await _mark_invoice_sent(invoice_number)

    return {
        "status":       "whatsapp_sent" if sent_to else "whatsapp_failed",
        "opened_for":   sent_to,
        "client_url":   links["client_url"],
        "owner_url":    links["owner_url"],
        "message":      f"WhatsApp sent to: {', '.join(sent_to)}." if sent_to else "WhatsApp send failed.",
    }


async def send_invoice_email(client: dict, invoice_path: str, invoice_number: str, amount: float) -> bool:
    """Send the invoice PDF link to the client by email."""
    from email_agent.sender import send_email
    import asyncio

    to_email = client.get("email", "")
    if not to_email:
        logger.warning(f"[invoice] No email for {client.get('name')}")
        return False

    subject = f"Invoice {invoice_number} — Dubai Prod"
    body = (
        f"Dear {client.get('name', '')},\n\n"
        f"Please find your invoice {invoice_number} for AED {amount:,.2f} attached.\n\n"
        f"Payment is due within 15 days of receipt.\n\n"
        f"Bank Transfer Details:\n"
        f"  {COMPANY['name']}\n"
        f"  IBAN: {COMPANY['iban']}\n"
        f"  {COMPANY['bank_name']}  |  SWIFT: {COMPANY['swift']}\n\n"
        f"For any questions please contact us at {COMPANY['email']} or {COMPANY['phone']}.\n\n"
        f"Thank you for your business!\n\n"
        f"Best regards,\nDubai Prod Team\n{COMPANY['website']}"
    )

    try:
        sent = await asyncio.to_thread(
            send_email, to=to_email, subject=subject, body=body,
            confirm_callback=lambda _: True,
        )
        if sent:
            logger.info(f"[invoice] Emailed to {to_email}")
            await _mark_invoice_sent(invoice_number)
        return sent
    except Exception as e:
        logger.error(f"[invoice] Email error: {e}")
        return False


async def _mark_invoice_sent(invoice_number: str):
    """Update 🧾 Invoices sheet row to Sent 📤."""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        if not sheet_id:
            return
        from agents.google_sync import _sheets_service
        service = _sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="🧾 Invoices!A:A"
        ).execute()
        for i, row in enumerate(result.get("values", [])):
            if row and row[0] == invoice_number:
                today = datetime.now().strftime("%Y-%m-%d")
                service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f"🧾 Invoices!F{i+1}:G{i+1}",
                    valueInputOption="RAW",
                    body={"values": [["Sent 📤", today]]},
                ).execute()
                break
    except Exception as e:
        logger.warning(f"[invoice] Sheet update error: {e}")
