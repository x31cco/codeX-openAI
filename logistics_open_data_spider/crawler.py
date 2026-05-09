"""Async crawler for public logistics open-data resources."""
from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

try:
    import aiohttp
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal environments
    aiohttp = None

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - fallback parser keeps helper code usable
    BeautifulSoup = None
from html.parser import HTMLParser

from .models import DOCUMENT_CONTENT_TYPES, DOCUMENT_EXTENSIONS, CrawlItem, Source
from .storage import CrawlStore

HTML_TYPES = ("text/html", "application/xhtml+xml")
DEFAULT_USER_AGENT = "LogisticsOpenDataSpider/0.1 (+open-data research crawler)"


@dataclass
class CrawlStats:
    pages_seen: int = 0
    files_downloaded: int = 0
    files_skipped: int = 0
    errors: int = 0


class LogisticsCrawler:
    """Polite, resumable crawler for mixed public pages and raw files."""

    def __init__(
        self,
        sources: tuple[Source, ...],
        output_dir: Path,
        *,
        concurrency: int = 4,
        request_timeout: int = 40,
        per_host_delay: float = 0.8,
        max_pages_per_source: int = 200,
        max_files_per_source: int = 100,
        user_agent: str = DEFAULT_USER_AGENT,
        respect_robots: bool = True,
        dry_run: bool = False,
    ) -> None:
        self.sources = sources
        self.store = CrawlStore(output_dir)
        self.concurrency = concurrency
        self.request_timeout = request_timeout
        self.per_host_delay = per_host_delay
        self.max_pages_per_source = max_pages_per_source
        self.max_files_per_source = max_files_per_source
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.dry_run = dry_run
        self._robots: dict[str, RobotFileParser] = {}
        self._host_locks: dict[str, asyncio.Lock] = {}
        self._last_request_at: dict[str, float] = {}

    async def run(self) -> dict[str, CrawlStats]:
        if aiohttp is None and not self.dry_run:
            raise RuntimeError("aiohttp is required for network crawling; install dependencies with `pip install -r requirements.txt`.")
        results: dict[str, CrawlStats] = {}
        sem = asyncio.Semaphore(self.concurrency)
        if self.dry_run:
            tasks = [self._crawl_source(None, sem, source) for source in self.sources]
            for source, stats in await asyncio.gather(*tasks):
                results[source.name] = stats
            self.store.close()
            return results

        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/json,application/pdf,*/*;q=0.8"}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            tasks = [self._crawl_source(session, sem, source) for source in self.sources]
            for source, stats in await asyncio.gather(*tasks):
                results[source.name] = stats
        self.store.close()
        return results

    async def _crawl_source(
        self, session: aiohttp.ClientSession, sem: asyncio.Semaphore, source: Source
    ) -> tuple[Source, CrawlStats]:
        stats = CrawlStats()
        queue: deque[tuple[str, int, str | None]] = deque((seed, 0, None) for seed in source.seeds)
        queued = {seed for seed in source.seeds}
        while queue and stats.pages_seen < self.max_pages_per_source and stats.files_downloaded < self.max_files_per_source:
            url, depth, parent = queue.popleft()
            normalized = self._normalize_url(url)
            if not normalized or normalized not in queued:
                continue
            if self.store.has_seen(normalized):
                stats.files_skipped += 1
                continue
            if not source.owns(normalized):
                continue
            if self.respect_robots and not self.dry_run and not await self._can_fetch(session, normalized):
                self.store.mark_seen(normalized, "robots_denied")
                stats.files_skipped += 1
                continue
            try:
                async with sem:
                    response_info = await self._fetch(session, normalized)
                status, content_type, body = response_info
            except Exception:
                self.store.mark_seen(normalized, "error")
                stats.errors += 1
                continue
            if status >= 400:
                self.store.mark_seen(normalized, f"http_{status}")
                stats.errors += 1
                continue
            stats.pages_seen += 1
            is_doc = self._is_document_url(normalized) or self._is_document_type(content_type)
            if is_doc or self._is_json_api(normalized, content_type):
                item = await self._save_document(source, normalized, status, content_type, body, parent)
                if item:
                    stats.files_downloaded += 1
                else:
                    stats.files_skipped += 1
                self.store.mark_seen(normalized, "downloaded" if item else "duplicate")
                continue
            self.store.mark_seen(normalized, "crawled")
            if depth >= source.max_depth or not self._is_html(content_type):
                continue
            for link in self._extract_links(normalized, body):
                clean = self._normalize_url(link)
                if clean and clean not in queued and source.owns(clean) and self._matches_keywords(clean, source):
                    queued.add(clean)
                    queue.append((clean, depth + 1, normalized))
        return source, stats

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> tuple[int, str, bytes]:
        host = urlparse(url).netloc
        lock = self._host_locks.setdefault(host, asyncio.Lock())
        async with lock:
            now = asyncio.get_running_loop().time()
            elapsed = now - self._last_request_at.get(host, 0.0)
            if elapsed < self.per_host_delay:
                await asyncio.sleep(self.per_host_delay - elapsed)
            if self.dry_run:
                self._last_request_at[host] = asyncio.get_running_loop().time()
                return 204, "text/plain", b""
            async with session.get(url, allow_redirects=True) as response:
                body = await response.read()
                self._last_request_at[host] = asyncio.get_running_loop().time()
                return response.status, response.headers.get("Content-Type", "").split(";")[0].lower(), body

    async def _save_document(
        self,
        source: Source,
        url: str,
        status: int,
        content_type: str,
        body: bytes,
        parent: str | None,
    ) -> CrawlItem | None:
        sha256 = hashlib.sha256(body).hexdigest()
        if self.store.has_hash(sha256):
            return None
        extension = self._extension_for(url, content_type)
        path = self.store.target_path(source, url, extension)
        if not self.dry_run:
            path.write_bytes(body)
            self.store.record_hash(sha256, path)
        item = CrawlItem(
            url=url,
            source_name=source.name,
            category=source.category.value,
            status=status,
            content_type=content_type,
            bytes_downloaded=len(body),
            sha256=sha256,
            local_path=str(path),
            discovered_from=parent,
        )
        self.store.append_item(item)
        return item

    async def _can_fetch(self, session: aiohttp.ClientSession, url: str) -> bool:
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        if root not in self._robots:
            robot = RobotFileParser()
            robot.set_url(urljoin(root, "/robots.txt"))
            try:
                async with session.get(robot.url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    text = await response.text(errors="ignore") if response.status < 400 else ""
                robot.parse(text.splitlines())
            except Exception:
                robot.parse([])
            self._robots[root] = robot
        return self._robots[root].can_fetch(self.user_agent, url)

    @staticmethod
    def _normalize_url(url: str) -> str | None:
        if not url or url.startswith(("mailto:", "javascript:", "tel:")):
            return None
        clean, _fragment = urldefrag(url.strip())
        parsed = urlparse(clean)
        if parsed.scheme not in {"http", "https"}:
            return None
        return clean

    @staticmethod
    def _extract_links(base_url: str, body: bytes) -> list[str]:
        links: list[str] = []
        if BeautifulSoup is not None:
            soup = BeautifulSoup(body, "lxml")
            for element in soup.find_all(["a", "link", "script", "iframe"]):
                href = element.get("href") or element.get("src")
                if href:
                    links.append(urljoin(base_url, href))
            return links

        class LinkParser(HTMLParser):
            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag not in {"a", "link", "script", "iframe"}:
                    return
                attr_map = dict(attrs)
                href = attr_map.get("href") or attr_map.get("src")
                if href:
                    links.append(urljoin(base_url, href))

        parser = LinkParser()
        parser.feed(body.decode("utf-8", errors="ignore"))
        return links

    @staticmethod
    def _is_html(content_type: str) -> bool:
        return any(content_type.startswith(html_type) for html_type in HTML_TYPES)

    @staticmethod
    def _is_document_type(content_type: str) -> bool:
        return content_type in DOCUMENT_CONTENT_TYPES or content_type.startswith("application/vnd")

    @staticmethod
    def _is_document_url(url: str) -> bool:
        suffix = Path(urlparse(url).path).suffix.lower()
        return suffix in DOCUMENT_EXTENSIONS

    @staticmethod
    def _is_json_api(url: str, content_type: str) -> bool:
        return content_type == "application/json" or "api." in (urlparse(url).hostname or "")

    @staticmethod
    def _extension_for(url: str, content_type: str) -> str | None:
        suffix = Path(urlparse(url).path).suffix.lower()
        if suffix:
            return suffix
        guessed = mimetypes.guess_extension(content_type)
        return ".json" if content_type == "application/json" else guessed

    @staticmethod
    def _matches_keywords(url: str, source: Source) -> bool:
        if not source.keywords:
            return True
        haystack = re.sub(r"[_\-/]+", " ", url).lower()
        return any(keyword.lower() in haystack for keyword in source.keywords) or LogisticsCrawler._is_document_url(url)


def summarize_stats(stats: dict[str, CrawlStats]) -> str:
    serializable: dict[str, dict[str, Any]] = {
        name: {
            "pages_seen": value.pages_seen,
            "files_downloaded": value.files_downloaded,
            "files_skipped": value.files_skipped,
            "errors": value.errors,
        }
        for name, value in stats.items()
    }
    return json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True)
