"""Test: scan and organize a temp folder with dummy files."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logger import setup_logger
from files.scanner import scan_directory
from files.organizer import plan_organization, show_plan, execute_plan


def create_dummy_files(base: Path):
    """Create a set of dummy files for testing."""
    dummy_files = [
        "report.pdf",
        "photo.jpg",
        "notes.txt",
        "budget.xlsx",
        "song.mp3",
        "backup.zip",
        "script.py",
        "data.json",
        "presentation.pptx",
        "video.mp4",
        "readme.md",
        "image.png",
        "mystery.xyz",
    ]
    for name in dummy_files:
        (base / name).write_text(f"dummy content for {name}")


def main():
    logger = setup_logger()
    logger.info("=== Test: File Organization ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        create_dummy_files(tmp)

        # Step 1: Scan
        print("--- Scan Results ---")
        scan = scan_directory(tmp)
        print(scan.summary())
        print()

        # Step 2: Plan
        actions = plan_organization(scan)
        plan_text = show_plan(actions)
        print("--- Organization Plan ---")
        print(plan_text)
        print()

        # Step 3: Execute (auto-confirm for test)
        print("--- Executing ---")
        log = execute_plan(actions)
        for entry in log:
            print(f"  {entry}")
        print()

        # Step 4: Verify
        print("--- After Organization ---")
        scan_after = scan_directory(tmp, recursive=True)
        print(scan_after.summary())
        for cat, files in sorted(scan_after.by_category.items()):
            print(f"\n  {cat}/")
            for f in files:
                print(f"    {f.name}")


if __name__ == "__main__":
    main()
