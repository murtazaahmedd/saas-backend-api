"""Database session: the only place SQL is executed. It only ever calls api.* functions."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import psycopg
from psycopg_pool import ConnectionPool

from ..errors import SQLSTATE_ERRORS, Errors

log = logging.getLogger(__name__)
_FN = re.compile(r"^api\.[a-z_]+$")


class Database:
    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10) -> None:
        self.pool = ConnectionPool(dsn, min_size=min_size, max_size=max_size, open=True)

    def call(self, function: str, *args: Any) -> Optional[Any]:
        """SELECT api.<function>(args...) in its own transaction, mapping SQLSTATE codes to app errors."""
        if not _FN.match(function):
            raise ValueError(f"[Database.call] only api.* functions may be called, got {function!r}")
        placeholders = ", ".join(["%s"] * len(args))
        params = [json.dumps(a) if isinstance(a, dict) else a for a in args]
        try:
            with self.pool.connection() as conn:
                row = conn.execute(f"SELECT {function}({placeholders})", params).fetchone()
                return row[0] if row else None
        except psycopg.Error as exc:
            error = SQLSTATE_ERRORS.get(exc.sqlstate or "")
            if error:
                raise error(exc.diag.message_primary or str(exc)) from exc
            log.exception("database call failed", extra={"function": function})
            raise Errors.HTTP.InternalServerError(f"database call {function} failed") from exc

    def close(self) -> None:
        self.pool.close()
