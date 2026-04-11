import time
import logging
import psycopg2
import psycopg2.extras
import psycopg2.pool
from app.config import settings

logger = logging.getLogger(__name__)

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        logger.info("Initialising DB connection pool (min=%d, max=%d).",
                    settings.app_db_pool_min, settings.app_db_pool_max)
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=settings.app_db_pool_min,
            maxconn=settings.app_db_pool_max,
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
    return _pool


class DBExecutionError(Exception):
    pass


def execute_query(sql: str) -> tuple[list[dict], float]:
    """
    Execute a validated SQL query using the connection pool.
    Returns (rows_as_dicts, execution_time_seconds).
    """
    pool = get_pool()
    conn = pool.getconn()
    start = time.perf_counter()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = [dict(row) for row in cur.fetchall()]
        conn.rollback()  # read-only — always rollback to keep connection clean
    except psycopg2.Error as e:
        logger.error("DB execution error: %s", e)
        conn.rollback()
        raise DBExecutionError(f"Query execution failed: {e}") from e
    finally:
        pool.putconn(conn)

    elapsed = time.perf_counter() - start
    logger.info("Query executed in %.3fs, returned %d rows.", elapsed, len(rows))
    return rows, elapsed
