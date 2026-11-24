from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status

from ..constants import project
from ..decorators import enforce, http_error_handler
from ..schemas import ProjectCreate, ProjectPage, ProjectResponse, ProjectUpdate
from ..services import ServiceContainer
from .deps import get_services

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@http_error_handler
@enforce(project.create)
def create_project(request: Request, response: Response, body: ProjectCreate,
                   idempotency_key: Optional[str] = Header(None, max_length=200),
                   services: ServiceContainer = Depends(get_services)):
    created, replayed = services.projects.create(request.state.auth, body.model_dump(), idempotency_key)
    if replayed:
        response.headers["Idempotent-Replayed"] = "true"
    return created


@router.get("", response_model=ProjectPage)
@http_error_handler
@enforce(project.read)
def list_projects(request: Request, status_filter: Optional[str] = Query(None, alias="status",
                                                                       pattern="^(active|paused|done)$"),
                  cursor: Optional[str] = Query(None), limit: int = Query(10, ge=1, le=100),
                  services: ServiceContainer = Depends(get_services)):
    return services.projects.list(request.state.auth, status_filter, cursor, limit)


@router.get("/{project_id}", response_model=ProjectResponse)
@http_error_handler
@enforce(project.read)
def get_project(request: Request, project_id: UUID, services: ServiceContainer = Depends(get_services)):
    return services.projects.get(request.state.auth, str(project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
@http_error_handler
@enforce(project.update)
def update_project(request: Request, project_id: UUID, body: ProjectUpdate,
                   services: ServiceContainer = Depends(get_services)):
    return services.projects.update(request.state.auth, str(project_id), body.model_dump(exclude_unset=True))


@router.delete("/{project_id}")
@http_error_handler
@enforce(project.delete)
def delete_project(request: Request, project_id: UUID, services: ServiceContainer = Depends(get_services)):
    services.projects.soft_delete(request.state.auth, str(project_id))
    return {"message": "Deleted successfully"}
