"""Error taxonomy. Services and repositories raise these; @http_error_handler turns them into responses."""


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class _HTTP:
    class BadRequest(AppError):
        status_code, code = 400, "bad_request"

    class Unauthorized(AppError):
        status_code, code = 401, "unauthorized"

    class Forbidden(AppError):
        status_code, code = 403, "forbidden"

    class NotFound(AppError):
        status_code, code = 404, "not_found"

    class Conflict(AppError):
        status_code, code = 409, "conflict"

    class TooManyRequests(AppError):
        status_code, code = 429, "rate_limited"

    class InternalServerError(AppError):
        status_code, code = 500, "internal_error"


class Errors:
    HTTP = _HTTP


# SQLSTATE codes raised by api.* functions -> error classes
SQLSTATE_ERRORS = {
    "P0401": Errors.HTTP.Unauthorized,
    "P0403": Errors.HTTP.Forbidden,
    "P0404": Errors.HTTP.NotFound,
    "P0409": Errors.HTTP.Conflict,
    "P0429": Errors.HTTP.TooManyRequests,
    "23514": Errors.HTTP.BadRequest,     # check_violation
}
