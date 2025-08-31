from typing import Any, Dict, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Normalize HTTP errors into a deterministic shape:
      { "detail": "<message>" }
    """
    detail = exc.detail if isinstance(exc.detail, str) else "Error"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Wrap FastAPI/Pydantic 422 into:
      {
        "detail": "Validation error",
        "errors": [ { "loc": [...], "msg": "...", "type": "..." }, ... ]
      }
    """
    errors: List[Dict[str, Any]] = []
    for e in exc.errors():
        errors.append(
            {
                "loc": list(e.get("loc", [])),
                "msg": e.get("msg", ""),
                "type": e.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
    """
    Convert DB integrity issues (e.g., unique constraint) into 409 Conflict.
    Routers already catch many cases explicitly, but this is a safety net.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Conflict: integrity constraint violated"},
    )


def add_exception_handlers(app) -> None:
    """
    Register all handlers at app startup.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
