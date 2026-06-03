"""PDF extraction pipeline with per-page fallback: pdfplumber → UMI-OCR → MCP marker.

CLI: python extract_with_fallback.py <input.pdf> <output_dir> [--ocr-lang LANG]
                                              [--text-threshold N] [--scale FLOAT]
"""
import os
import sys
from dataclasses import dataclass

import pdfplumber


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
