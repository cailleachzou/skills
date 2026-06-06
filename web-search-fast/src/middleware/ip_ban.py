"""IP ban middleware — blocks requests from banned IPs."""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class IPBanMiddleware(BaseHTTPMiddleware):
    """Reject requests from banned IP addresses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        ip = request.client.host if request.client else "unknown"
        try:
            from src.admin.repository import is_ip_banned
            if await is_ip_banned(ip):
                logger.warning("Blocked banned IP: %s", ip)
                return JSONResponse({"error": "IP address is banned"}, status_code=403)
        except Exception:
            # DB not initialized yet or error — let request through
            pass
        return await call_next(request)
