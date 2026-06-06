#!/usr/bin/env bash
# Build web-search-mcp with Nuitka for optimized performance
# Usage:
#   ./scripts/build-nuitka.sh              # Build standalone binary
#   ./scripts/build-nuitka.sh --module     # Build accelerated .so modules only
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python}"
OUTPUT_DIR="$PROJECT_DIR/dist/nuitka"
ENTRY="$PROJECT_DIR/src/mcp_server.py"

echo "=== Nuitka Build ==="
echo "  Python:  $($PYTHON --version)"
echo "  Nuitka:  $($PYTHON -m nuitka --version | head -1)"
echo "  Entry:   $ENTRY"
echo "  Output:  $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

if [ "${1:-}" = "--module" ]; then
    echo "Building accelerated modules (.so) ..."
    $PYTHON -m nuitka \
        --module \
        --include-package=src \
        --output-dir="$OUTPUT_DIR" \
        "$PROJECT_DIR/src"
    echo "Done. Modules in $OUTPUT_DIR"
    exit 0
fi

echo "Building standalone binary ..."
$PYTHON -m nuitka \
    --standalone \
    --onefile \
    --output-dir="$OUTPUT_DIR" \
    --output-filename="web-search-mcp" \
    \
    --follow-imports \
    --include-package=src \
    --include-package=mcp \
    --include-package=starlette \
    --include-package=uvicorn \
    --include-package=fastapi \
    --include-package=pydantic \
    --include-package=pydantic_core \
    --include-package=httpx \
    --include-package=httpcore \
    --include-package=anyio \
    --include-package=bs4 \
    --include-package=lxml \
    --include-package=markdownify \
    --include-package=camoufox \
    --include-package=playwright \
    --include-package=certifi \
    --include-package=h11 \
    --include-package=sniffio \
    --include-package=idna \
    --include-package=typing_extensions \
    \
    --include-module=uvloop \
    --include-module=httptools \
    \
    --nofollow-import-to=pytest \
    --nofollow-import-to=_pytest \
    --nofollow-import-to=setuptools \
    --nofollow-import-to=pip \
    --nofollow-import-to=mypy \
    --nofollow-import-to=ruff \
    \
    --enable-plugin=anti-bloat \
    --prefer-source-code \
    \
    --python-flag=no_site \
    --python-flag=-O \
    \
    "$ENTRY"

echo ""
echo "=== Build Complete ==="
ls -lh "$OUTPUT_DIR/web-search-mcp"
echo ""
echo "Run: $OUTPUT_DIR/web-search-mcp --transport http --host 0.0.0.0 --port 8897"
