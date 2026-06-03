"""Integration tests for extract_with_fallback pipeline."""
from scripts.extract_with_fallback import TextExtractor


def test_text_extractor_returns_per_page_results(text_only_pdf):
    extractor = TextExtractor(text_only_pdf, text_threshold=50)
    pages = extractor.extract()
    assert len(pages) == 3
    for i, page in enumerate(pages, start=1):
        assert page.page_num == i
        assert page.char_count > 50
        assert page.text  # non-empty
        assert page.is_text_page() is True


def test_text_extractor_marks_scanned_pages(scanned_pdf):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    assert len(pages) == 3
    for page in pages:
        assert page.char_count < 50
        assert page.is_text_page() is False
