from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.schemas import SearchResponse, SearchResult, SearchMetadata
from src.config import SearchEngine


def _make_response(query: str = "test") -> SearchResponse:
    return SearchResponse(
        query=query,
        engine=SearchEngine.DUCKDUCKGO,
        depth=1,
        total=1,
        results=[SearchResult(title="Test", url="https://example.com", snippet="A test")],
        metadata=SearchMetadata(elapsed_ms=100, engine=SearchEngine.DUCKDUCKGO, depth=1),
    )


def _mock_ctx(started: bool = True) -> MagicMock:
    ctx = MagicMock()
    pool = MagicMock()
    pool._started = started
    pool._pool_size = 5
    ctx.request_context.lifespan_context = {"pool": pool}
    return ctx


class TestWebSearchTool:
    @pytest.mark.asyncio
    @patch("src.core.search.do_search", new_callable=AsyncMock)
    async def test_returns_markdown(self, mock_search):
        mock_search.return_value = _make_response("hello")
        from src.mcp_server import web_search

        ctx = _mock_ctx()
        result = await web_search(query="hello", ctx=ctx)
        assert "# Search Results" in result
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_invalid_engine(self):
        from src.mcp_server import web_search

        ctx = _mock_ctx()
        result = await web_search(query="test", engine="invalid", ctx=ctx)
        assert "Error" in result
        assert "invalid" in result

    @pytest.mark.asyncio
    @patch("src.core.search.do_search", new_callable=AsyncMock)
    async def test_clamps_depth(self, mock_search):
        mock_search.return_value = _make_response("test")
        from src.mcp_server import web_search

        ctx = _mock_ctx()
        await web_search(query="test", depth=99, ctx=ctx)
        call_args = mock_search.call_args
        req = call_args[0][1]
        assert req.depth == 3

    @pytest.mark.asyncio
    @patch("src.core.search.do_search", new_callable=AsyncMock)
    async def test_search_error_handled(self, mock_search):
        from src.core.search import SearchError
        mock_search.side_effect = SearchError("pool down")
        from src.mcp_server import web_search

        ctx = _mock_ctx()
        result = await web_search(query="test", ctx=ctx)
        assert "Search error" in result


class TestGetPageContentTool:
    @pytest.mark.asyncio
    @patch("src.core.search.fetch_url_content", new_callable=AsyncMock)
    async def test_returns_content(self, mock_fetch):
        mock_fetch.return_value = "# Hello World\n\nSome content"
        from src.mcp_server import get_page_content

        ctx = _mock_ctx()
        result = await get_page_content(url="https://example.com", ctx=ctx)
        assert "Content from https://example.com" in result
        assert "Hello World" in result

    @pytest.mark.asyncio
    @patch("src.core.search.fetch_url_content", new_callable=AsyncMock)
    async def test_empty_content(self, mock_fetch):
        mock_fetch.return_value = ""
        from src.mcp_server import get_page_content

        ctx = _mock_ctx()
        result = await get_page_content(url="https://example.com", ctx=ctx)
        assert "Could not extract" in result


class TestListSearchEnginesTool:
    @pytest.mark.asyncio
    async def test_lists_engines(self):
        from src.mcp_server import list_search_engines

        ctx = _mock_ctx()
        result = await list_search_engines(ctx=ctx)
        assert "google" in result
        assert "bing" in result
        assert "duckduckgo" in result
        assert "Pool size" in result


class TestPoolSingleton:
    def test_initial_state(self):
        import src.mcp_server as m
        # _pool_started should be bool
        assert isinstance(m._pool_started, bool)

    @pytest.mark.asyncio
    async def test_ensure_pool_creates_instance(self):
        """_ensure_pool creates a pool when none exists."""
        import src.mcp_server as m
        original_instance = m._pool_instance
        original_started = m._pool_started
        try:
            m._pool_instance = MagicMock()
            m._pool_instance.start = AsyncMock()
            m._pool_started = True
            pool = await m._ensure_pool()
            assert pool is m._pool_instance
        finally:
            m._pool_instance = original_instance
            m._pool_started = original_started
