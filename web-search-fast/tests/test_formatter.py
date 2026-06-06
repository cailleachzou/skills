from __future__ import annotations
import pytest

from src.api.schemas import SearchResponse, SearchResult, SearchMetadata, SubLink
from src.config import SearchEngine
from src.formatter.json_fmt import format_json
from src.formatter.markdown_fmt import format_markdown


def _make_response(depth: int = 1) -> SearchResponse:
    results = [
        SearchResult(
            title="Example Page",
            url="https://example.com",
            snippet="An example snippet",
            content="Full page content here" if depth >= 2 else "",
            sub_links=[
                SubLink(url="https://sub.example.com", title="Sub Page", content="Sub content")
            ] if depth >= 3 else [],
        )
    ]
    return SearchResponse(
        query="test query",
        engine=SearchEngine.GOOGLE,
        depth=depth,
        total=len(results),
        results=results,
        metadata=SearchMetadata(elapsed_ms=500, engine=SearchEngine.GOOGLE, depth=depth),
    )


class TestJsonFormatter:
    def test_returns_dict(self):
        resp = _make_response()
        data = format_json(resp)
        assert isinstance(data, dict)
        assert data["query"] == "test query"
        assert len(data["results"]) == 1

    def test_depth2_includes_content(self):
        data = format_json(_make_response(depth=2))
        assert data["results"][0]["content"] == "Full page content here"


class TestMarkdownFormatter:
    def test_returns_string(self):
        md = format_markdown(_make_response())
        assert isinstance(md, str)
        assert "# Search Results: test query" in md

    def test_depth1_no_content_section(self):
        md = format_markdown(_make_response(depth=1))
        assert "### Content" not in md

    def test_depth2_has_content(self):
        md = format_markdown(_make_response(depth=2))
        assert "### Content" in md
        assert "Full page content here" in md

    def test_depth3_has_sub_links(self):
        md = format_markdown(_make_response(depth=3))
        assert "### Sub Links" in md
        assert "Sub Page" in md
