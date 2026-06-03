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
