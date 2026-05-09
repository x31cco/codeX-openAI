from logistics_open_data_spider.crawler import LogisticsCrawler
from logistics_open_data_spider.models import Category, Source


def test_document_url_detection():
    assert LogisticsCrawler._is_document_url("https://example.org/a/report.pdf")
    assert LogisticsCrawler._is_document_url("https://example.org/a/slides.pptx?x=1")
    assert not LogisticsCrawler._is_document_url("https://example.org/a/page.html")


def test_keyword_matching_keeps_raw_documents():
    source = Source(
        name="demo",
        category=Category.POLICIES,
        seeds=("https://example.org",),
        allowed_domains=("example.org",),
        keywords=("logistics",),
    )
    assert LogisticsCrawler._matches_keywords("https://example.org/files/random.pdf", source)
    assert LogisticsCrawler._matches_keywords("https://example.org/logistics/news.html", source)
    assert not LogisticsCrawler._matches_keywords("https://example.org/finance/news.html", source)


def test_link_extraction_resolves_relative_urls():
    body = b'<html><a href="/doc.pdf">PDF</a><script src="/app.js"></script></html>'
    assert LogisticsCrawler._extract_links("https://example.org/base/index.html", body) == [
        "https://example.org/doc.pdf",
        "https://example.org/app.js",
    ]
