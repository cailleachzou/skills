#!/usr/bin/env python3
"""Integration test script — starts the server and runs live search tests."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlencode

# ── colours ──────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

HOST = "127.0.0.1"
PORT = 8000
BASE = f"http://{HOST}:{PORT}"

# ── helpers ──────────────────────────────────────────────────────────────────

def log_info(msg: str) -> None:
    print(f"{CYAN}[INFO]{RESET} {msg}")


def log_pass(msg: str) -> None:
    print(f"{GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str) -> None:
    print(f"{RED}[FAIL]{RESET} {msg}")


def log_warn(msg: str) -> None:
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def log_section(title: str) -> None:
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")


def http_get(path: str, timeout: int = 60) -> tuple[int, dict | str]:
    """Send GET request and return (status_code, body)."""
    url = f"{BASE}{path}"
    req = Request(url)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except URLError as e:
        return 0, str(e)


# ── server lifecycle ─────────────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    """Start uvicorn in a subprocess and wait until healthy."""
    log_info(f"Starting server on {BASE} ...")
    env = os.environ.copy()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", HOST, "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    # Wait for health check
    for i in range(40):
        time.sleep(1)
        try:
            status, body = http_get("/health", timeout=3)
            if status == 200 and isinstance(body, dict) and body.get("pool_ready"):
                log_pass(f"Server healthy (attempt {i + 1})")
                return proc
        except Exception:
            pass

    proc.kill()
    raise RuntimeError("Server failed to start within 40 seconds")


def stop_server(proc: subprocess.Popen) -> None:
    """Gracefully stop the server."""
    log_info("Stopping server ...")
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_info("Server stopped.")


# ── test cases ───────────────────────────────────────────────────────────────

passed = 0
failed = 0
warned = 0


def assert_test(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        log_pass(name)
        passed += 1
    else:
        log_fail(f"{name}  {detail}")
        failed += 1


def test_health() -> None:
    log_section("Health Check")
    status, body = http_get("/health")
    assert_test("GET /health returns 200", status == 200)
    assert_test("pool_ready is True", isinstance(body, dict) and body.get("pool_ready") is True)


def test_search_get(query: str, engine: str, depth: int, max_results: int) -> dict | None:
    """Run a GET /search test and return the response body."""
    params = urlencode({"q": query, "engine": engine, "depth": depth, "max_results": max_results})
    path = f"/search?{params}"
    timeout = 120 if depth >= 2 else 60

    log_info(f"GET /search  query={query!r}  engine={engine}  depth={depth}  max_results={max_results}")
    status, body = http_get(path, timeout=timeout)

    if status != 200:
        log_fail(f"HTTP {status}: {body}")
        return None

    assert_test(
        f"[{engine}] depth={depth} returns 200",
        status == 200,
    )
    assert_test(
        f"[{engine}] depth={depth} has results",
        isinstance(body, dict) and body.get("total", 0) > 0,
        f"total={body.get('total', 0) if isinstance(body, dict) else 'N/A'}",
    )

    if isinstance(body, dict):
        used_engine = body.get("engine", engine)
        if used_engine != engine:
            global warned
            log_warn(f"[{engine}] fell back to {used_engine}")
            warned += 1

        results = body.get("results", [])
        for i, r in enumerate(results[:3]):
            title = r.get("title", "")[:60]
            url = r.get("url", "")[:80]
            has_content = bool(r.get("content"))
            content_flag = " [+content]" if has_content else ""
            sub_count = len(r.get("sub_links", []))
            sub_flag = f" [+{sub_count} sub_links]" if sub_count else ""
            log_info(f"  [{i}] {title}")
            log_info(f"       {url}{content_flag}{sub_flag}")

        if depth >= 2:
            has_any_content = any(r.get("content") for r in results)
            assert_test(
                f"[{engine}] depth={depth} has content in results",
                has_any_content,
            )

        if depth >= 3:
            has_any_sublinks = any(r.get("sub_links") for r in results)
            assert_test(
                f"[{engine}] depth={depth} has sub_links",
                has_any_sublinks,
            )

    return body if isinstance(body, dict) else None


def test_search_post(query: str) -> None:
    """Test POST /search endpoint."""
    log_info(f"POST /search  query={query!r}")
    url = f"{BASE}/search"
    payload = json.dumps({"query": query, "engine": "duckduckgo", "depth": 1, "max_results": 3}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as resp:
            status = resp.status
            body = json.loads(resp.read().decode())
    except URLError as e:
        status = 0
        body = str(e)

    assert_test("POST /search returns 200", status == 200)
    if isinstance(body, dict):
        assert_test("POST /search has results", body.get("total", 0) > 0)


def test_markdown_format(query: str) -> None:
    """Test markdown output format."""
    params = urlencode({"q": query, "engine": "duckduckgo", "depth": 1, "format": "markdown", "max_results": 3})
    path = f"/search?{params}"
    log_info(f"GET /search format=markdown")
    status, body = http_get(path)
    assert_test("Markdown format returns 200", status == 200)
    assert_test("Markdown contains header", isinstance(body, str) and "# Search Results" in body)
    if isinstance(body, str):
        log_info(f"  Markdown preview (first 200 chars):")
        for line in body[:200].split("\n"):
            log_info(f"    {line}")


def test_validation() -> None:
    """Test request validation."""
    log_section("Request Validation")

    # Missing query
    status, _ = http_get("/search")
    # FastAPI returns 422 for validation errors, but urlopen raises on 4xx
    # We just check it's not 200
    assert_test("Missing query rejected", status != 200, f"status={status}")

    # Invalid depth
    status, _ = http_get("/search?q=test&depth=99")
    assert_test("Invalid depth rejected", status != 200, f"status={status}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Live integration tests for web-search-mcp")
    parser.add_argument("-q", "--query", default="firsh.me blog", help="Search query (default: 'firsh.me blog')")
    parser.add_argument("-e", "--engines", nargs="+", default=["duckduckgo", "google", "bing"],
                        choices=["google", "bing", "duckduckgo"], help="Engines to test")
    parser.add_argument("-d", "--max-depth", type=int, default=2, choices=[1, 2, 3],
                        help="Max depth to test (default: 2)")
    parser.add_argument("-n", "--max-results", type=int, default=3, help="Max results per search (default: 3)")
    parser.add_argument("--no-server", action="store_true", help="Skip server start (assume already running)")
    args = parser.parse_args()

    print(f"\n{BOLD}Web Search MCP — Live Integration Tests{RESET}")
    print(f"Query: {args.query!r}  Engines: {args.engines}  Max depth: {args.max_depth}\n")

    proc = None
    if not args.no_server:
        proc = start_server()

    try:
        # 1. Health check
        test_health()

        # 2. Search each engine at each depth
        for engine in args.engines:
            for depth in range(1, args.max_depth + 1):
                log_section(f"Search: engine={engine}  depth={depth}")
                test_search_get(args.query, engine, depth, args.max_results)

        # 3. POST endpoint
        log_section("POST /search")
        test_search_post(args.query)

        # 4. Markdown format
        log_section("Markdown Format")
        test_markdown_format(args.query)

        # 5. Validation
        test_validation()

    finally:
        if proc:
            stop_server(proc)

    # Summary
    log_section("Summary")
    total = passed + failed
    print(f"  {GREEN}Passed: {passed}{RESET}")
    print(f"  {RED}Failed: {failed}{RESET}")
    if warned:
        print(f"  {YELLOW}Warnings: {warned} (engine fallbacks){RESET}")
    print(f"  Total:  {total}")
    print()

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
