"""Fetch and parse emails via IMAP."""

import imaplib
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.parser import BytesParser

logger = logging.getLogger("amine-agent")


@dataclass
class EmailMessage:
    uid: str
    subject: str
    sender: str
    to: str
    date: str
    body_text: str
    body_html: str

    def summary(self, max_body: int = 200) -> str:
        body = self.body_text[:max_body]
        if len(self.body_text) > max_body:
            body += "..."
        return (
            f"From: {self.sender}\n"
            f"To: {self.to}\n"
            f"Date: {self.date}\n"
            f"Subject: {self.subject}\n"
            f"Body: {body}"
        )


def _get_imap_connection() -> imaplib.IMAP4_SSL:
    host = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
    port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not user or not password:
        raise ValueError(
            "EMAIL_USER and EMAIL_PASSWORD must be set in .env. "
            "For Gmail, use an App Password: https://myaccount.google.com/apppasswords"
        )

    logger.info(f"[email] Connecting to {host}:{port} as {user}")
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, password)
    return conn


def _parse_message(raw: bytes) -> EmailMessage:
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not body_text:
                body_text = part.get_content()
            elif ct == "text/html" and not body_html:
                body_html = part.get_content()
    else:
        ct = msg.get_content_type()
        content = msg.get_content()
        if ct == "text/plain":
            body_text = content
        elif ct == "text/html":
            body_html = content

    return EmailMessage(
        uid="",
        subject=str(msg.get("Subject", "(no subject)")),
        sender=str(msg.get("From", "")),
        to=str(msg.get("To", "")),
        date=str(msg.get("Date", "")),
        body_text=body_text,
        body_html=body_html,
    )


def fetch_emails(
    folder: str = "INBOX",
    limit: int = 5,
    unseen_only: bool = False,
) -> list[EmailMessage]:
    """Fetch recent emails from the specified folder.

    Args:
        folder: IMAP folder name (default: INBOX).
        limit: Max number of emails to fetch.
        unseen_only: If True, only fetch unread emails.

    Returns:
        List of EmailMessage objects, newest first.
    """
    conn = _get_imap_connection()

    try:
        conn.select(folder, readonly=True)
        criteria = "UNSEEN" if unseen_only else "ALL"
        status, data = conn.search(None, criteria)

        if status != "OK":
            logger.error(f"[email] Search failed: {status}")
            return []

        uids = data[0].split()
        if not uids:
            logger.info("[email] No emails found.")
            return []

        # Get the most recent ones
        uids = uids[-limit:]
        uids.reverse()

        messages = []
        for uid in uids:
            status, msg_data = conn.fetch(uid, "(RFC822)")
            if status == "OK" and msg_data[0]:
                raw = msg_data[0][1]
                email_msg = _parse_message(raw)
                email_msg.uid = uid.decode()
                messages.append(email_msg)

        logger.info(f"[email] Fetched {len(messages)} emails from {folder}")
        return messages

    finally:
        conn.logout()
