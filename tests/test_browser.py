"""Test: open Hacker News and report the top 5 headlines."""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logger import setup_logger
from browser.agent import run_browser_task


def main():
    logger = setup_logger()
    logger.info("=== Test: Browser Agent ===")

    task = (
        "Go to https://news.ycombinator.com. "
        "Extract the page title and the top 5 headlines. "
        "Return them as a numbered list."
    )

    result = asyncio.run(run_browser_task(task))
    print("\n--- Result ---")
    print(result)


if __name__ == "__main__":
    main()
