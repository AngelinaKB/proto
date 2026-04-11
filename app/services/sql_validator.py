import re
from app.config import settings

# Keywords that must never appear in a safe SELECT query
BLOCKED_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
]


class SQLValidationError(Exception):
    pass


def validate_sql(sql: str) -> None:
    """
    Validate a generated SQL string against all safety and business rules.
    Raises SQLValidationError with a descriptive message on any violation.
    """
    upper = sql.upper()

    # 1. Must start with SELECT
    if not upper.lstrip().startswith("SELECT"):
        raise SQLValidationError("Only SELECT statements are allowed.")

    # 2. No dangerous keywords
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, upper):
            keyword = pattern.replace(r"\b", "")
            raise SQLValidationError(f"Forbidden keyword detected: {keyword}")

    # 3. No multiple statements (semicolons mid-query)
    # Strip a trailing semicolon, then check for any remaining ones
    cleaned = sql.rstrip().rstrip(";")
    if ";" in cleaned:
        raise SQLValidationError("Multiple statements are not allowed.")

    # 4. Only allowed tables
    lower_sql = sql.lower()
    found_tables = [t for t in settings.allowed_tables if t in lower_sql]
    if not found_tables:
        raise SQLValidationError(
            "Query does not reference any allowed tables."
        )

    # 5. No cross-table joins (only one table may appear per query)
    if len(found_tables) > 1:
        raise SQLValidationError(
            "Queries spanning multiple tables are not allowed."
        )

    # 6. LIMIT must be present
    if not re.search(r"\bLIMIT\b", upper):
        raise SQLValidationError("Query must include a LIMIT clause.")

    # 7. LIMIT must not exceed max
    limit_match = re.search(r"\bLIMIT\s+(\d+)", upper)
    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > settings.app_max_sql_limit:
            raise SQLValidationError(
                f"LIMIT {limit_value} exceeds the maximum allowed value of {settings.app_max_sql_limit}."
            )
