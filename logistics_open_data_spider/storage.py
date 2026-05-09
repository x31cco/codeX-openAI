"""Persistence helpers for downloaded files and crawl metadata."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

import re

try:
    from slugify import slugify
except ModuleNotFoundError:  # pragma: no cover - minimal environment fallback
    def slugify(value: str) -> str:
        value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value).strip("-").lower()
        return value or "item"

from .models import CrawlItem, Source


class CrawlStore:
    """Small SQLite/JSONL backed store for repeatable crawls."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.files_dir = output_dir / "raw"
        self.meta_dir = output_dir / "metadata"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(output_dir / "crawl_state.sqlite3")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS seen_urls (url TEXT PRIMARY KEY, status TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS file_hashes (sha256 TEXT PRIMARY KEY, path TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def has_seen(self, url: str) -> bool:
        row = self.db.execute("SELECT 1 FROM seen_urls WHERE url = ?", (url,)).fetchone()
        return row is not None

    def mark_seen(self, url: str, status: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO seen_urls(url, status, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (url, status),
        )
        self.db.commit()

    def has_hash(self, sha256: str) -> bool:
        row = self.db.execute("SELECT 1 FROM file_hashes WHERE sha256 = ?", (sha256,)).fetchone()
        return row is not None

    def record_hash(self, sha256: str, path: Path) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO file_hashes(sha256, path, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (sha256, str(path)),
        )
        self.db.commit()

    def target_path(self, source: Source, url: str, extension: str | None) -> Path:
        parsed = urlparse(url)
        stem = slugify(Path(parsed.path).stem or parsed.netloc or source.name)[:90]
        ext = extension or Path(parsed.path).suffix or ".bin"
        if not ext.startswith("."):
            ext = f".{ext}"
        folder = self.files_dir / source.category.value / slugify(source.name)[:80]
        folder.mkdir(parents=True, exist_ok=True)
        candidate = folder / f"{stem}{ext}"
        index = 1
        while candidate.exists():
            candidate = folder / f"{stem}-{index}{ext}"
            index += 1
        return candidate

    def append_item(self, item: CrawlItem) -> None:
        path = self.meta_dir / f"{item.category}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True) + "\n")
