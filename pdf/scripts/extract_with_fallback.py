"""PDF extraction pipeline with per-page fallback: pdfplumber → UMI-OCR → MCP marker.

CLI: python extract_with_fallback.py <input.pdf> <output_dir> [--ocr-lang LANG]
                                              [--text-threshold N] [--scale FLOAT]
"""
import os
import sys
from dataclasses import dataclass

import pdfplumber

from scripts.ocr_client import OCRClient, OCRUnavailable


@dataclass
class PageResult:
    page_num: int  # 1-based
    text: str
    char_count: int
    image_path: str | None  # path to exported PNG, or None if not exported
    source: str = "pdfplumber"  # one of: pdfplumber, umi-ocr, needs-vision
    ocr_text: str = ""

    def is_text_page(self):
        return self.source == "pdfplumber" and self.char_count > 0


class TextExtractor:
    """Phase 1: per-page text extraction via pdfplumber."""

    def __init__(self, pdf_path, text_threshold=50):
        self.pdf_path = pdf_path
        self.text_threshold = text_threshold

    def extract(self):
        results = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                results.append(
                    PageResult(
                        page_num=i,
                        text=text,
                        char_count=len(text.strip()),
                        image_path=None,
                    )
                )
        return results

    def export_images(self, pages, output_dir, scale=2.0):
        """Render each page to PNG using pypdfium2; set page.image_path."""
        import pypdfium2 as pdfium
        os.makedirs(output_dir, exist_ok=True)
        pdf = pdfium.PdfDocument(self.pdf_path)
        for page_result in pages:
            idx = page_result.page_num - 1
            if idx < 0 or idx >= len(pdf):
                continue
            bitmap = pdf[idx].render(scale=scale)
            img = bitmap.to_pil()
            out = os.path.join(output_dir, f"page_{page_result.page_num:03d}.png")
            img.save(out, "PNG")
            page_result.image_path = out


def run_ocr_fallback(pages, ocr_lang="简体中文"):
    """Phase 2: for pages that pdfplumber couldn't read, try UMI-OCR.

    Mutates each PageResult in-place:
      - Sets source='umi-ocr' and ocr_text on success
      - Sets source='needs-vision' if OCR unavailable or returns empty
    Never raises; logs to stderr on failure.
    """
    no_text = [p for p in pages if not p.is_text_page()]
    if not no_text:
        return
    try:
        client = OCRClient()
        client.ensure_running()
    except (OCRUnavailable, OSError) as e:
        print(f"[warn] Umi-OCR unavailable, marking {len(no_text)} page(s) for vision: {e}", file=sys.stderr)
        for p in no_text:
            p.source = "needs-vision"
        return
    for p in no_text:
        if not p.image_path or not os.path.exists(p.image_path):
            p.source = "needs-vision"
            continue
        try:
            text = client.recognize_image(p.image_path, language=ocr_lang)
            if text:
                p.source = "umi-ocr"
                p.ocr_text = text
            else:
                p.source = "needs-vision"
        except Exception as e:
            print(f"[warn] OCR failed on page {p.page_num}: {e}", file=sys.stderr)
            p.source = "needs-vision"


class OutputMerger:
    """Assemble extracted_text.txt with per-page source tags."""

    def __init__(self, pages):
        self.pages = pages

    def _render_block(self, page):
        header = f"=== Page {page.page_num} (source: {page.source}) ==="
        if page.source == "pdfplumber":
            body = page.text
        elif page.source == "umi-ocr":
            body = page.ocr_text
        elif page.source == "needs-vision":
            body = f"[image: {page.image_path} — please run mcp__MiniMax__understand_image for semantic understanding]"
        else:
            body = page.text
        return f"{header}\n{body}\n"

    def write(self, output_path):
        content = "\n".join(self._render_block(p) for p in self.pages)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
