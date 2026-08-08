"""
SentinelAI Database Setup

SQLAlchemy engine and session factory against Supabase PostgreSQL.
Falls back to SQLite for local development if DATABASE_URL not set.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.core.config import settings


# Determine driver-specific args
connect_args = {}
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://")
elif db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on startup."""
    # Import all models so they register with Base
    import app.models.user  # noqa: F401
    import app.models.portfolio  # noqa: F401
    import app.models.holding  # noqa: F401
    import app.models.event  # noqa: F401
    import app.models.alert  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.agent_state  # noqa: F401
    import app.models.preference  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight schema patches for existing DBs (create_all won't ALTER)
    from sqlalchemy import text, inspect
    try:
        insp = inspect(engine)
        if "alerts" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("alerts")}
            if "ai_summary" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN ai_summary TEXT"))
    except Exception:
        pass
