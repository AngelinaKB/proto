import re
import time
import logging
import psycopg2
import psycopg2.extras
import psycopg2.pool
from app.config import settings

logger = logging.getLogger(__name__)

_pools: dict[str, psycopg2.pool.ThreadedConnectionPool] = {}


def _pool_key(conn_kwargs: dict) -> str:
    return f"{conn_kwargs['host']}:{conn_kwargs['port']}/{conn_kwargs['dbname']}"


def _get_pool(conn_kwargs: dict) -> psycopg2.pool.ThreadedConnectionPool:
    key = _pool_key(conn_kwargs)
    if key not in _pools:
        logger.info("Initialising DB pool for %s (min=%d, max=%d).",
                    key, settings.app_db_pool_min, settings.app_db_pool_max)
        _pools[key] = psycopg2.pool.ThreadedConnectionPool(
            minconn=settings.app_db_pool_min,
            maxconn=settings.app_db_pool_max,
            **conn_kwargs,
        )
    return _pools[key]


def _resolve_connection(sql: str) -> dict:
    lower_sql = sql.lower()
    for table, conn_kwargs in settings.db_routing.items():
        if table in lower_sql:
            logger.info("Routing query to DB: %s", _pool_key(conn_kwargs))
            return conn_kwargs
    raise ValueError("Could not resolve a database connection for this query.")


def apply_casts(sql: str) -> str:
    """
    Wrap varchar-stored timestamp columns in CAST(col AS timestamp).
    Works line by line — skips the SELECT list, applies casts in
    WHERE / AND / OR / ORDER BY / HAVING lines only.
    Skips lines that already contain cast() to avoid double-wrapping.
    """
    # Normalize escaped newlines (LLM sometimes returns \\n instead of real newlines)
    sql = sql.replace('\\n', '\n').replace('\\r\\n', '\n').replace('\\r', '\n')

    cast_map = settings.timestamp_cast_columns
    lower_sql = sql.lower()

    for table, cols in cast_map.items():
        if table not in lower_sql:
            continue
        for col in cols:
            lines = sql.split('\n')
            new_lines = []
            in_select = True
            for line in lines:
                upper_line = line.upper().lstrip()
                if upper_line.startswith('FROM'):
                    in_select = False
                if (
                    not in_select
                    and re.search(rf'\b{re.escape(col)}\b', line, re.IGNORECASE)
                    and 'cast(' not in line.lower()
                ):
                    line = re.sub(
                        rf'\b{re.escape(col)}\b',
                        f'CAST({col} AS timestamp)',
                        line,
                        flags=re.IGNORECASE,
                    )
                new_lines.append(line)
            sql = '\n'.join(new_lines)

    return sql


class DBExecutionError(Exception):
    pass


def execute_query(sql: str) -> tuple[list[dict], str, float]:
    """
    1. Resolve which DB pool to use.
    2. Apply varchar → timestamp casts.
    3. Execute and return (rows, final_sql, elapsed_seconds).
    """
    try:
        conn_kwargs = _resolve_connection(sql)
    except ValueError as e:
        raise DBExecutionError(str(e)) from e

    final_sql = apply_casts(sql)
    logger.info("SQL after cast normalisation:\n%s", final_sql)

    pool = _get_pool(conn_kwargs)
    conn = pool.getconn()
    start = time.perf_counter()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(final_sql)
            rows = [dict(row) for row in cur.fetchall()]
        conn.rollback()
    except psycopg2.Error as e:
        logger.error("DB execution error: %s", e)
        conn.rollback()
        raise DBExecutionError(f"Query execution failed: {e}") from e
    finally:
        pool.putconn(conn)

    elapsed = time.perf_counter() - start
    logger.info("Query executed in %.3fs, returned %d rows.", elapsed, len(rows))
    return rows, final_sql, elapsed
