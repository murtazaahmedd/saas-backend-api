from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from ..interfaces import IAuthRepository, IIdempotencyRepository, IProjectRepository, IUserRepository
from .database import Database


class AuthRepository(IAuthRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def enforce(self, user_id: str, organization_id: str, permission: str) -> Dict[str, Any]:
        return self._db.call("api.enforce", user_id, organization_id, permission)


class UserRepository(IUserRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def signup(self, org_name: str, email: str, password_hash: str) -> Dict[str, Any]:
        return self._db.call("api.signup", org_name, email, password_hash)

    def create(self, organization_id: str, email: str, password_hash: str, role: str) -> Dict[str, Any]:
        return self._db.call("api.user_create", organization_id, email, password_hash, role)

    def credentials(self, email: str) -> Optional[Dict[str, Any]]:
        return self._db.call("api.user_credentials", email)


class ProjectRepository(IProjectRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, organization_id: str, user_id: str, name: str, description: str) -> Dict[str, Any]:
        return self._db.call("api.project_create", organization_id, user_id, name, description)

    def get(self, organization_id: str, project_id: str) -> Dict[str, Any]:
        return self._db.call("api.project_get", organization_id, project_id)

    def list(self, organization_id: str, status: Optional[str], after_created: Optional[datetime],
             after_id: Optional[str], limit: int) -> Dict[str, Any]:
        return self._db.call("api.project_list", organization_id, status, after_created, after_id, limit)

    def update(self, organization_id: str, project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        return self._db.call("api.project_update", organization_id, project_id, patch)

    def soft_delete(self, organization_id: str, project_id: str) -> None:
        self._db.call("api.project_soft_delete", organization_id, project_id)


class IdempotencyRepository(IIdempotencyRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, organization_id: str, key: str) -> Optional[Dict[str, Any]]:
        return self._db.call("api.idempotency_get", organization_id, key)

    def put(self, organization_id: str, key: str, request_hash: str, response: Dict[str, Any], status: int) -> None:
        self._db.call("api.idempotency_put", organization_id, key, request_hash, response, status)
