"""@http_error_handler maps AppError to JSON responses; @enforce authenticates, authorises and rate-limits.

Order on every endpoint:

    @router.post("/path")
    @http_error_handler
    @enforce(permission)
    def endpoint(request: Request, ...): ...
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from ..errors import AppError, Errors

log = logging.getLogger(__name__)


def _find_request(args: tuple, kwargs: dict) -> Request:
    for value in list(args) + list(kwargs.values()):
        if isinstance(value, Request):
            return value
    raise RuntimeError("[enforce] endpoint must declare a `request: Request` parameter")


def http_error_handler(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except AppError as exc:
            return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "detail": exc.message})
        except Exception:
            log.exception("unhandled error")
            return JSONResponse(status_code=500, content={"error": "internal_error", "detail": "unexpected error"})
    return wrapper


def enforce(permission: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _find_request(args, kwargs)
            header = request.headers.get("authorization", "")
            if not header.lower().startswith("bearer "):
                raise Errors.HTTP.Unauthorized("missing bearer token")
            services = request.app.state.services
            auth = services.auth.authorize(header[7:], permission)
            request.state.auth = auth
            return fn(*args, **kwargs)
        return wrapper
    return decorator
