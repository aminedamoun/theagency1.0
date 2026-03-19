"""Send emails via SMTP with confirmation and attachment support.

Supports:
- Microsoft 365 / Outlook (smtp.office365.com:587) — requires SMTP AUTH enabled
- GoDaddy (smtpout.secureserver.net:465) — SSL
- Any custom SMTP server via .env

If the primary SMTP fails, automatically tries GoDaddy as fallback.
"""

import logging
import os
import re
import smtplib
import mimetypes
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

logger = logging.getLogger("amine-agent")

# SMTP configs to try in order
SMTP_CONFIGS = [
    {
        "name": "Office365",
        "host": "smtp.office365.com",
        "port": 587,
        "ssl": False,
        "starttls": True,
    },
    {
        "name": "GoDaddy-SSL",
        "host": "smtpout.secureserver.net",
        "port": 465,
        "ssl": True,
        "starttls": False,
    },
    {
        "name": "GoDaddy-TLS",
        "host": "smtpout.secureserver.net",
        "port": 587,
        "ssl": False,
        "starttls": True,
    },
]


def _try_connect(host, port, user, password, use_ssl=False, use_starttls=True):
    """Try to connect and authenticate to an SMTP server."""
    if use_ssl:
        conn = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        conn = smtplib.SMTP(host, port, timeout=15)
        conn.ehlo()
        if use_starttls:
            conn.starttls()
            conn.ehlo()
    conn.login(user, password)
    return conn


def _get_smtp_connection() -> smtplib.SMTP:
    """Connect to SMTP — tries configured host first, then fallbacks."""
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not user or not password:
        raise ValueError("EMAIL_USER and EMAIL_PASSWORD must be set in .env.")

    # Try the configured host first
    configured_host = os.getenv("EMAIL_SMTP_HOST", "smtp.office365.com")
    configured_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))

    # Build ordered list: configured first, then fallbacks
    configs = [
        {
            "name": "Configured",
            "host": configured_host,
            "port": configured_port,
            "ssl": configured_port == 465,
            "starttls": configured_port != 465,
        }
    ]
    # Add other configs that aren't duplicates
    for cfg in SMTP_CONFIGS:
        if cfg["host"] != configured_host or cfg["port"] != configured_port:
            configs.append(cfg)

    last_error = None
    for cfg in configs:
        try:
            logger.info(f"[email] Trying {cfg['name']} ({cfg['host']}:{cfg['port']})...")
            conn = _try_connect(
                cfg["host"], cfg["port"], user, password,
                use_ssl=cfg["ssl"], use_starttls=cfg["starttls"]
            )
            logger.info(f"[email] ✅ Connected via {cfg['name']}")
            return conn
        except Exception as e:
            last_error = e
            logger.warning(f"[email] ❌ {cfg['name']} failed: {e}")
            continue

    raise ConnectionError(
        f"All SMTP servers failed. Last error: {last_error}\n"
        f"For Office365: Enable SMTP AUTH in admin.microsoft.com → Users → Mail → Manage email apps\n"
        f"Or switch to GoDaddy SMTP: set EMAIL_SMTP_HOST=smtpout.secureserver.net EMAIL_SMTP_PORT=465"
    )


def _format_preview(to: str, subject: str, body: str, attachments: list = None) -> str:
    att_str = ""
    if attachments:
        att_str = f"\n  Attachments: {', '.join(str(a) for a in attachments)}"
    return (
        f"\n{'='*50}\n"
        f"  To:      {to}\n"
        f"  Subject: {subject}{att_str}\n"
        f"{'='*50}\n"
        f"{body[:200]}...\n"
        f"{'='*50}"
    )


def send_email(
    to: str,
    subject: str,
    body: str,
    confirm_callback=None,
    attachments: list = None,
) -> bool:
    """Send an email with confirmation and optional attachments.

    Supports HTML body — if body contains '<' tags, sends as HTML.

    Returns True if sent, False if cancelled.
    """
    sender = os.getenv("EMAIL_USER")
    sender_name = os.getenv("EMAIL_SENDER_NAME", "Dubai Prod")
    if not sender:
        raise ValueError("EMAIL_USER must be set in .env")

    # Confirmation
    preview = _format_preview(to, subject, body, attachments)
    if confirm_callback:
        approved = confirm_callback(preview)
    else:
        print(preview)
        answer = input("\nSend this email? (yes/no): ").strip().lower()
        approved = answer in ("yes", "y")

    if not approved:
        logger.info("[email] Send cancelled by user.")
        return False

    # Detect HTML
    is_html = bool(re.search(r'<[a-z][\s\S]*>', body, re.IGNORECASE)) if body else False

    # Build message
    if is_html:
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{sender_name} <{sender}>"
        msg["To"] = to
        msg["Subject"] = subject
        html_part = MIMEText(body, "html", "utf-8")
        msg.attach(html_part)
    else:
        msg = EmailMessage()
        msg["From"] = f"{sender_name} <{sender}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

    # Attachments
    if attachments:
        for filepath in attachments:
            fp = Path(filepath)
            if not fp.exists():
                fp = Path(__file__).resolve().parent.parent / filepath.lstrip("/")
            if not fp.exists():
                logger.warning(f"[email] Attachment not found: {filepath}")
                continue

            mime_type, _ = mimetypes.guess_type(str(fp))
            if mime_type is None:
                mime_type = "application/octet-stream"

            if is_html:
                maintype, subtype = mime_type.split("/", 1)
                part = MIMEBase(maintype, subtype)
                with open(fp, "rb") as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={fp.name}")
                msg.attach(part)
            else:
                maintype, subtype = mime_type.split("/", 1)
                with open(fp, "rb") as f:
                    msg.add_attachment(
                        f.read(), maintype=maintype, subtype=subtype,
                        filename=fp.name,
                    )
            logger.info(f"[email] Attached: {fp.name}")

    # Send with auto-fallback
    conn = _get_smtp_connection()
    try:
        conn.send_message(msg)
        att_count = len(attachments) if attachments else 0
        logger.info(f"[email] ✅ Sent to {to}: {subject} ({att_count} attachments)")
        return True
    finally:
        try:
            conn.quit()
        except Exception:
            pass
