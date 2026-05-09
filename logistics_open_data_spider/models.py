"""Domain models used by the logistics open-data spiders."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse


class Category(str, Enum):
    """Tender-defined dataset categories."""

    BIBLIOGRAPHY = "reference_bibliography"
    ACADEMIC_PAPERS = "academic_papers"
    PROFESSIONAL_KNOWLEDGE = "professional_knowledge_base"
    TERMINOLOGY = "standardized_terminology"
    EXERCISES = "commodity_supply_chain_exercises"
    LAWS = "laws_and_regulations"
    STANDARDS = "standards_specifications"
    PATENTS = "patents"
    POLICIES = "policies"
    PUBLIC_OPINION = "internet_public_opinion"


DOCUMENT_EXTENSIONS = {
    ".json",
    ".jsonl",
    ".xml",
    ".csv",
    ".xls",
    ".xlsx",
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
    ".7z",
}

DOCUMENT_CONTENT_TYPES = {
    "application/json",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/xml",
    "text/xml",
    "application/zip",
}


@dataclass(frozen=True)
class Source:
    """A crawl seed and policy for one authoritative source."""

    name: str
    category: Category
    seeds: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    keywords: tuple[str, ...] = ()
    max_depth: int = 2
    notes: str = ""

    def owns(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in self.allowed_domains)


@dataclass
class CrawlItem:
    """Metadata recorded for each downloaded raw object."""

    url: str
    source_name: str
    category: str
    status: int
    content_type: str
    bytes_downloaded: int
    sha256: str
    local_path: str
    title: str | None = None
    discovered_from: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


def normalize_categories(values: Iterable[str] | None) -> set[Category] | None:
    if not values:
        return None
    normalized: set[Category] = set()
    by_value = {category.value: category for category in Category}
    by_name = {category.name.lower(): category for category in Category}
    for value in values:
        key = value.strip().lower()
        if key in by_value:
            normalized.add(by_value[key])
        elif key in by_name:
            normalized.add(by_name[key])
        else:
            valid = ", ".join(category.value for category in Category)
            raise ValueError(f"Unknown category '{value}'. Valid values: {valid}")
    return normalized
