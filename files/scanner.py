"""Scan directories and categorize files."""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("amine-agent")

CATEGORIES = {
    "documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".md"},
    "spreadsheets": {".xls", ".xlsx", ".csv", ".numbers", ".ods"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic", ".tiff"},
    "videos": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
    "audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"},
    "archives": {".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"},
    "code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".go", ".rs", ".rb", ".sh"},
    "data": {".json", ".xml", ".yaml", ".yml", ".sql", ".db", ".sqlite"},
    "presentations": {".ppt", ".pptx", ".key", ".odp"},
}


def _get_category(suffix: str) -> str:
    suffix = suffix.lower()
    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category
    return "other"


@dataclass
class FileInfo:
    path: Path
    name: str
    suffix: str
    category: str
    size_bytes: int
    modified: datetime

    @property
    def size_human(self) -> str:
        size = self.size_bytes
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class ScanResult:
    directory: Path
    files: list[FileInfo] = field(default_factory=list)
    total_size: int = 0

    @property
    def by_category(self) -> dict[str, list[FileInfo]]:
        result: dict[str, list[FileInfo]] = {}
        for f in self.files:
            result.setdefault(f.category, []).append(f)
        return result

    def summary(self) -> str:
        lines = [f"Scanned: {self.directory}", f"Total files: {len(self.files)}"]
        for cat, files in sorted(self.by_category.items()):
            total = sum(f.size_bytes for f in files)
            size = FileInfo(Path(), "", "", "", total, datetime.now()).size_human
            lines.append(f"  {cat}: {len(files)} files ({size})")
        return "\n".join(lines)


def scan_directory(path: str | Path, recursive: bool = False) -> ScanResult:
    """Scan a directory and return categorized file info."""
    directory = Path(path).expanduser().resolve()

    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    logger.info(f"[files] Scanning: {directory} (recursive={recursive})")

    result = ScanResult(directory=directory)
    pattern = "**/*" if recursive else "*"

    for item in directory.glob(pattern):
        if item.is_file() and not item.name.startswith("."):
            stat = item.stat()
            info = FileInfo(
                path=item,
                name=item.name,
                suffix=item.suffix,
                category=_get_category(item.suffix),
                size_bytes=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
            )
            result.files.append(info)
            result.total_size += stat.st_size

    result.files.sort(key=lambda f: f.name)
    logger.info(f"[files] Found {len(result.files)} files")
    return result
