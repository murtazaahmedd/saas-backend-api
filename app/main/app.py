"""Composition root: build every container once and hang the services on the app."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..repositories import Database, RepositoryContainer
from ..routers import auth_router, projects_router, users_router
from ..services import ServiceContainer
from ..utilities import UtilityContainer


def create_app(dsn: str, jwt_secret: str) -> FastAPI:
    db = Database(dsn)
    services = ServiceContainer(UtilityContainer(jwt_secret), RepositoryContainer(db))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        db.close()

    app = FastAPI(title="SaaS Backend API", version="0.1.0", lifespan=lifespan)
    app.state.services = services
    for router in (auth_router, users_router, projects_router):
        app.include_router(router)

    @app.get("/health", tags=["ops"])
    def health():
        return {"status": "ok"}

    return app


def app_from_env() -> FastAPI:
    return create_app(os.environ["DATABASE_URL"], os.environ["JWT_SECRET"])
