from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.schemas import SearchResult, SearchResponse, SearchMetadata
from src.config import SearchEngine


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool._started = True
    return pool


@pytest.fixture
def client(mock_pool):
    from src.main import app
    from src.api.routes import set_browser_pool
    set_browser_pool(mock_pool)
    return TestClient(app)


def _make_response(query: str = "test") -> SearchResponse:
    return SearchResponse(
        query=query,
        engine=SearchEngine.GOOGLE,
        depth=1,
        total=1,
        results=[SearchResult(title="Test", url="https://example.com", snippet="A test result")],
        metadata=SearchMetadata(elapsed_ms=100, engine=SearchEngine.GOOGLE, depth=1),
    )


class TestHealthEndpoint:
    def test_health_ok(self, client, mock_pool):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["pool_ready"] is True


class TestSearchEndpoint:
    @patch("src.api.routes._do_search")
    def test_get_search_json(self, mock_search, client):
        mock_search.return_value = _make_response("hello")
        resp = client.get("/search?q=hello")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "hello"
        assert len(data["results"]) == 1

    @patch("src.api.routes._do_search")
    def test_get_search_markdown(self, mock_search, client):
        mock_search.return_value = _make_response("hello")
        resp = client.get("/search?q=hello&format=markdown")
        assert resp.status_code == 200
        assert "# Search Results" in resp.text

    @patch("src.api.routes._do_search")
    def test_post_search(self, mock_search, client):
        mock_search.return_value = _make_response("world")
        resp = client.post("/search", json={"query": "world"})
        assert resp.status_code == 200

    def test_get_search_missing_query(self, client):
        resp = client.get("/search")
        assert resp.status_code == 422

    def test_get_search_invalid_depth(self, client):
        resp = client.get("/search?q=test&depth=5")
        assert resp.status_code == 422
