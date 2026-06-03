"""Integration tests for extract_with_fallback pipeline."""
import os

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


def test_text_extractor_exports_images_for_no_text_pages(scanned_pdf, output_dir):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    no_text = [p for p in pages if not p.is_text_page()]
    assert no_text, "fixture should produce no-text pages"
    # Now export
    extractor.export_images(no_text, output_dir, scale=2.0)
    for p in no_text:
        assert p.image_path is not None
        assert os.path.exists(p.image_path)
        assert p.image_path.endswith(f"page_{p.page_num:03d}.png")
