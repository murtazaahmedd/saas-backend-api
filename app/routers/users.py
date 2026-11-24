from fastapi import APIRouter, Depends, Request, status

from ..constants import user
from ..decorators import enforce, http_error_handler
from ..schemas import InviteUserRequest, UserResponse
from ..services import ServiceContainer
from .deps import get_services

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@http_error_handler
@enforce(user.create)
def invite_user(request: Request, body: InviteUserRequest, services: ServiceContainer = Depends(get_services)):
    org = request.state.auth["organization_id"]
    return services.users.invite(org, body.email, body.password, body.role)


@router.get("/me")
@http_error_handler
@enforce(user.read)
def me(request: Request):
    return request.state.auth
