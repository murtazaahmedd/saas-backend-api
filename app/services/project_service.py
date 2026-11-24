from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..errors import Errors
from ..interfaces import IIdempotencyRepository, IProjectRepository, IProjectService

log = logging.getLogger(__name__)


def encode_cursor(item: Dict[str, Any]) -> str:
    raw = json.dumps([item["created_at"], item["id"]]).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> Tuple[datetime, str]:
    try:
        created, pid = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        return datetime.fromisoformat(created), pid
    except (ValueError, TypeError):
        raise Errors.HTTP.BadRequest("cursor is invalid; use the next_cursor value from a previous page")


def request_hash(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class ProjectService(IProjectService):
    def __init__(self, projects: IProjectRepository, idempotency: IIdempotencyRepository) -> None:
        self._projects, self._idem = projects, idempotency

    def create(self, auth: Dict[str, Any], data: Dict[str, Any], idempotency_key: Optional[str]) -> Tuple[Dict[str, Any], bool]:
        """Returns (project, replayed). A repeated key with the same body replays; a different body conflicts."""
        org = auth["organization_id"]
        if idempotency_key:
            stored = self._idem.get(org, idempotency_key)
            if stored:
                if stored["request_hash"] != request_hash(data):
                    raise Errors.HTTP.Conflict("idempotency key was already used with a different request body")
                return stored["response"], True
        project = self._projects.create(org, auth["user_id"], data["name"], data.get("description", ""))
        if idempotency_key:
            self._idem.put(org, idempotency_key, request_hash(data), project, 201)
        log.info("project created", extra={"tenant_id": org, "project_id": project["id"]})
        return project, False

    def get(self, auth: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        return self._projects.get(auth["organization_id"], project_id)

    def list(self, auth: Dict[str, Any], status: Optional[str], cursor: Optional[str], limit: int) -> Dict[str, Any]:
        after_created, after_id = decode_cursor(cursor) if cursor else (None, None)
        page = self._projects.list(auth["organization_id"], status, after_created, after_id, limit)
        items = page["items"]
        return {"items": items, "next_cursor": encode_cursor(items[-1]) if page["has_more"] else None}

    def update(self, auth: Dict[str, Any], project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        if not patch:
            raise Errors.HTTP.BadRequest("nothing to update; send at least one field")
        return self._projects.update(auth["organization_id"], project_id, patch)

    def soft_delete(self, auth: Dict[str, Any], project_id: str) -> None:
        self._projects.soft_delete(auth["organization_id"], project_id)
