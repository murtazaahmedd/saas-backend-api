from __future__ import annotations

from typing import Optional

from .security import TokenService


class UtilityContainer:
    def __init__(self, jwt_secret: str) -> None:
        self._jwt_secret = jwt_secret
        self._tokens: Optional[TokenService] = None

    @property
    def tokens(self) -> TokenService:
        if self._tokens is None:
            self._tokens = TokenService(self._jwt_secret)
        return self._tokens
