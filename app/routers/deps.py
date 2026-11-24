from fastapi import Request

from ..services import ServiceContainer


def get_services(request: Request) -> ServiceContainer:
    return request.app.state.services
