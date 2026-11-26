import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("lms.error")


class AppException(Exception):
    """Application exception that renders as {"detail": ..., "code": ...}."""

    def __init__(self, status_code: int, detail: str, code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "code": f"HTTP_{exc.status_code}"},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first_msg = errors[0].get("msg", "Validation error") if errors else "Validation error"
        return JSONResponse(
            status_code=422,
            content={"detail": first_msg, "code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later.", "code": "RATE_LIMITED"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "code": "INTERNAL_ERROR"},
        )
