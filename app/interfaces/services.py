"""Service interfaces used by routers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class IAuthService(ABC):
    @abstractmethod
    def signup(self, org_name: str, email: str, password: str) -> Dict[str, Any]: ...
    @abstractmethod
    def login(self, email: str, password: str) -> str: ...
    @abstractmethod
    def authorize(self, token: str, permission: str) -> Dict[str, Any]: ...


class IUserService(ABC):
    @abstractmethod
    def invite(self, organization_id: str, email: str, password: str, role: str) -> Dict[str, Any]: ...


class IProjectService(ABC):
    @abstractmethod
    def create(self, auth: Dict[str, Any], data: Dict[str, Any], idempotency_key: Optional[str]) -> Tuple[Dict[str, Any], bool]: ...
    @abstractmethod
    def get(self, auth: Dict[str, Any], project_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def list(self, auth: Dict[str, Any], status: Optional[str], cursor: Optional[str], limit: int) -> Dict[str, Any]: ...
    @abstractmethod
    def update(self, auth: Dict[str, Any], project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def soft_delete(self, auth: Dict[str, Any], project_id: str) -> None: ...
