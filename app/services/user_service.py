from __future__ import annotations

from typing import Any, Dict

from ..interfaces import IUserRepository, IUserService
from ..utilities import hash_password


class UserService(IUserService):
    def __init__(self, users: IUserRepository) -> None:
        self._users = users

    def invite(self, organization_id: str, email: str, password: str, role: str) -> Dict[str, Any]:
        return self._users.create(organization_id, email, hash_password(password), role)
