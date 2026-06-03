"""Shared pytest fixtures: generate sample PDFs in-memory."""
import pytest
import pypdfium2 as pdfium
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _build_image_only_pdf(src_text_pdf: str, out_path: str, dpi: float = 2.0) -> None:
    """Render a text PDF's pages to PIL images, then write as image-only PDF.

    Uses pypdfium2 (no system poppler binary required) instead of pdf2image.
    The result has no text layer, so pdfplumber.extract_text() returns ''.
    """
    pdf = pdfium.PdfDocument(src_text_pdf)
    images = [pdf[i].render(scale=dpi).to_pil() for i in range(len(pdf))]
    images[0].save(out_path, save_all=True, append_images=images[1:])


def _make_text_pdf(path: str, page_count: int, prefix: str) -> None:
    c = canvas.Canvas(path, pagesize=letter)
    for i in range(1, page_count + 1):
        c.drawString(100, 700, f"Page {i} {prefix} — at least fifty characters to pass the threshold check easily.")
        c.showPage()
    c.save()


@pytest.fixture
def text_only_pdf(tmp_path):
    """3 pages, each with extractable text (pdfplumber will succeed)."""
    pdf_path = tmp_path / "text_only.pdf"
    _make_text_pdf(str(pdf_path), 3, "body text")
    return str(pdf_path)


@pytest.fixture
def scanned_pdf(tmp_path):
    """3 pages, each is a rendered image (no text layer → pdfplumber returns empty)."""
    src = tmp_path / "_src.pdf"
    _make_text_pdf(str(src), 3, "rendered as image")
    out = tmp_path / "scanned.pdf"
    _build_image_only_pdf(str(src), str(out))
    return str(out)


@pytest.fixture
def mixed_pdf(tmp_path):
    """3 pages, all rendered as images (forces OCR path in tests).

    The 'mixed' (text + image) behavior is mocked at the test layer rather than
    built into the fixture, so the fixture itself stays pure image-only.
    """
    src = tmp_path / "_src.pdf"
    _make_text_pdf(str(src), 3, "content for mixing test")
    out = tmp_path / "mixed.pdf"
    _build_image_only_pdf(str(src), str(out))
    return str(out)


@pytest.fixture
def output_dir(tmp_path):
    """Output directory for scripts to write into."""
    d = tmp_path / "out"
    d.mkdir()
    return str(d)
