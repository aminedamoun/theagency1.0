"""Agent Memory — persistent knowledge that makes agents smarter over time.

Each agent has a memory file that stores:
- Client preferences and history
- Past work learnings
- User feedback and corrections
- Domain knowledge they've acquired
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("amine-agent")

MEMORY_DIR = Path(__file__).resolve().parent.parent / "data" / "agent_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _memory_path(agent_key: str) -> Path:
    return MEMORY_DIR / f"{agent_key}.json"


def load_memory(agent_key: str) -> list[dict]:
    """Load agent's memory entries."""
    path = _memory_path(agent_key)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def save_memory(agent_key: str, entries: list[dict]):
    """Save agent's full memory."""
    path = _memory_path(agent_key)
    path.write_text(json.dumps(entries, indent=2, default=str))


def add_memory(agent_key: str, content: str, category: str = "learning"):
    """Add a new memory entry for an agent."""
    entries = load_memory(agent_key)
    entries.append({
        "content": content,
        "category": category,  # learning, feedback, client, preference
        "created_at": datetime.now().isoformat(),
    })
    # Keep max 50 memories per agent
    if len(entries) > 50:
        entries = entries[-50:]
    save_memory(agent_key, entries)
    logger.info(f"[memory] {agent_key}: added {category} memory")


def get_memory_context(agent_key: str) -> str:
    """Format agent memories as context for the system prompt."""
    entries = load_memory(agent_key)
    if not entries:
        return ""

    lines = ["**Your memories (things you've learned and should remember):**"]
    for e in entries[-20:]:  # Last 20 memories
        lines.append(f"- [{e.get('category', 'note')}] {e['content']}")

    return "\n".join(lines)


def clear_memory(agent_key: str):
    """Clear all memories for an agent."""
    path = _memory_path(agent_key)
    if path.exists():
        path.unlink()
