"""Repository interfaces. Implementations call api.* UDFs only."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class IAuthRepository(ABC):
    @abstractmethod
    def enforce(self, user_id: str, organization_id: str, permission: str) -> Dict[str, Any]: ...


class IUserRepository(ABC):
    @abstractmethod
    def signup(self, org_name: str, email: str, password_hash: str) -> Dict[str, Any]: ...
    @abstractmethod
    def create(self, organization_id: str, email: str, password_hash: str, role: str) -> Dict[str, Any]: ...
    @abstractmethod
    def credentials(self, email: str) -> Optional[Dict[str, Any]]: ...


class IProjectRepository(ABC):
    @abstractmethod
    def create(self, organization_id: str, user_id: str, name: str, description: str) -> Dict[str, Any]: ...
    @abstractmethod
    def get(self, organization_id: str, project_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def list(self, organization_id: str, status: Optional[str], after_created: Optional[datetime],
             after_id: Optional[str], limit: int) -> Dict[str, Any]: ...
    @abstractmethod
    def update(self, organization_id: str, project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def soft_delete(self, organization_id: str, project_id: str) -> None: ...


class IIdempotencyRepository(ABC):
    @abstractmethod
    def get(self, organization_id: str, key: str) -> Optional[Dict[str, Any]]: ...
    @abstractmethod
    def put(self, organization_id: str, key: str, request_hash: str, response: Dict[str, Any], status: int) -> None: ...
