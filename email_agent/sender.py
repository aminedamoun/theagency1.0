"""Send emails via SMTP with mandatory confirmation and attachment support."""

import logging
import os
import smtplib
import mimetypes
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger("amine-agent")


def _get_smtp_connection() -> smtplib.SMTP:
    host = os.getenv("EMAIL_SMTP_HOST", "smtpout.secureserver.net")
    port = int(os.getenv("EMAIL_SMTP_PORT", "465"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not user or not password:
        raise ValueError("EMAIL_USER and EMAIL_PASSWORD must be set in .env.")

    logger.info(f"[email] Connecting to SMTP {host}:{port}")
    if port == 465:
        conn = smtplib.SMTP_SSL(host, port)
    else:
        conn = smtplib.SMTP(host, port)
        conn.ehlo()
        conn.starttls()
        conn.ehlo()
    conn.login(user, password)
    return conn


def _format_preview(to: str, subject: str, body: str, attachments: list = None) -> str:
    att_str = ""
    if attachments:
        att_str = f"\n  Attachments: {', '.join(str(a) for a in attachments)}"
    return (
        f"\n{'='*50}\n"
        f"  To:      {to}\n"
        f"  Subject: {subject}{att_str}\n"
        f"{'='*50}\n"
        f"{body}\n"
        f"{'='*50}"
    )


def send_email(
    to: str,
    subject: str,
    body: str,
    confirm_callback=None,
    attachments: list = None,
) -> bool:
    """Send an email with mandatory confirmation and optional attachments.

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Email body (plain text).
        confirm_callback: A callable that receives the preview string and returns True/False.
                         If None, defaults to interactive input().
        attachments: List of file paths to attach (str or Path).

    Returns:
        True if sent, False if cancelled.
    """
    sender = os.getenv("EMAIL_USER")
    if not sender:
        raise ValueError("EMAIL_USER must be set in .env")

    # Always show preview and ask for confirmation
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

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    # Add attachments
    if attachments:
        for filepath in attachments:
            fp = Path(filepath)
            if not fp.exists():
                # Try relative to project root
                fp = Path(__file__).resolve().parent.parent / filepath.lstrip("/")
            if not fp.exists():
                logger.warning(f"[email] Attachment not found: {filepath}")
                continue

            mime_type, _ = mimetypes.guess_type(str(fp))
            if mime_type is None:
                mime_type = "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)

            with open(fp, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=fp.name,
                )
            logger.info(f"[email] Attached: {fp.name} ({mime_type})")

    conn = _get_smtp_connection()
    try:
        conn.send_message(msg)
        att_count = len(attachments) if attachments else 0
        logger.info(f"[email] Sent email to {to}: {subject} ({att_count} attachments)")
        return True
    finally:
        conn.quit()
