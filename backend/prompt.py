ALLOWED_TABLES = {
    "GETEMPLOYEES": [
        "EMPLOYEEID", "HIREDATE", "EMPLOYMENTSTATUS", "EMPLOYEECLASS",
        "WORKFROMHOME", "LEGALENTITYCODE", "LEGALENTITYNAME",
        "WORKLOCATIONCODE", "WORKLOCATIONNAME", "COUNTRYCODE",
        "DIVISION", "FUNCTIONALAREACODE", "FUNCTIONALAREANAME",
        "VERTICALCODE", "VERTICALNAME", "PROFITCENTERCODE", "PROFITCENTERNAME",
        "CLIENTCODE", "CLIENTNAME", "COSTCENTERCODE", "COSTCENTERNAME",
        "JOBCODE", "JOBTITLE", "DEPARTMENTCODE",
        "TRAININGSTARTDATE", "TRAININGENDDATE",
        "NESTINGSTARTDATE", "NESTINGENDDATE",
        "HYBRID", "TERMINATIONDATE", "TERMEFFECTIVEDATE",
        "TERMCATEGORY", "TERMREASON",
    ],
    "GETCOSTCENTERS": [
        "COSTCENTERCODE", "COSTCENTERNAME",
        "PROFITCENTERCODE", "PROFITCENTERNAME",
        "VERTICALCODE", "VERTICALNAME",
    ],
    "GETDEPARTMENTS": [
        "DEPARTMENTCODE", "DEPARTMENTNAME",
        "PARENTDEPARTMENTCODE", "PARENTDEPARTMENTNAME",
    ],
    "GETCOUNTRIES": [
        "COUNTRYCODE", "COUNTRYNAME",
        "CURRENCYCODE", "CURRENCYNAME",
    ],
    "GETFUNCTIONALAREAS": [
        "FUNCTIONALAREACODE", "FUNCTIONALAREANAME",
    ],
    "GETPROFITCENTERS": [
        "PROFITCENTERCODE", "PROFITCENTERNAME",
        "CLIENTCODE", "CLIENTNAME",
    ],
    "GETVERTICALS": [
        "VERTICALCODE", "VERTICALNAME",
    ],
    "GETWORKLOCATIONS": [
        "WORKLOCATIONCODE", "WORKLOCATIONNAME",
        "COUNTRYCODE", "COUNTRYNAME",
        "STATECODE", "STATENAME",
    ],
}

BLOCKED_COLUMNS = [
    "FIRSTNAME", "LASTNAME", "EMAIL", "PHONE",
    "ADDRESS", "PERSONALPHONE", "WORKEMAIL", "PERSONALEMAIL",
]


def build_sql_prompt(question: str, max_rows: int) -> str:
    tables_block = "\n".join(
        f"- {table}: {', '.join(cols)}"
        for table, cols in ALLOWED_TABLES.items()
    )

    examples = f"""
Q: How many employees were hired last month?
SQL: SELECT COUNT(EMPLOYEEID) AS hire_count FROM GETEMPLOYEES WHERE HIREDATE >= DATEADD('month', -1, CURRENT_DATE()) LIMIT {max_rows};

Q: How many active employees are in each division?
SQL: SELECT DIVISION, COUNT(EMPLOYEEID) AS headcount FROM GETEMPLOYEES WHERE EMPLOYMENTSTATUS = 'Active' GROUP BY DIVISION ORDER BY headcount DESC LIMIT {max_rows};

Q: Which countries have the most employees?
SQL: SELECT COUNTRYCODE, COUNT(EMPLOYEEID) AS headcount FROM GETEMPLOYEES WHERE EMPLOYMENTSTATUS = 'Active' GROUP BY COUNTRYCODE ORDER BY headcount DESC LIMIT {max_rows};

Q: What are the most common termination reasons this year?
SQL: SELECT TERMREASON, COUNT(EMPLOYEEID) AS count FROM GETEMPLOYEES WHERE TERMEFFECTIVEDATE >= DATE_TRUNC('year', CURRENT_DATE()) GROUP BY TERMREASON ORDER BY count DESC LIMIT {max_rows};
"""

    return f"""You are a SQL generation assistant for a Snowflake data warehouse.
Convert the user's question into a valid Snowflake SQL query.

## STRICT RULES:
1. Only SELECT statements. Never INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
2. Always include LIMIT {max_rows} or less.
3. Never use SELECT *. Always name specific columns.
4. Only use tables and columns from the approved list below.
5. Maximum 3 JOINs per query.
6. No subqueries — use JOINs instead.
7. No CROSS JOINs.
8. No window functions (ROW_NUMBER, RANK, LAG, etc.).
9. Never reference these blocked PII columns: {', '.join(BLOCKED_COLUMNS)}.
10. If the question cannot be answered with available data, respond with:
    CANNOT_GENERATE: <reason>

## APPROVED TABLES AND COLUMNS:
{tables_block}

## EXAMPLE QUERIES:
{examples}

## OUTPUT FORMAT:
Respond with ONLY the SQL query. No explanation, no markdown, no backticks.

## QUESTION:
{question}

SQL:"""
