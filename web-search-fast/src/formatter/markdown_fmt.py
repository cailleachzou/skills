from __future__ import annotations

from src.api.schemas import SearchResponse, SearchResult


def format_result_markdown(idx: int, result: SearchResult, depth: int) -> str:
    """Format a single search result as markdown."""
    lines = [
        f"## {idx}. {result.title}",
        f"**URL:** {result.url}",
        "",
    ]
    if result.snippet:
        lines.append(f"> {result.snippet}")
        lines.append("")

    if depth >= 2 and result.content:
        lines.append("### Content")
        lines.append("")
        # Truncate very long content for readability
        content = result.content[:10000]
        lines.append(content)
        lines.append("")

    if depth >= 3 and result.sub_links:
        lines.append("### Sub Links")
        lines.append("")
        for sub in result.sub_links:
            lines.append(f"#### [{sub.title or sub.url}]({sub.url})")
            if sub.content:
                lines.append("")
                lines.append(sub.content[:3000])
            lines.append("")

    return "\n".join(lines)


def format_markdown(response: SearchResponse) -> str:
    """Format the full search response as a markdown document."""
    lines = [
        f"# Search Results: {response.query}",
        "",
        f"**Engine:** {response.engine} | **Depth:** {response.depth} | **Results:** {response.total}",
        f"**Time:** {response.metadata.elapsed_ms}ms | **Timestamp:** {response.metadata.timestamp}",
        "",
        "---",
        "",
    ]

    for idx, result in enumerate(response.results, 1):
        lines.append(format_result_markdown(idx, result, response.depth))
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
