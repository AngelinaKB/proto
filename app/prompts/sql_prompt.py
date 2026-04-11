"""
Builds the SQL generation prompt.
All table names, column schema, and cast rules are injected at runtime from
settings — nothing is hardcoded here.
"""

from app.config import settings


def _build_tables_block() -> str:
    col_map = settings.column_map
    lines = []
    for table in settings.allowed_tables:
        cols = col_map.get(table)
        if cols:
            lines.append(f"- {table}: {', '.join(cols)}")
        else:
            lines.append(f"- {table}: (no columns configured)")
    return "\n".join(lines)


def _build_cast_rules() -> str:
    """
    Builds a section listing which columns must be cast to timestamp.
    Returns empty string if no cast columns are configured.
    """
    cast_map = settings.timestamp_cast_columns
    if not cast_map:
        return ""

    lines = ["## COLUMN TYPE CASTING", ""]
    lines.append("The following columns are stored as varchar and MUST be cast to")
    lines.append("timestamp before any date/time comparison or ordering:")
    lines.append("")
    for table, cols in cast_map.items():
        for col in cols:
            lines.append(f"- {table}.{col} → use CAST({col} AS timestamp)")
    lines.append("")
    lines.append("ALWAYS wrap these columns in CAST(col AS timestamp) when used in:")
    lines.append("WHERE clauses, ORDER BY, DATE_TRUNC(), or any time comparison.")
    lines.append("")
    return "\n".join(lines)


def _build_examples() -> str:
    default = settings.app_default_sql_limit
    cast_map = settings.timestamp_cast_columns

    log_table = next(
        (t for t in settings.allowed_tables if "customreportlog" in t), ""
    )
    svc_table = next(
        (t for t in settings.allowed_tables if "flowserviceinformation" in t), ""
    )

    # Determine which columns need casting for each table
    log_casts = set(cast_map.get(log_table, []))
    svc_casts = set(cast_map.get(svc_table, []))

    def col(table_casts: set, name: str) -> str:
        """Wrap column in CAST if it needs it."""
        return f"CAST({name} AS timestamp)" if name in table_casts else name

    log_logtime = col(log_casts, "logtime")
    svc_lastrunutc = col(svc_casts, "lastrunutc")

    return f"""
Q: What failed last night?
SQL: SELECT reportname, stepname, logtime, error, status, jobid
FROM {log_table}
WHERE status ILIKE 'fail%'
  AND {log_logtime} >= NOW() - INTERVAL '1 day'
ORDER BY {log_logtime} DESC
LIMIT {default};

Q: Which services haven't run in the last 7 days?
SQL: SELECT servicename, status, lastrunutc, servername, packagename
FROM {svc_table}
WHERE {svc_lastrunutc} IS NULL
  OR {svc_lastrunutc} < NOW() - INTERVAL '7 days'
ORDER BY {svc_lastrunutc} NULLS FIRST
LIMIT {default};

Q: What are the most common errors this week?
SQL: SELECT error, COUNT(*) AS error_count
FROM {log_table}
WHERE {log_logtime} >= DATE_TRUNC('week', NOW())
  AND error IS NOT NULL
  AND TRIM(error) <> ''
GROUP BY error
ORDER BY error_count DESC
LIMIT {default};

Q: Which services use schema X?
SQL: SELECT servicename, schemaname, tablename, procedurename
FROM {svc_table}
WHERE schemaname ILIKE 'X'
ORDER BY servicename
LIMIT {default};

Q: Show SQL for service Y.
SQL: SELECT servicename, sqlquery, dynamicquery
FROM {svc_table}
WHERE servicename ILIKE 'Y'
LIMIT {default};

Q: Which jobs are running right now?
SQL: SELECT reportname, stepname, logtime, status, jobid
FROM {log_table}
WHERE status ILIKE 'running%'
ORDER BY {log_logtime} DESC
LIMIT {default};

Q: Compare failures this week versus last week by report.
SQL: SELECT reportname,
       COUNT(*) FILTER (
         WHERE {log_logtime} >= DATE_TRUNC('week', NOW())
           AND status ILIKE 'fail%'
       ) AS failures_this_week,
       COUNT(*) FILTER (
         WHERE {log_logtime} >= DATE_TRUNC('week', NOW()) - INTERVAL '7 days'
           AND {log_logtime} < DATE_TRUNC('week', NOW())
           AND status ILIKE 'fail%'
       ) AS failures_last_week
FROM {log_table}
GROUP BY reportname
ORDER BY reportname
LIMIT {default};

Q: Who was hired last month?
SQL: CANNOT_GENERATE: The question is outside the supported data scope.

Q: Delete failed jobs from last night.
SQL: CANNOT_GENERATE: Only read-only SELECT queries are supported.

Q: Which services appear related to failed reports last night?
SQL: CANNOT_GENERATE: The two tables are independent and cannot be joined.

Q: Show me everything.
SQL: CANNOT_GENERATE: The request is too broad or ambiguous. Ask a more specific question.
"""


def build_sql_prompt(question: str) -> str:
    tables_block = _build_tables_block()
    cast_rules = _build_cast_rules()
    examples = _build_examples()
    default = settings.app_default_sql_limit
    max_limit = settings.app_max_sql_limit

    return f"""You are a SQL generation assistant for an internal tool called Data Flow Insight.

Your job is to convert a user's plain-English question into a valid PostgreSQL SELECT query.

The system supports questions only about:
- service configuration metadata
- report execution logs

## STRICT RULES

1. Only generate a single SELECT statement.
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or EXEC statements.
3. Only query the approved tables listed below.
4. Use only the columns listed below.
5. Always include a LIMIT clause.
6. Use LIMIT {default} unless the user asks for fewer rows.
7. Never exceed LIMIT {max_limit}.
8. Prefer explicit column names.
9. Use SELECT * only for narrow technical lookups.
10. Use PostgreSQL syntax only.
11. Return ONLY the SQL query or a CANNOT_GENERATE response. No explanation, no markdown, no backticks.
12. If the question cannot be answered, respond exactly as:
CANNOT_GENERATE: <reason>

## TABLE RELATIONSHIP RULE

The two tables are independent and must NOT be joined.
If a question requires combining both tables, respond:
CANNOT_GENERATE: The two tables are independent and cannot be joined.

## WHEN TO RETURN CANNOT_GENERATE

Return CANNOT_GENERATE instead of SQL if any of the following are true:
- the question cannot be answered from the listed tables and columns
- the question is outside the supported data scope
- the user asks for HR, finance, employee, revenue, weather, email, or unrelated business data
- the user asks to write, delete, update, modify, execute, or change data
- the request is too broad, vague, or ambiguous
- answering would require inventing a table, column, or relationship
- answering would require joining the two tables

Do NOT return CANNOT_GENERATE for valid analytical questions that can be answered from a single allowed table.
Valid single-table analytical questions include: counts, grouped summaries, top N results,
time-based comparisons, trends, error frequency analysis, service metadata lookups.

## APPROVED TABLES AND COLUMNS

{tables_block}

{cast_rules}
## QUERY GUIDELINES

- Use ILIKE for case-insensitive string matching
- Time filters: last day → NOW() - INTERVAL '1 day' | last 7 days → NOW() - INTERVAL '7 days' | this week → DATE_TRUNC('week', NOW())
- Order results when useful: recent → ORDER BY timestamp DESC | counts → ORDER BY count DESC
- Preserve raw source values. Do not normalize or reinterpret business meaning.

## SPECIAL HANDLING

- "everything" / "all data" / overly broad → CANNOT_GENERATE
- unsupported write actions → CANNOT_GENERATE
- cross-table questions → CANNOT_GENERATE
- typos where intent is still clear and answerable → generate SQL

## EXAMPLES
{examples}

## QUESTION
{question}

SQL:"""
