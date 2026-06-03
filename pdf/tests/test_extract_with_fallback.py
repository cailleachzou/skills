"""Integration tests for extract_with_fallback pipeline."""
import os
from unittest.mock import patch

from scripts.extract_with_fallback import PageResult, TextExtractor, run_ocr_fallback
from scripts.extract_with_fallback import OutputMerger
from scripts.ocr_client import OCRUnavailable


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


def test_run_ocr_fallback_calls_ocr_for_no_text_pages(scanned_pdf, output_dir):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    extractor.export_images([p for p in pages if not p.is_text_page()], output_dir)
    with patch("scripts.extract_with_fallback.OCRClient") as MockClient:
        instance = MockClient.return_value
        instance.ensure_running.return_value = True
        instance.recognize_image.return_value = "OCR'd text for page"
        run_ocr_fallback(pages, ocr_lang="简体中文")
    for p in pages:
        if not p.is_text_page():
            assert p.source == "umi-ocr"
            assert p.ocr_text == "OCR'd text for page"


def test_run_ocr_fallback_marks_pages_when_ocr_unavailable(scanned_pdf, output_dir):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    extractor.export_images([p for p in pages if not p.is_text_page()], output_dir)
    with patch("scripts.extract_with_fallback.OCRClient") as MockClient:
        instance = MockClient.return_value
        instance.ensure_running.side_effect = OCRUnavailable("OCR not available")
        run_ocr_fallback(pages)
    for p in pages:
        if not p.is_text_page():
            assert p.source == "needs-vision"


def test_run_ocr_fallback_marks_pages_on_empty_result(scanned_pdf, output_dir):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    extractor.export_images([p for p in pages if not p.is_text_page()], output_dir)
    with patch("scripts.extract_with_fallback.OCRClient") as MockClient:
        instance = MockClient.return_value
        instance.ensure_running.return_value = True
        instance.recognize_image.return_value = ""  # empty
        run_ocr_fallback(pages)
    for p in pages:
        if not p.is_text_page():
            assert p.source == "needs-vision"


def test_run_ocr_fallback_marks_pages_with_missing_image_path(scanned_pdf):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    # Intentionally skip export_images so image_path stays None
    with patch("scripts.extract_with_fallback.OCRClient") as MockClient:
        instance = MockClient.return_value
        instance.ensure_running.return_value = True
        instance.recognize_image.return_value = "should not be called"
        run_ocr_fallback(pages)
    for p in pages:
        if not p.is_text_page():
            assert p.source == "needs-vision"
            # recognize_image should NOT have been called because image_path was None
            instance.recognize_image.assert_not_called()


def _make_pages():
    """Build a small set of pages with mixed sources for merger tests."""
    return [
        PageResult(page_num=1, text="Hello world from page one", char_count=27, image_path=None, source="pdfplumber"),
        PageResult(page_num=2, text="", char_count=0, image_path="/tmp/page_002.png", source="umi-ocr", ocr_text="OCR result page 2"),
        PageResult(page_num=3, text="", char_count=0, image_path="/tmp/page_003.png", source="needs-vision"),
    ]


def test_output_merger_writes_per_page_blocks(tmp_path):
    pages = _make_pages()
    out = tmp_path / "extracted_text.txt"
    OutputMerger(pages).write(str(out))
    content = out.read_text(encoding="utf-8")
    assert "=== Page 1 (source: pdfplumber) ===" in content
    assert "Hello world from page one" in content
    assert "=== Page 2 (source: umi-ocr) ===" in content
    assert "OCR result page 2" in content
    assert "=== Page 3 (source: needs-vision) ===" in content
    assert "/tmp/page_003.png" in content
    # Page order preserved
    p1 = content.index("Page 1")
    p2 = content.index("Page 2")
    p3 = content.index("Page 3")
    assert p1 < p2 < p3
