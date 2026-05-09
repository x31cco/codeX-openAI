# Logistics Open Data Spider

A configurable Python spider for collecting original public logistics and supply-chain datasets described by the tender. It targets ten classes of resources and downloads raw public files such as JSON, PDF, Word, PowerPoint, Excel, XML, CSV and archives while recording normalized JSONL metadata.

## Dataset coverage

The built-in source registry maps each tender category to authoritative public entry points:

1. Reference bibliography datasets.
2. Academic paper datasets.
3. Professional knowledge-base datasets.
4. Standardized terminology datasets.
5. Commodity and supply-chain exercise datasets.
6. Laws and regulations datasets.
7. Standards and specifications datasets.
8. Patent datasets.
9. Policy datasets.
10. Internet public-opinion and market-intelligence datasets.

The registry is intentionally declarative (`logistics_open_data_spider/sources.py`) so new journal sites, government portals, certification bodies or APIs can be added without touching crawler logic.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Crawl every category with conservative defaults:

```bash
logistics-spider --output-dir data/logistics_open_data
```

Crawl only policies and standards:

```bash
logistics-spider \
  --category policies \
  --category standards_specifications \
  --output-dir data/policy_standard \
  --max-pages 500 \
  --max-files 200 \
  --concurrency 6
```

Use a dry run for pipeline validation:

```bash
python -m logistics_open_data_spider.cli --dry-run --max-pages 2 --max-files 1
```

## Output layout

```text
data/
  raw/<category>/<source-name>/...      # original downloaded files
  metadata/<category>.jsonl             # URL, content type, SHA-256, local path and source metadata
  crawl_state.sqlite3                   # resumable URL/hash state
```

## Crawler behavior

- Respects `robots.txt` by default and allows a custom User-Agent.
- Applies per-host throttling and global concurrency limits.
- Deduplicates raw files by SHA-256 and remembers seen URLs in SQLite.
- Preserves original public files and keeps discovery metadata separately.
- Filters in-domain links by source keywords while always retaining direct raw-file URLs.

Some public patent, standards and news portals are JavaScript-heavy or gated by usage terms. For those sites, keep the registry entries as discovery seeds and add officially supported export/API endpoints when credentials or institutional access are available.
