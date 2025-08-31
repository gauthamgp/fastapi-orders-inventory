from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# SQLite-specific connect args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Engine creation
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    connect_args=connect_args,
)

def get_session():
    """Dependency: yield a session per request."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Create tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)
