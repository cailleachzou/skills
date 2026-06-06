from __future__ import annotations

from src.api.schemas import SearchResponse


def format_json(response: SearchResponse) -> dict:
    """Format search response as a JSON-serializable dict."""
    return response.model_dump(mode="json")
