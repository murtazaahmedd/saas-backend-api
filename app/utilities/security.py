"""Password hashing (scrypt) and JWT access tokens. Pure helpers, no I/O."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Any, Dict

import jwt

from ..errors import Errors

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_b64, digest_b64 = stored.split("$")
        digest = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=_N, r=_R, p=_P)
        return hmac.compare_digest(digest, base64.b64decode(digest_b64))
    except (ValueError, TypeError):
        return False


class TokenService:
    def __init__(self, secret: str, ttl_seconds: int = 3600) -> None:
        if not secret or len(secret) < 32:
            raise ValueError("[TokenService] JWT secret must be at least 32 characters. Fix: set JWT_SECRET.")
        self._secret, self._ttl = secret, ttl_seconds

    def issue(self, user_id: str, organization_id: str, role: str) -> str:
        now = int(time.time())
        claims = {"sub": user_id, "org": organization_id, "role": role, "iat": now, "exp": now + self._ttl}
        return jwt.encode(claims, self._secret, algorithm="HS256")

    def verify(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self._secret, algorithms=["HS256"], options={"require": ["sub", "org", "exp"]})
        except jwt.ExpiredSignatureError:
            raise Errors.HTTP.Unauthorized("access token expired; log in again")
        except jwt.InvalidTokenError:
            raise Errors.HTTP.Unauthorized("invalid access token")
