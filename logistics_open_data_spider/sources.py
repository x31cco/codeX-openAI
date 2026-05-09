"""Authoritative seed registry for the ten tender-defined logistics data classes.

The registry intentionally uses public official, academic, standards, patent and
industry-information entry points. The crawler follows in-domain links from these
seeds and downloads original JSON/PDF/Word/PPT/Excel/archive files it discovers.
"""
from __future__ import annotations

from .models import Category, Source

SOURCES: tuple[Source, ...] = (
    Source(
        name="OpenAlex logistics bibliography and works",
        category=Category.BIBLIOGRAPHY,
        seeds=(
            "https://api.openalex.org/works?search=logistics%20supply%20chain%20textbook&per-page=50",
            "https://api.openalex.org/works?search=APICS%20CPIM%20CSCP%20SCOR%20reference&per-page=50",
        ),
        allowed_domains=("api.openalex.org", "openalex.org"),
        keywords=("logistics", "supply chain", "APICS", "SCOR", "textbook"),
        max_depth=1,
        notes="Open bibliographic metadata for classic books, textbooks and reference works.",
    ),
    Source(
        name="Crossref recent logistics papers",
        category=Category.ACADEMIC_PAPERS,
        seeds=(
            "https://api.crossref.org/works?query=logistics%20supply%20chain%20management&filter=from-pub-date:2021-01-01,type:journal-article&rows=100",
            "https://api.crossref.org/works?query=international%20trade%20transportation%20operations%20research&filter=from-pub-date:2021-01-01,type:journal-article&rows=100",
        ),
        allowed_domains=("api.crossref.org", "crossref.org"),
        keywords=("logistics", "supply chain", "international trade", "operations research"),
        max_depth=1,
        notes="International journal article metadata; DOI landing pages are preserved as metadata.",
    ),
    Source(
        name="China Transport and customs professional knowledge",
        category=Category.PROFESSIONAL_KNOWLEDGE,
        seeds=(
            "https://www.mot.gov.cn/tongjishuju/",
            "http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/index.html",
            "https://www.mofcom.gov.cn/zwgk/tjzl/",
        ),
        allowed_domains=("mot.gov.cn", "customs.gov.cn", "mofcom.gov.cn"),
        keywords=("统计", "公报", "报告", "物流", "海关", "运输", "粮食", "能源"),
        max_depth=2,
        notes="Government statistics, announcements and industry reports.",
    ),
    Source(
        name="Trade logistics terminology",
        category=Category.TERMINOLOGY,
        seeds=(
            "https://unece.org/trade/uncefact/introducing-unedifact",
            "https://iccwbo.org/business-solutions/incoterms-rules/",
            "https://www.ascm.org/corporate-transformation/standards-tools/scor-ds/",
        ),
        allowed_domains=("unece.org", "iccwbo.org", "ascm.org"),
        keywords=("term", "glossary", "Incoterms", "UN/EDIFACT", "SCOR", "definition"),
        max_depth=2,
        notes="Multilingual terms, abbreviations, Incoterms and SCOR definitions.",
    ),
    Source(
        name="Supply-chain and futures examination exercises",
        category=Category.EXERCISES,
        seeds=(
            "https://www.cfachina.org/",
            "https://www.ascm.org/learning-development/certifications-credentials/",
            "https://www.cips.org/qualifications/",
        ),
        allowed_domains=("cfachina.org", "ascm.org", "cips.org"),
        keywords=("考试", "试题", "模拟", "CPIM", "CSCP", "CLTD", "CIPS", "sample", "exam"),
        max_depth=2,
        notes="Public qualification pages and sample/mock exercise files when published.",
    ),
    Source(
        name="Domestic and international trade law",
        category=Category.LAWS,
        seeds=(
            "https://flk.npc.gov.cn/",
            "https://uncitral.un.org/en/texts",
            "https://www.hcch.net/en/instruments/conventions",
            "https://www.un.org/depts/los/convention_agreements/convention_overview_convention.htm",
        ),
        allowed_domains=("flk.npc.gov.cn", "uncitral.un.org", "hcch.net", "un.org"),
        keywords=("law", "convention", "arbitration", "trade", "海商", "合同", "进出口"),
        max_depth=2,
        notes="Chinese laws and international commercial-law conventions.",
    ),
    Source(
        name="Standards specifications",
        category=Category.STANDARDS,
        seeds=(
            "https://openstd.samr.gov.cn/",
            "https://std.samr.gov.cn/",
            "https://www.iso.org/ics/55.020/x/",
            "https://www.gs1.org/standards",
        ),
        allowed_domains=("openstd.samr.gov.cn", "std.samr.gov.cn", "iso.org", "gs1.org"),
        keywords=("物流", "包装", "运输", "标准", "standard", "specification", "data exchange"),
        max_depth=2,
        notes="National, industry, local and international standard/specification resources.",
    ),
    Source(
        name="Global patent literature",
        category=Category.PATENTS,
        seeds=(
            "https://patentscope.wipo.int/search/en/search.jsf",
            "https://ppubs.uspto.gov/pubwebapp/",
            "https://worldwide.espacenet.com/patent/",
        ),
        allowed_domains=("patentscope.wipo.int", "ppubs.uspto.gov", "worldwide.espacenet.com"),
        keywords=("smart logistics", "supply chain", "cold chain", "port automation", "warehouse"),
        max_depth=1,
        notes="Patent search entry points; dynamic portals may require API/export configuration.",
    ),
    Source(
        name="Policy documents",
        category=Category.POLICIES,
        seeds=(
            "https://www.gov.cn/zhengce/",
            "https://www.mot.gov.cn/zhengcejiedu/",
            "https://www.wto.org/english/tratop_e/tpr_e/tpr_e.htm",
            "https://www.imo.org/en/MediaCentre/HotTopics/Pages/Default.aspx",
            "https://www.wcoomd.org/en/topics/facilitation/instrument-and-tools/tools/safe_package.aspx",
        ),
        allowed_domains=("gov.cn", "mot.gov.cn", "wto.org", "imo.org", "wcoomd.org"),
        keywords=("政策", "规划", "通知", "trade policy", "framework", "amendment", "customs"),
        max_depth=2,
        notes="Non-legislative policy, planning, interpretation and treaty-system documents.",
    ),
    Source(
        name="Public logistics opinion and market intelligence",
        category=Category.PUBLIC_OPINION,
        seeds=(
            "https://unctad.org/topic/transport-and-trade-logistics",
            "https://www.balticexchange.com/en/data-services/market-information.html",
            "https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/shipping",
            "https://www.reuters.com/business/autos-transportation/",
        ),
        allowed_domains=("unctad.org", "balticexchange.com", "spglobal.com", "reuters.com"),
        keywords=("shipping", "freight", "supply chain", "commodity", "sanctions", "tariff", "port"),
        max_depth=2,
        notes="Market news, shipping indices, commodity logistics and supply-chain events.",
    ),
)


def iter_sources(categories: set[Category] | None = None) -> tuple[Source, ...]:
    if categories is None:
        return SOURCES
    return tuple(source for source in SOURCES if source.category in categories)
