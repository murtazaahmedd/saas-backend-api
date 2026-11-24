from __future__ import annotations

import logging
from typing import Any, Dict

from ..errors import Errors
from ..interfaces import IAuthRepository, IAuthService, IUserRepository
from ..utilities import TokenService, hash_password, verify_password

log = logging.getLogger(__name__)
# verifying against a dummy hash for unknown emails keeps login time constant (no user enumeration by timing)
_DUMMY_HASH = hash_password("timing-equaliser")


class AuthService(IAuthService):
    def __init__(self, users: IUserRepository, auth: IAuthRepository, tokens: TokenService) -> None:
        self._users, self._auth, self._tokens = users, auth, tokens

    def signup(self, org_name: str, email: str, password: str) -> Dict[str, Any]:
        created = self._users.signup(org_name, email, hash_password(password))
        log.info("organization created", extra={"tenant_id": created["organization_id"]})
        token = self._tokens.issue(created["user_id"], created["organization_id"], created["role"])
        return {**created, "access_token": token}

    def login(self, email: str, password: str) -> str:
        creds = self._users.credentials(email)
        if not verify_password(password, creds["password_hash"] if creds else _DUMMY_HASH) or not creds:
            raise Errors.HTTP.Unauthorized("invalid email or password")
        return self._tokens.issue(creds["id"], creds["organization_id"], creds["role"])

    def authorize(self, token: str, permission: str) -> Dict[str, Any]:
        claims = self._tokens.verify(token)
        # role and membership are re-checked in the database on every call: revoking access takes effect at once
        return self._auth.enforce(claims["sub"], claims["org"], permission)
