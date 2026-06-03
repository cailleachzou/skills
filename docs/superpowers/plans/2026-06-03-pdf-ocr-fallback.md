# PDF Skill — OCR/MCP Fallback Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-page fallback chain (pdfplumber → UMI-OCR → MCP vision marker) to the `pdf` skill so mixed/scanned PDFs are handled automatically.

**Architecture:** Replace `scripts/extract_and_prompt.py` with `scripts/extract_with_fallback.py`. New script owns Phases 1-3 (text extract, OCR fallback, vision marker); Claude in the main session owns Phase 4 (MCP vision call + inline write-back). UMI-OCR integration is a standalone module `scripts/ocr_client.py` for testability.

**Tech Stack:** Python 3 (Windows: `python` per CLAUDE.md), pdfplumber, pypdfium2, stdlib `urllib`/`base64`/`json`, pytest, Umi-OCR HTTP API at `http://127.0.0.1:1224`.

**Project Conventions (per CLAUDE.md):**
- Windows Python: use `python` (not `python3`)
- Windows paths in user-facing output use `\`; bash commands use `/`
- Bash heredoc / forward slashes for paths
- Commit messages: `git commit -m "..."` with HEREDOC

---

## File Structure

| File | Responsibility |
|---|---|
| `pdf/scripts/ocr_client.py` | UMI-OCR HTTP client: ping, start, call, error handling. Pure module, no PDF logic. |
| `pdf/scripts/extract_with_fallback.py` | CLI entry. Owns 4 classes (`TextExtractor`, `OCRFallback` wrapper, `VisionMarker`, `OutputMerger`) + `main()`. |
| `pdf/tests/conftest.py` | pytest fixtures: sample text-only/scanned/mixed PDFs generated via reportlab. |
| `pdf/tests/test_ocr_client.py` | Unit tests for UMI-OCR client (mocked HTTP). |
| `pdf/tests/test_extract_with_fallback.py` | Integration tests: full pipeline against generated PDFs (OCR can be skipped/mocked). |
| `pdf/tests/pytest.ini` | Minimal pytest config (testpaths = tests). |
| `pdf/evals/evals.json` | Project-convention eval scenarios (3 cases). |
| `pdf/SKILL.md` | Modified: replace `extract_and_prompt.py` refs, add fallback decision tree, MCP write-back guide. |
| `docs/superpowers/specs/2026-06-03-pdf-ocr-fallback-design.md` | (Already exists — the spec.) |

`pdf/scripts/extract_and_prompt.py` is **deleted** in Task 1 (git history keeps it).

---

## Task 1: Test infrastructure + delete old script

**Files:**
- Create: `pdf/tests/pytest.ini`
- Create: `pdf/tests/conftest.py`
- Create: `pdf/tests/__init__.py`
- Delete: `pdf/scripts/extract_and_prompt.py`

- [ ] **Step 1: Create `pdf/tests/pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
```

- [ ] **Step 2: Create empty `pdf/tests/__init__.py`**

```python
# Makes tests/ a package for pytest discovery
```

- [ ] **Step 3: Create `pdf/tests/conftest.py` with PDF fixtures**

```python
"""Shared pytest fixtures: generate sample PDFs in-memory."""
import os
import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image


@pytest.fixture
def text_only_pdf(tmp_path):
    """3 pages, each with extractable text (pdfplumber will succeed)."""
    pdf_path = tmp_path / "text_only.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    for i in range(1, 4):
        c.drawString(100, 700, f"Page {i} body text — at least fifty characters to pass the threshold check easily.")
        c.showPage()
    c.save()
    return str(pdf_path)


@pytest.fixture
def scanned_pdf(tmp_path):
    """3 pages, each is a rendered image (no text layer → pdfplumber returns empty)."""
    from pdf2image import convert_from_path
    # First create a text PDF
    src = tmp_path / "_src.pdf"
    c = canvas.Canvas(str(src), pagesize=letter)
    for i in range(1, 4):
        c.drawString(100, 700, f"Page {i} rendered as image.")
        c.showPage()
    c.save()
    # Convert each page to image, then rebuild PDF with images only
    images = convert_from_path(str(src), dpi=150)
    out = tmp_path / "scanned.pdf"
    images[0].save(str(out), save_all=True, append_images=images[1:])
    return str(out)


@pytest.fixture
def mixed_pdf(tmp_path):
    """3 pages: 1 text, 1 image, 1 text."""
    from pdf2image import convert_from_path
    src = tmp_path / "_src.pdf"
    c = canvas.Canvas(str(src), pagesize=letter)
    for i in range(1, 4):
        c.drawString(100, 700, f"Page {i} content for mixing test.")
        c.showPage()
    c.save()
    images = convert_from_path(str(src), dpi=150)
    out = tmp_path / "mixed.pdf"
    # Build new PDF: page 1 image, page 2 image+text overlay, page 3 image+text
    # Simpler: save all as images (forces OCR path) — we'll mock OCR for this test
    images[0].save(str(out), save_all=True, append_images=images[1:])
    return str(out)


@pytest.fixture
def output_dir(tmp_path):
    """Output directory for scripts to write into."""
    d = tmp_path / "out"
    d.mkdir()
    return str(d)
```

Note: `scanned_pdf` and `mixed_pdf` both produce image-only PDFs (no text layer). The "mixed" nature is then simulated in the integration test by mocking the per-page text extraction to return text for some pages and empty for others. Keep fixture simple.

- [ ] **Step 4: Verify pytest works**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/ --collect-only`
Expected: "no tests ran" or "collected 0 items" — but no import errors.

- [ ] **Step 5: Delete old script**

```bash
git rm pdf/scripts/extract_and_prompt.py
```

- [ ] **Step 6: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/tests/ pdf/scripts/extract_and_prompt.py
git commit -m "$(cat <<'EOF'
test(pdf): add pytest infra; remove deprecated extract_and_prompt.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Build `ocr_client.py` — TDD

**Files:**
- Create: `pdf/scripts/ocr_client.py`
- Create: `pdf/scripts/__init__.py`
- Create: `pdf/tests/test_ocr_client.py`

- [ ] **Step 1: Write failing test for ping**

Create `pdf/tests/test_ocr_client.py`:

```python
"""Unit tests for ocr_client (UMI-OCR HTTP wrapper)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from scripts.ocr_client import OCRClient, OCRUnavailable


@pytest.fixture
def client():
    return OCRClient(host="127.0.0.1", port=1224, exe_path="C:/fake/Umi-OCR.exe")


def test_ping_returns_true_when_service_alive(client):
    with patch.object(client, "_http_get", return_value="pong"):
        assert client.ping() is True


def test_ping_raises_when_connection_refused(client):
    with patch.object(client, "_http_get", side_effect=OCRUnavailable("refused")):
        with pytest.raises(OCRUnavailable):
            client.ping()
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_ocr_client.py -v`
Expected: ImportError (no `scripts.ocr_client` yet).

- [ ] **Step 3: Create `pdf/scripts/__init__.py`**

```python
# Makes scripts/ a package
```

- [ ] **Step 4: Write minimal `ocr_client.py` to pass test**

Create `pdf/scripts/ocr_client.py`:

```python
"""UMI-OCR HTTP API client.

Wraps the offline Umi-OCR engine (Rapid v2.1.5+) at http://127.0.0.1:1224.
Provides ping/ensure-running/recognize_image with graceful error handling.
"""
import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1224
DEFAULT_EXE = r"C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\Umi-OCR.exe"
PING_PATH = "/umiocr"
OCR_PATH = "/api/ocr"
STARTUP_WAIT_SEC = 5


class OCRUnavailable(Exception):
    """Raised when Umi-OCR service cannot be reached."""


class OCRClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, exe_path=DEFAULT_EXE, timeout=10):
        self.host = host
        self.port = port
        self.exe_path = exe_path
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

    def _http_get(self, path):
        req = urllib.request.Request(self.base_url + path)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _http_post_json(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def ping(self):
        """Return True if service responds. Raise OCRUnavailable if not."""
        try:
            self._http_get(PING_PATH)
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            raise OCRUnavailable(f"Umi-OCR not reachable at {self.base_url}: {e}")

    def ensure_running(self):
        """Ping; if down, start the exe and re-ping after wait. Return True if up."""
        try:
            self.ping()
            return True
        except OCRUnavailable:
            pass
        if not os.path.exists(self.exe_path):
            raise OCRUnavailable(f"Umi-OCR exe not found at {self.exe_path}")
        # Start the exe detached
        subprocess.Popen(
            [self.exe_path],
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
            close_fds=False,
        )
        time.sleep(STARTUP_WAIT_SEC)
        try:
            self.ping()
            return True
        except OCRUnavailable as e:
            raise OCRUnavailable(f"Umi-OCR started but did not respond: {e}")

    def recognize_image(self, image_path, language="简体中文"):
        """Run OCR on a local image file. Return extracted text (may be empty)."""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {
            "base64": b64,
            "options": {
                "ocr.language": language,
                "tbpu.parser": "multi_para",
                "data.format": "text",
            },
        }
        resp = self._http_post_json(OCR_PATH, payload)
        if resp.get("code") != 100:
            raise OCRUnavailable(f"OCR error: {resp.get('data')}")
        return (resp.get("data") or "").strip()
```

- [ ] **Step 5: Run test, verify it passes**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_ocr_client.py -v`
Expected: 2 passed.

- [ ] **Step 6: Add test for `recognize_image`**

Append to `pdf/tests/test_ocr_client.py`:

```python
def test_recognize_image_returns_text_on_success(client, tmp_path):
    img = tmp_path / "test.png"
    # Minimal valid 1x1 PNG
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
        b"\xff?\x00\x05\xfe\x02\xfe\xa3W\xbd\xe0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    fake_resp = {"code": 100, "data": "识别结果"}
    with patch.object(client, "_http_post_json", return_value=fake_resp):
        result = client.recognize_image(str(img))
        assert result == "识别结果"


def test_recognize_image_raises_on_error_code(client, tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"not a real png")
    with patch.object(client, "_http_post_json", return_value={"code": 200, "data": "bad"}):
        with pytest.raises(OCRUnavailable):
            client.recognize_image(str(img))


def test_ensure_running_starts_exe_if_down(client):
    with patch.object(client, "ping", side_effect=[OCRUnavailable("down"), True]):
        with patch("scripts.ocr_client.subprocess.Popen") as mock_popen:
            with patch("scripts.ocr_client.time.sleep"):
                assert client.ensure_running() is True
                mock_popen.assert_called_once()
                args = mock_popen.call_args[0][0]
                assert args[0] == client.exe_path
```

- [ ] **Step 7: Run all ocr_client tests, verify pass**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_ocr_client.py -v`
Expected: 5 passed.

- [ ] **Step 8: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/__init__.py pdf/scripts/ocr_client.py pdf/tests/test_ocr_client.py
git commit -m "$(cat <<'EOF'
feat(pdf): add ocr_client (UMI-OCR HTTP wrapper) with tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Build `TextExtractor` class — TDD

**Files:**
- Create: `pdf/scripts/extract_with_fallback.py` (partial — TextExtractor only)
- Modify: `pdf/tests/test_extract_with_fallback.py`

- [ ] **Step 1: Write failing test for `TextExtractor`**

Append to `pdf/tests/test_extract_with_fallback.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py -v`
Expected: ImportError on `TextExtractor`.

- [ ] **Step 3: Implement `TextExtractor` + `PageResult` in `extract_with_fallback.py`**

Create `pdf/scripts/extract_with_fallback.py` with this content (we'll extend it in later tasks):

```python
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py::test_text_extractor_returns_per_page_results tests/test_extract_with_fallback.py::test_text_extractor_marks_scanned_pages -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/extract_with_fallback.py pdf/tests/test_extract_with_fallback.py
git commit -m "$(cat <<'EOF'
feat(pdf): TextExtractor — per-page pdfplumber extraction with threshold

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add image export to TextExtractor — TDD

**Files:**
- Modify: `pdf/scripts/extract_with_fallback.py` (add `export_images` method)
- Modify: `pdf/tests/test_extract_with_fallback.py`

- [ ] **Step 1: Write failing test for image export**

Append to `pdf/tests/test_extract_with_fallback.py`:

```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py::test_text_extractor_exports_images_for_no_text_pages -v`
Expected: AttributeError on `export_images`.

- [ ] **Step 3: Add `export_images` method**

In `pdf/scripts/extract_with_fallback.py`, add this to the `TextExtractor` class (keep everything else):

```python
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/extract_with_fallback.py pdf/tests/test_extract_with_fallback.py
git commit -m "$(cat <<'EOF'
feat(pdf): TextExtractor.export_images — render no-text pages to PNG

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Build OCR fallback integration in main pipeline — TDD with mocked OCR

**Files:**
- Modify: `pdf/scripts/extract_with_fallback.py` (add `run_ocr_fallback` function)
- Modify: `pdf/tests/test_extract_with_fallback.py`

- [ ] **Step 1: Write failing test**

Append to `pdf/tests/test_extract_with_fallback.py`:

```python
from unittest.mock import patch
from scripts.extract_with_fallback import run_ocr_fallback


def test_run_ocr_fallback_calls_ocr_for_no_text_pages(scanned_pdf, output_dir):
    extractor = TextExtractor(scanned_pdf, text_threshold=50)
    pages = extractor.extract()
    extractor.export_images([p for p in pages if not p.is_text_page()], output_dir)
    with patch("scripts.extract_with_fallback.OCRClient") as MockClient:
        instance = MockClient.return_value
        instance.ensure_running.return_value = True
        instance.recognize_image.return_value = "OCR'd text for page"
        run_ocr_fallback(pages, output_dir, ocr_lang="简体中文")
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
        instance.ensure_running.side_effect = Exception("OCR not available")
        run_ocr_fallback(pages, output_dir)
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
        run_ocr_fallback(pages, output_dir)
    for p in pages:
        if not p.is_text_page():
            assert p.source == "needs-vision"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py -k ocr_fallback -v`
Expected: ImportError on `run_ocr_fallback`.

- [ ] **Step 3: Implement `run_ocr_fallback` function**

Add to `pdf/scripts/extract_with_fallback.py` (top-level function, after imports):

```python
def run_ocr_fallback(pages, output_dir, ocr_lang="简体中文"):
    """Phase 2: for pages that pdfplumber couldn't read, try UMI-OCR.

    Mutates each PageResult in-place:
      - Sets source='umi-ocr' and ocr_text on success
      - Sets source='needs-vision' if OCR unavailable or returns empty
    Never raises; logs to stderr on failure.
    """
    import sys
    from scripts.ocr_client import OCRClient, OCRUnavailable

    no_text = [p for p in pages if not p.is_text_page()]
    if not no_text:
        return
    try:
        client = OCRClient()
        client.ensure_running()
    except (OCRUnavailable, Exception) as e:
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
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/extract_with_fallback.py pdf/tests/test_extract_with_fallback.py
git commit -m "$(cat <<'EOF'
feat(pdf): run_ocr_fallback — UMI-OCR phase with graceful degradation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Build `OutputMerger` — TDD

**Files:**
- Modify: `pdf/scripts/extract_with_fallback.py` (add `OutputMerger`)
- Modify: `pdf/tests/test_extract_with_fallback.py`

- [ ] **Step 1: Write failing test**

Append to `pdf/tests/test_extract_with_fallback.py`:

```python
from scripts.extract_with_fallback import OutputMerger


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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py::test_output_merger_writes_per_page_blocks -v`
Expected: ImportError on `OutputMerger`.

- [ ] **Step 3: Implement `OutputMerger`**

Add to `pdf/scripts/extract_with_fallback.py`:

```python
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd C:/Users/59620/.claude/skills/pdf && python -m pytest tests/test_extract_with_fallback.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/extract_with_fallback.py pdf/tests/test_extract_with_fallback.py
git commit -m "$(cat <<'EOF'
feat(pdf): OutputMerger — assemble per-page blocks with source tags

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Add table extraction + `main()` orchestration + CLI

**Files:**
- Modify: `pdf/scripts/extract_with_fallback.py` (add `extract_tables` + `main` + CLI)

- [ ] **Step 1: Add `extract_tables` function**

Append to `pdf/scripts/extract_with_fallback.py`:

```python
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
```

- [ ] **Step 2: Add `main()` orchestration**

Append:

```python
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

    # Phase 2: OCR fallback
    if not args.skip_ocr and no_text:
        print(f"[3/4] Running UMI-OCR fallback ...", file=sys.stderr)
        run_ocr_fallback(pages, args.output_dir, ocr_lang=args.ocr_lang)

    # Tables
    tables_path = os.path.join(args.output_dir, "extracted_tables.txt")
    if extract_tables(args.pdf_path, tables_path):
        print(f"[4/4] Tables written to {tables_path}", file=sys.stderr)
    else:
        print(f"[4/4] No tables found", file=sys.stderr)

    # Output merger
    text_path = os.path.join(args.output_dir, "extracted_text.txt")
    OutputMerger(pages).write(text_path)
    print(f"\nDone. Wrote: {text_path}", file=sys.stderr)

    needs_vision = [p for p in pages if p.source == "needs-vision"]
    if needs_vision:
        print(f"\n{len(needs_vision)} page(s) marked 'needs-vision'.", file=sys.stderr)
        print("Claude: read extracted_text.txt, find '=== Page N (source: needs-vision) ===' markers,", file=sys.stderr)
        print("        call mcp__MiniMax__understand_image for each, write results back to the file.", file=sys.stderr)


if __name__ == "__main__":
    import sys
    main()
```

- [ ] **Step 3: Smoke test — text-only PDF (no OCR needed)**

Run:
```bash
cd C:/Users/59620/.claude/skills
python -c "
import sys
sys.path.insert(0, 'pdf')
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
c = canvas.Canvas('/tmp/smoke_text.pdf', pagesize=letter)
for i in range(1, 4):
    c.drawString(100, 700, f'Page {i} — sample body text over fifty chars to pass the threshold check.')
    c.showPage()
c.save()
" && python pdf/scripts/extract_with_fallback.py /tmp/smoke_text.pdf /tmp/smoke_out --skip-ocr
```

Expected stderr:
```
[1/4] Extracting text from /tmp/smoke_text.pdf ...
      3 page(s), 0 need fallback
[2/4] Exporting 0 no-text page(s) to PNG ...
[3/4] Running UMI-OCR fallback ...
[4/4] No tables found
Done. Wrote: /tmp/smoke_out/extracted_text.txt
```

Verify content:
```bash
cat /tmp/smoke_out/extracted_text.txt
```
Expected: 3 blocks each with `(source: pdfplumber)`.

- [ ] **Step 4: Smoke test — scanned PDF with mocked OCR**

```bash
cd C:/Users/59620/.claude/skills
python -c "
import sys
sys.path.insert(0, 'pdf')
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pdf2image import convert_from_path
c = canvas.Canvas('/tmp/_s.pdf', pagesize=letter)
for i in range(3):
    c.drawString(100, 700, f'p{i+1}')
    c.showPage()
c.save()
imgs = convert_from_path('/tmp/_s.pdf', dpi=150)
imgs[0].save('/tmp/smoke_scanned.pdf', save_all=True, append_images=imgs[1:])
"
# Patch run_ocr_fallback to inject fake OCR result, just for this test
python -c "
import sys, os
sys.path.insert(0, 'pdf')
from scripts import extract_with_fallback as m
orig = m.run_ocr_fallback
def fake(pages, output_dir, ocr_lang='简体中文'):
    from scripts.ocr_client import OCRClient
    client = OCRClient()
    for p in pages:
        if not p.is_text_page() and p.image_path:
            p.source = 'umi-ocr'
            p.ocr_text = f'FAKE OCR for page {p.page_num}'
m.run_ocr_fallback = fake
sys.argv = ['x', '/tmp/smoke_scanned.pdf', '/tmp/smoke_out2']
m.main()
"
cat /tmp/smoke_out2/extracted_text.txt
```

Expected: 3 blocks, all marked `(source: umi-ocr)`.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/scripts/extract_with_fallback.py
git commit -m "$(cat <<'EOF'
feat(pdf): main() orchestration + CLI for extract_with_fallback

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update SKILL.md

**Files:**
- Modify: `pdf/SKILL.md` (replace "AI 视觉审图" section; update script refs)

- [ ] **Step 1: Replace "AI 视觉审图" section**

In `pdf/SKILL.md`, find the section starting with `## AI 视觉审图` and ending just before `## 下一步`. Replace the **entire** section with:

````markdown
## AI 视觉审图（带 OCR/MCP fallback）

新脚本 `extract_with_fallback.py` 把整个审图流程串起来：先用 pdfplumber 逐页抽文，**抽不到文字的页自动调 UMI-OCR**，**OCR 也抽不到的页标记为 `needs-vision`**，由 Claude 在主会话里调 `mcp__MiniMax__understand_image` 做语义理解。

### 调用方式

```bash
python scripts/extract_with_fallback.py <input.pdf> <output_dir> \
    [--ocr-lang 简体中文] [--text-threshold 50] [--scale 2.0] \
    [--skip-ocr]
```

输出到 `<output_dir>/`：
- `extracted_text.txt` — 合并结果，每页带来源标签
- `extracted_tables.txt` — 表格（如果有）
- `page_NNN.png` — 导出的页面图（OCR 和 vision 共用）

### 决策树

```
每页 pdfplumber 抽文
   ├─ char_count ≥ 阈值（默认 50）→ 标签 (source: pdfplumber)
   └─ char_count < 阈值 → 导出 PNG → UMI-OCR
                              ├─ OCR 成功 → 标签 (source: umi-ocr)
                              └─ OCR 失败/空 → 标签 (source: needs-vision)
                                                  ↓
                                        Claude 调 mcp__MiniMax__understand_image
                                                  ↓
                                        Claude 把结果回写到 extracted_text.txt
```

### 逐页标签格式

```
=== Page 1 (source: pdfplumber) ===
[正文...]

=== Page 2 (source: umi-ocr) ===
[OCR 抽出的文字...]

=== Page 3 (source: needs-vision) ===
[image: page_003.png — please run mcp__MiniMax__understand_image for semantic understanding]
```

### Claude 侧：处理 `needs-vision` 标记

1. 读 `extracted_text.txt`，正则匹配 `=== Page (\d+) \(source: needs-vision\) ===` 块
2. 对每个匹配，取 `image:` 后的 PNG 路径
3. 调 `mcp__MiniMax__understand_image`，prompt 用下面模板（针对弱电/建筑审图）：
   ```
   你在看一份弱电/建筑专业图纸。请描述：
   - 图中可见的设备、机房、管井、点位
   - 系统标注（CCTV/门禁/BA/网络/消防等）
   - 房间名称、功能区
   - 标高、尺寸、比例尺
   - 任何文字标注（精确转写）
   ```
4. 把 vision 输出**就地替换**对应 `needs-vision` 块的内容（保留 `=== Page N (source: mcp-vision) ===` 头）
5. 改完保存回 `extracted_text.txt`

### 弱电/建筑审图增强

默认模板通用，针对专业场景可重点核查：
- 设备机房、弱电间、管井位置是否准确
- 系统标注（消防、安防、BA、网络点位）是否一致
- 比例尺、标高、尺寸标注是否正确
- 房间名称、功能标注与图纸是否匹配
````

- [ ] **Step 2: Update any other script references**

In `pdf/SKILL.md`, grep for `extract_and_prompt.py`. If found, replace with `extract_with_fallback.py`. Note: only the "AI 视觉审图" section uses it, so this is usually a no-op.

- [ ] **Step 3: Verify SKILL.md renders sensibly**

Run: `head -30 "C:/Users/59620/.claude/skills/pdf/SKILL.md"` and check structure.

- [ ] **Step 4: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/SKILL.md
git commit -m "$(cat <<'EOF'
docs(pdf): rewrite AI 视觉审图 section for fallback chain

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Write `evals/evals.json`

**Files:**
- Create: `pdf/evals/evals.json`

- [ ] **Step 1: Create the evals file**

Create `pdf/evals/evals.json`:

```json
{
  "evals": [
    {
      "id": "text_only_pdf",
      "name": "全文字 PDF — pdfplumber path only",
      "description": "验证当 pdfplumber 能抽到文字时，OCR 和 vision 都不会被触发。",
      "input_fixture": "tests/conftest.py:text_only_pdf",
      "command": "python scripts/extract_with_fallback.py <pdf> <out>",
      "expected": {
        "all_pages_have_source": "pdfplumber",
        "no_ocr_invocation": true,
        "no_needs_vision_markers": true
      }
    },
    {
      "id": "scanned_pdf",
      "name": "扫描件 PDF — UMI-OCR path",
      "description": "验证无文字页自动走 UMI-OCR，结果写入 (source: umi-ocr)。",
      "input_fixture": "tests/conftest.py:scanned_pdf",
      "command": "python scripts/extract_with_fallback.py <pdf> <out>",
      "expected": {
        "all_pages_have_source": "umi-ocr",
        "ocr_invocation_count_equals_page_count": true
      }
    },
    {
      "id": "mixed_pdf",
      "name": "混合 PDF — text + scanned pages interleaved",
      "description": "验证逐页判定正确：文字页走 pdfplumber，扫描页走 OCR（或 needs-vision）。",
      "input_fixture": "tests/conftest.py:mixed_pdf + manual page masking",
      "command": "python scripts/extract_with_fallback.py <pdf> <out>",
      "expected": {
        "text_pages_have_source": "pdfplumber",
        "scanned_pages_have_source_in": ["umi-ocr", "needs-vision"],
        "page_order_preserved": true
      }
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
cd C:/Users/59620/.claude/skills
git add pdf/evals/evals.json
git commit -m "$(cat <<'EOF'
test(pdf): add evals.json with 3 fallback chain scenarios

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Final integration smoke test with real Tendo PDF

**Files:** none — manual verification only.

- [ ] **Step 1: Pick a real Tendo project PDF**

Use any existing Tendo project PDF (江阴博物馆 / Cooley / etc.) that the user has on disk. Confirm path with user if not already known.

- [ ] **Step 2: Run script on the real PDF**

```bash
cd C:/Users/59620/.claude/skills
python pdf/scripts/extract_with_fallback.py "<real_pdf_path>" /tmp/tendo_smoke
```

Verify:
- Script exits cleanly
- `/tmp/tendo_smoke/extracted_text.txt` exists and has per-page blocks
- Source tags match reality (text pages = pdfplumber; scanned = umi-ocr or needs-vision)
- `/tmp/tendo_smoke/page_NNN.png` files exist for any non-pdfplumber pages

- [ ] **Step 3: Manually run UMI-OCR if not already running**

If script reported UMI-OCR unavailable, start it:
```bash
"C:/Users/59620/Downloads/Programs/Umi-OCR_Rapid_v2.1.5/Umi-OCR.exe" &
sleep 8
```
Re-run the script. Verify UMI-OCR path is taken.

- [ ] **Step 4: Document any issues found**

If the smoke test reveals bugs (wrong threshold, bad UMI-OCR path, formatting issues), create a Task 11+ to address them, or fix inline and commit. **Do not declare done with known issues.**

- [ ] **Step 5: Final summary commit if any fixes were applied**

```bash
cd C:/Users/59620/.claude/skills
git add -A
git diff --cached --quiet || git commit -m "$(cat <<'EOF'
fix(pdf): smoke-test fixes from Tendo project run

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Checklist

Run after writing the plan, before handing off:

- [x] **Spec coverage:** every requirement in the spec maps to a task:
  - per-page trigger (text_threshold) → Tasks 3, 4
  - UMI-OCR HTTP integration → Tasks 2, 5
  - output format with source tags → Task 6
  - vision marker placeholder → Task 5, 6
  - SKILL.md fallback decision tree → Task 8
  - Claude MCP write-back instructions → Task 8
  - evals.json 3 cases → Task 9
  - real-world smoke test → Task 10
  - table extraction → Task 7
  - delete old script → Task 1
  - error handling (OCR down, empty result, bad lang) → Task 5, 2
- [x] **Placeholder scan:** no TBD/TODO/"similar to"/"appropriate error handling" without code. Every code step shows the actual code.
- [x] **Type consistency:** `PageResult.page_num` (1-based int), `is_text_page()`, `image_path`, `source`, `ocr_text` used consistently across Tasks 3-7. `OCRClient(host, port, exe_path, timeout)` signature stable across Tasks 2 & 5.
- [x] **Bite-sized steps:** each step is one action (write test, run, implement, run, commit). 2-5 min each.
- [x] **Frequent commits:** one commit per task minimum, sometimes two (test, then impl).
- [x] **TDD discipline:** tests written before impl in Tasks 2, 3, 4, 5, 6.

Ready for execution.
