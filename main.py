"""Amine Agent — personal local agent."""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from app.logger import setup_logger


USAGE = """\
Amine Agent — personal local agent

Commands:
  python main.py browse "Go to example.com and tell me what you see"
  python main.py scan ~/Downloads
  python main.py scan ~/Downloads --recursive
  python main.py organize ~/Downloads
  python main.py organize ~/Downloads --recursive
  python main.py inbox                       # fetch last 5 emails
  python main.py inbox 10                    # fetch last 10
  python main.py inbox --unread              # unread only
  python main.py send to@email.com "Subject" "Body text"
"""


def cmd_browse(args: list[str]):
    from browser.agent import run_browser_task

    task = " ".join(args)
    if not task:
        print('Usage: python main.py browse "your task"')
        return
    result = asyncio.run(run_browser_task(task))
    print("\n--- Result ---")
    print(result)


def cmd_scan(args: list[str]):
    from files.scanner import scan_directory

    if not args:
        print("Usage: python main.py scan <directory> [--recursive]")
        return
    path = args[0]
    recursive = "--recursive" in args
    scan = scan_directory(path, recursive=recursive)
    print(scan.summary())


def cmd_inbox(args: list[str]):
    from email_agent.reader import fetch_emails

    limit = 5
    unseen_only = "--unread" in args
    for a in args:
        if a.isdigit():
            limit = int(a)

    emails = fetch_emails(limit=limit, unseen_only=unseen_only)
    if not emails:
        print("No emails found.")
        return
    for i, em in enumerate(emails, 1):
        print(f"\n{'='*50}")
        print(f"  Email {i}")
        print(f"{'='*50}")
        print(em.summary())


def cmd_send(args: list[str]):
    from email_agent.sender import send_email

    if len(args) < 3:
        print('Usage: python main.py send to@email.com "Subject" "Body"')
        return
    to, subject, body = args[0], args[1], " ".join(args[2:])
    sent = send_email(to=to, subject=subject, body=body)
    if sent:
        print("Email sent.")
    else:
        print("Send cancelled.")


def cmd_organize(args: list[str]):
    from files.organizer import organize_directory

    if not args:
        print("Usage: python main.py organize <directory> [--recursive]")
        return
    path = args[0]
    recursive = "--recursive" in args
    log = organize_directory(path, recursive=recursive)
    for entry in log:
        print(entry)


def main():
    logger = setup_logger()
    logger.info("Amine Agent started.")

    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "browse": cmd_browse,
        "scan": cmd_scan,
        "organize": cmd_organize,
        "inbox": cmd_inbox,
        "send": cmd_send,
    }

    if command in commands:
        logger.info(f"Command: {command} {' '.join(args)}")
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
