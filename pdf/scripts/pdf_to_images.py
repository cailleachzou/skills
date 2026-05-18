"""
Export PDF pages as high-resolution images for AI image understanding.
Usage: python pdf_to_images.py <input.pdf> <output_dir> [scale]
  scale: optional, default 2.0 (2x resolution)
"""
import sys
import os
import shutil

try:
    import pypdfium2 as pdfium
except ImportError:
    print("Error: pypdfium2 not installed. Run: pip install pypdfium2")
    sys.exit(1)


def pdf_to_images(pdf_path, output_dir, scale=2.0):
    pdf = pdfium.PdfDocument(pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(pdf):
        bitmap = page.render(scale=scale)
        img = bitmap.to_pil()
        output_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
        img.save(output_path, "PNG")
        print(f"Saved: {output_path}")

    print(f"\nDone. {len(pdf)} page(s) exported to: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    pdf_to_images(pdf_path, output_dir, scale)
