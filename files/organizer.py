"""Organize files by category with confirmation before any move."""

import logging
import shutil
from pathlib import Path
from dataclasses import dataclass

from files.scanner import scan_directory, ScanResult

logger = logging.getLogger("amine-agent")


@dataclass
class MoveAction:
    source: Path
    destination: Path
    category: str


def plan_organization(scan: ScanResult) -> list[MoveAction]:
    """Create a plan to organize files into category folders. Does NOT move anything."""
    actions = []
    base = scan.directory

    for category, files in scan.by_category.items():
        target_dir = base / category
        for f in files:
            # Skip if already in the right folder
            if f.path.parent == target_dir:
                continue
            dest = target_dir / f.name
            # Handle name collisions
            if dest.exists() or any(a.destination == dest for a in actions):
                stem = f.path.stem
                suffix = f.path.suffix
                counter = 1
                while True:
                    dest = target_dir / f"{stem}_{counter}{suffix}"
                    if not dest.exists() and not any(a.destination == dest for a in actions):
                        break
                    counter += 1
            actions.append(MoveAction(source=f.path, destination=dest, category=category))

    return actions


def show_plan(actions: list[MoveAction]) -> str:
    """Format the move plan as a readable string."""
    if not actions:
        return "No files to organize — everything is already in place."

    lines = ["Proposed file organization:"]
    by_cat: dict[str, list[MoveAction]] = {}
    for a in actions:
        by_cat.setdefault(a.category, []).append(a)

    for cat, moves in sorted(by_cat.items()):
        lines.append(f"\n  [{cat}/]")
        for m in moves:
            lines.append(f"    {m.source.name} -> {cat}/{m.destination.name}")

    lines.append(f"\nTotal: {len(actions)} files to move")
    return "\n".join(lines)


def execute_plan(actions: list[MoveAction], dry_run: bool = False) -> list[str]:
    """Execute the move plan. Returns a log of actions taken."""
    log = []

    for action in actions:
        if dry_run:
            msg = f"[DRY RUN] Would move: {action.source} -> {action.destination}"
            logger.info(msg)
            log.append(msg)
            continue

        action.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(action.source), str(action.destination))
        msg = f"Moved: {action.source.name} -> {action.category}/{action.destination.name}"
        logger.info(f"[files] {msg}")
        log.append(msg)

    return log


def organize_directory(
    path: str | Path,
    recursive: bool = False,
    confirm_callback=None,
) -> list[str]:
    """Scan, plan, confirm, and organize files.

    Args:
        path: Directory to organize.
        recursive: Whether to scan subdirectories.
        confirm_callback: A callable that receives the plan string and returns True/False.
                         If None, defaults to interactive input().
    """
    scan = scan_directory(path, recursive=recursive)

    if not scan.files:
        logger.info("[files] No files found to organize.")
        return ["No files found."]

    actions = plan_organization(scan)
    plan_text = show_plan(actions)

    if not actions:
        return [plan_text]

    # Always ask before moving
    if confirm_callback:
        approved = confirm_callback(plan_text)
    else:
        print(plan_text)
        answer = input("\nProceed? (yes/no): ").strip().lower()
        approved = answer in ("yes", "y")

    if not approved:
        logger.info("[files] Organization cancelled by user.")
        return ["Cancelled by user."]

    return execute_plan(actions)
