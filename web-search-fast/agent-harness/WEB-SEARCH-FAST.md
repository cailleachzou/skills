# WEB-SEARCH-FAST — CLI Harness SOP

## Software Overview

**web-search-fast** (v0.4.1) is a high-performance web search service using Camoufox (stealth Firefox) to scrape Google, Bing, and DuckDuckGo. It exposes results as structured JSON/Markdown via MCP protocol and REST API.

**This CLI harness** wraps the core search engine for direct command-line usage — no server required.

## Architecture

```
CLI (Click + asyncio)
 └─ imports directly from src/
    ├─ src/core/search.py      → do_search(), fetch_url_content()
    ├─ src/scraper/browser.py  → BrowserPool
    ├─ src/api/schemas.py      → SearchRequest, SearchResponse
    ├─ src/formatter/          → format_json(), format_markdown()
    └─ src/config.py           → get_config(), enums
```

## Command Groups

| Group | Commands | Purpose |
|-------|----------|---------|
| `search` | `run`, `batch` | Execute searches |
| `fetch` | `url` | Fetch single URL content |
| `engine` | `list`, `probe` | Engine management |
| `session` | `save`, `load`, `show` | Session persistence |
| `pool` | `status` | Browser pool health |

## Key Design Decisions

1. **Direct import** — no HTTP server needed; imports `src.*` modules directly
2. **Async lifecycle** — each command does `pool.start()` → work → `pool.stop()`
3. **Session state** — JSON file at `~/.cli-anything-web-search-fast/session.json`
4. **Auto-save** — search/fetch results auto-save to session after one-shot mutations
5. **--dry-run** — shows search parameters without executing
6. **--json** — machine-readable output for AI agents

## Environment Variables

All `BROWSER_*` env vars from web-search-fast are supported:

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_POOL_SIZE` | 30 | Concurrency slots |
| `BROWSER_MAX_POOL_SIZE` | 90 | Max auto-scaled slots |
| `BROWSER_PROXY` | — | Proxy URL |
| `BROWSER_OS` | — | OS fingerprint |
| `BROWSER_BLOCK_WEBGL` | false | Block WebGL |
| `BROWSER_FONTS` | — | Custom fonts (comma-separated) |
| `BROWSER_ADDONS` | — | Firefox addons |
| `BROWSER_PROXY_LIST` | — | Proxy list file |

## Installation

```bash
cd web-search-fast/agent-harness
pip install -e .
```

## Prerequisites

- Python 3.10+
- Camoufox browser fetched: `python -m camoufox fetch`
- All web-search-fast dependencies installed
