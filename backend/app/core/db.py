from psycopg2.pool import SimpleConnectionPool
from app.core.config import get_settings

_pool: SimpleConnectionPool | None = None


def get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.SUPABASE_DATABASE_URL,
        )
    return _pool


def get_db():
    """FastAPI dependency — yields a connection, commits or rolls back on exit."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
