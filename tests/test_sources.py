from logistics_open_data_spider.models import Category, normalize_categories
from logistics_open_data_spider.sources import SOURCES, iter_sources


def test_all_tender_categories_have_sources():
    categories = {source.category for source in SOURCES}
    assert categories == set(Category)


def test_each_source_has_seed_and_domain():
    for source in SOURCES:
        assert source.seeds
        assert source.allowed_domains
        assert source.max_depth >= 1


def test_category_filtering():
    selected = iter_sources({Category.PATENTS})
    assert selected
    assert {source.category for source in selected} == {Category.PATENTS}


def test_normalize_categories_accepts_values_and_names():
    assert normalize_categories(["patents", "LAWS"]) == {Category.PATENTS, Category.LAWS}
