# Small dependency module so routers don't import DB internals directly.
from typing import Iterator
from sqlmodel import Session
from fastapi import Depends

from app.db.session import get_session


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency that yields a DB session for each request.
    - Keeps routers clean (they don't know how sessions are created).
    - Makes testing easier (we can override this in tests).
    """
    return next(get_session())  # get_session() is a generator; yield once
