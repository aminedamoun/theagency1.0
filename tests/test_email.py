"""Test: email reader and sender (requires credentials in .env)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.logger import setup_logger


def test_fetch():
    from email_agent.reader import fetch_emails

    print("--- Fetching last 3 emails ---")
    try:
        emails = fetch_emails(limit=3)
        if not emails:
            print("No emails found.")
            return
        for i, em in enumerate(emails, 1):
            print(f"\n--- Email {i} ---")
            print(em.summary())
    except ValueError as e:
        print(f"Setup needed: {e}")
    except Exception as e:
        print(f"Error: {e}")


def test_send_dry():
    from email_agent.sender import send_email

    print("\n--- Send Test (will ask for confirmation) ---")
    try:
        sent = send_email(
            to="test@example.com",
            subject="Test from Amine Agent",
            body="This is a test email from your personal agent.",
            confirm_callback=lambda preview: (print(preview), False)[1],  # Always cancel
        )
        print(f"Sent: {sent} (expected: False — auto-cancelled)")
    except ValueError as e:
        print(f"Setup needed: {e}")


def main():
    logger = setup_logger()
    logger.info("=== Test: Email Module ===")
    test_fetch()
    test_send_dry()


if __name__ == "__main__":
    main()
