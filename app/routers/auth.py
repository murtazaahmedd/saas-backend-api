from fastapi import APIRouter, Depends, status

from ..decorators import http_error_handler
from ..schemas import LoginRequest, SignupRequest, SignupResponse, TokenResponse
from ..services import ServiceContainer
from .deps import get_services

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
@http_error_handler
def signup(body: SignupRequest, services: ServiceContainer = Depends(get_services)):
    return services.auth.signup(body.organization_name, body.email, body.password)


@router.post("/token", response_model=TokenResponse)
@http_error_handler
def token(body: LoginRequest, services: ServiceContainer = Depends(get_services)):
    return {"access_token": services.auth.login(body.email, body.password)}
