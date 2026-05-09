"""Command-line interface for the logistics open-data spider."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .crawler import LogisticsCrawler, summarize_stats
from .models import Category, normalize_categories
from .sources import iter_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logistics-spider",
        description="Crawl original open logistics dataset files across the ten tender-defined classes.",
    )
    parser.add_argument(
        "--category",
        action="append",
        choices=[category.value for category in Category],
        help="Restrict crawl to a category. May be repeated. Defaults to all ten categories.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Directory for raw files, metadata and state.")
    parser.add_argument("--max-pages", type=int, default=200, help="Maximum pages fetched per source.")
    parser.add_argument("--max-files", type=int, default=100, help="Maximum raw files downloaded per source.")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent HTTP requests across sources.")
    parser.add_argument("--delay", type=float, default=0.8, help="Minimum seconds between requests to the same host.")
    parser.add_argument("--timeout", type=int, default=40, help="Total request timeout in seconds.")
    parser.add_argument("--user-agent", default=None, help="Override the default crawler User-Agent.")
    parser.add_argument("--ignore-robots", action="store_true", help="Do not consult robots.txt before fetching URLs.")
    parser.add_argument("--dry-run", action="store_true", help="Build crawl queues without downloading remote content.")
    return parser


async def async_main(args: argparse.Namespace) -> int:
    categories = normalize_categories(args.category)
    sources = iter_sources(categories)
    crawler = LogisticsCrawler(
        sources,
        args.output_dir,
        concurrency=args.concurrency,
        request_timeout=args.timeout,
        per_host_delay=args.delay,
        max_pages_per_source=args.max_pages,
        max_files_per_source=args.max_files,
        user_agent=args.user_agent or "LogisticsOpenDataSpider/0.1 (+open-data research crawler)",
        respect_robots=not args.ignore_robots,
        dry_run=args.dry_run,
    )
    stats = await crawler.run()
    print(summarize_stats(stats))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
