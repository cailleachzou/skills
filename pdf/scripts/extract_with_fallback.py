"""PDF extraction pipeline with per-page fallback: pdfplumber → UMI-OCR → MCP marker.

CLI: python extract_with_fallback.py <input.pdf> <output_dir> [--ocr-lang LANG]
                                              [--text-threshold N] [--scale FLOAT]
"""
import os
import sys
from dataclasses import dataclass

import pdfplumber

# Allow `python pdf/scripts/extract_with_fallback.py ...` direct invocation
# by adding the parent (pdf/) dir to sys.path so `from scripts.ocr_client import ...` works.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ocr_client import OCRClient, OCRUnavailable


@dataclass
class PageResult:
    page_num: int  # 1-based
    text: str
    char_count: int
    image_path: str | None  # path to exported PNG, or None if not exported
    text_threshold: int = 0  # threshold captured at extraction time
    source: str = "pdfplumber"  # one of: pdfplumber, umi-ocr, needs-vision
    ocr_text: str = ""

    def is_text_page(self):
        return self.source == "pdfplumber" and self.char_count >= self.text_threshold


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
                        text_threshold=self.text_threshold,
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
            body = f"[image: {page.image_path} — please run mimo-multimodal image for semantic understanding]"
        else:
            body = page.text
        return f"{header}\n{body}\n"

    def write(self, output_path):
        content = "\n".join(self._render_block(p) for p in self.pages)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path


def extract_tables(pdf_path, output_path):
    """Extract tables to extracted_tables.txt. Returns True if any tables found."""
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            for j, table in enumerate(page.extract_tables() or []):
                non_empty = [row for row in table if any(cell for cell in row if cell)]
                if not non_empty:
                    continue
                rows = [" | ".join(str(c).strip() if c else "" for c in row) for row in non_empty]
                all_tables.append(f"=== Page {i} - Table {j+1} ===\n" + "\n".join(rows))
    if not all_tables:
        return False
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_tables))
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract text from PDF with per-page fallback: pdfplumber → UMI-OCR → vision marker."
    )
    parser.add_argument("pdf_path")
    parser.add_argument("output_dir")
    parser.add_argument("--ocr-lang", default="简体中文", help="UMI-OCR language (default: 简体中文)")
    parser.add_argument("--text-threshold", type=int, default=50, help="Min chars/page to skip OCR (default: 50)")
    parser.add_argument("--scale", type=float, default=2.0, help="PNG export scale (default: 2.0)")
    parser.add_argument("--skip-ocr", action="store_true", help="Skip UMI-OCR phase (debug)")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Fail fast on encrypted/corrupt PDFs so we never leave a half-written output
    # directory. Per spec: "PDF 加密/损坏 | 启动时检测，stderr 报错退出，不留半成品".
    try:
        with pdfplumber.open(args.pdf_path) as _pdf:
            _ = len(_pdf.pages)
    except Exception as e:
        print(f"Error: cannot read PDF ({type(e).__name__}: {e}). "
              f"If encrypted, decrypt it first; if corrupt, re-export the source.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Phase 1: text extract
    print(f"[1/4] Extracting text from {args.pdf_path} ...", file=sys.stderr)
    extractor = TextExtractor(args.pdf_path, text_threshold=args.text_threshold)
    pages = extractor.extract()
    no_text = [p for p in pages if not p.is_text_page()]
    print(f"      {len(pages)} page(s), {len(no_text)} need fallback", file=sys.stderr)

    # Export PNGs for fallback pages
    if no_text:
        print(f"[2/4] Exporting {len(no_text)} no-text page(s) to PNG ...", file=sys.stderr)
        extractor.export_images(no_text, args.output_dir, scale=args.scale)

    # Phase 2: OCR fallback (or skip → mark needs-vision)
    if args.skip_ocr and no_text:
        print(f"[3/4] --skip-ocr set: marking {len(no_text)} no-text page(s) as needs-vision ...", file=sys.stderr)
        for p in no_text:
            p.source = "needs-vision"
    elif no_text:
        print(f"[3/4] Running UMI-OCR fallback ...", file=sys.stderr)
        run_ocr_fallback(pages, ocr_lang=args.ocr_lang)

    # Tables
    tables_path = os.path.join(args.output_dir, "extracted_tables.txt")
    if extract_tables(args.pdf_path, tables_path):
        print(f"[4/4] Tables written to {tables_path}", file=sys.stderr)
    else:
        print("[4/4] No tables found", file=sys.stderr)

    # Output merger
    text_path = os.path.join(args.output_dir, "extracted_text.txt")
    OutputMerger(pages).write(text_path)
    print(f"\nDone. Wrote: {text_path}", file=sys.stderr)

    needs_vision = [p for p in pages if p.source == "needs-vision"]
    if needs_vision:
        print(f"\n{len(needs_vision)} page(s) marked 'needs-vision'.", file=sys.stderr)
        print("Claude: read extracted_text.txt, find '=== Page N (source: needs-vision) ===' markers,", file=sys.stderr)
        print("        call mimo-multimodal image for each, write results back to the file.", file=sys.stderr)


if __name__ == "__main__":
    main()
