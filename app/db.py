from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
_connect_args = {"check_same_thread": False, "timeout": 30} if _is_sqlite else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)

if _is_sqlite:
    # Rollback-journal SQLite serializes writers behind a single file lock,
    # which surfaces as spurious "readonly database" / "database is locked"
    # errors as soon as more than one process writes concurrently (the live
    # /query endpoint and a batch scripts/run_eval.py run, in particular).
    # WAL mode lets readers and a writer coexist; busy_timeout makes a
    # second writer wait instead of failing immediately.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    # Ensure sqlite parent dir exists before create_all tries to open the file.
    if settings.database_url.startswith("sqlite"):
        settings.eval_dir.mkdir(parents=True, exist_ok=True)
    import app.models  # noqa: F401 register models on Base before create_all

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()
