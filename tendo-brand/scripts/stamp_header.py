#!/usr/bin/env python3
"""
Stamp a header image onto each page of a PDF.
Places header as background layer (behind content).

Usage:
    python stamp_header.py input.pdf header.png
"""

import sys
import os
import tempfile
from PIL import Image
import fitz  # PyMuPDF


def stamp_header(pdf_path, header_path):
    with Image.open(header_path) as img:
        img_w, img_h = img.size

    doc = fitz.open(pdf_path)

    for page in doc:
        page_width = page.rect.width
        header_height = page_width * (img_h / img_w)
        header_rect = fitz.Rect(0, 0, page_width, header_height)

        # Insert as background (below content) using overlay=False
        page.insert_image(header_rect, filename=header_path, overlay=False)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(tmp_fd)
    doc.save(tmp_path)
    doc.close()
    os.replace(tmp_path, pdf_path)
    print('Stamped header on pages')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python stamp_header.py input.pdf header.png')
        sys.exit(1)
    stamp_header(sys.argv[1], sys.argv[2])
