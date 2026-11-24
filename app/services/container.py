from __future__ import annotations

from typing import Optional

from ..interfaces import IAuthService, IProjectService, IUserService
from ..repositories import RepositoryContainer
from ..utilities import UtilityContainer
from .auth_service import AuthService
from .project_service import ProjectService
from .user_service import UserService


class ServiceContainer:
    def __init__(self, utilities: UtilityContainer, repositories: RepositoryContainer) -> None:
        self._utils, self._repos = utilities, repositories
        self._auth: Optional[IAuthService] = None
        self._users: Optional[IUserService] = None
        self._projects: Optional[IProjectService] = None

    @property
    def auth(self) -> IAuthService:
        if self._auth is None:
            self._auth = AuthService(self._repos.users, self._repos.auth, self._utils.tokens)
        return self._auth

    @property
    def users(self) -> IUserService:
        if self._users is None:
            self._users = UserService(self._repos.users)
        return self._users

    @property
    def projects(self) -> IProjectService:
        if self._projects is None:
            self._projects = ProjectService(self._repos.projects, self._repos.idempotency)
        return self._projects
