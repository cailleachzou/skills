from __future__ import annotations
import pytest
from src.scraper.parser import extract_main_content, extract_links, extract_main_content_markdown


SAMPLE_HTML = """
<html>
<head><title>Test</title></head>
<body>
<nav>Navigation</nav>
<main>
<h1>Main Title</h1>
<p>This is the main content paragraph.</p>
<a href="https://example.com/link1">Link 1</a>
<a href="/relative">Relative Link</a>
<a href="javascript:void(0)">JS Link</a>
</main>
<footer>Footer</footer>
</body>
</html>
"""


class TestExtractMainContent:
    def test_extracts_main_text(self):
        text = extract_main_content(SAMPLE_HTML)
        assert "Main Title" in text
        assert "main content paragraph" in text
        assert "Navigation" not in text
        assert "Footer" not in text

    def test_empty_html(self):
        assert extract_main_content("") == ""

    def test_no_main_tag(self):
        html = "<html><body><p>Hello</p></body></html>"
        text = extract_main_content(html)
        assert "Hello" in text


class TestExtractMainContentMarkdown:
    def test_returns_markdown(self):
        md = extract_main_content_markdown(SAMPLE_HTML)
        assert "Main Title" in md
        assert "main content paragraph" in md


class TestExtractLinks:
    def test_extracts_http_links(self):
        links = extract_links(SAMPLE_HTML)
        urls = [l["url"] for l in links]
        assert "https://example.com/link1" in urls

    def test_resolves_relative_links(self):
        links = extract_links(SAMPLE_HTML, base_url="https://example.com")
        urls = [l["url"] for l in links]
        assert "https://example.com/relative" in urls

    def test_skips_javascript_links(self):
        links = extract_links(SAMPLE_HTML)
        urls = [l["url"] for l in links]
        for u in urls:
            assert not u.startswith("javascript:")

    def test_deduplicates(self):
        html = '<html><body><a href="https://a.com">A</a><a href="https://a.com">A2</a></body></html>'
        links = extract_links(html)
        assert len(links) == 1
