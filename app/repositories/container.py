from __future__ import annotations

from typing import Optional

from ..interfaces import IAuthRepository, IIdempotencyRepository, IProjectRepository, IUserRepository
from .database import Database
from .repositories import AuthRepository, IdempotencyRepository, ProjectRepository, UserRepository


class RepositoryContainer:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._auth: Optional[IAuthRepository] = None
        self._users: Optional[IUserRepository] = None
        self._projects: Optional[IProjectRepository] = None
        self._idempotency: Optional[IIdempotencyRepository] = None

    @property
    def auth(self) -> IAuthRepository:
        if self._auth is None:
            self._auth = AuthRepository(self._db)
        return self._auth

    @property
    def users(self) -> IUserRepository:
        if self._users is None:
            self._users = UserRepository(self._db)
        return self._users

    @property
    def projects(self) -> IProjectRepository:
        if self._projects is None:
            self._projects = ProjectRepository(self._db)
        return self._projects

    @property
    def idempotency(self) -> IIdempotencyRepository:
        if self._idempotency is None:
            self._idempotency = IdempotencyRepository(self._db)
        return self._idempotency
