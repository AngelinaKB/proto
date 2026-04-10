import logging
from app.services.openai_service import chat
from app.prompts.sql_prompt import build_sql_prompt

logger = logging.getLogger(__name__)


class UnsupportedQuestionError(Exception):
    pass


def generate_sql(question: str) -> str:
    """
    Ask the LLM to produce a SQL SELECT statement for the given question.
    Returns the raw SQL string.
    Raises UnsupportedQuestionError if the LLM returns CANNOT_GENERATE.
    """
    prompt = build_sql_prompt(question)

    # Prompt is self-contained — system role carries the full instruction set
    raw = chat(system_prompt=prompt, user_prompt="")
    sql = raw.strip()

    if sql.upper().startswith("CANNOT_GENERATE"):
        # Extract the reason after the colon if present
        reason = sql.split(":", 1)[1].strip() if ":" in sql else "Question cannot be answered from available data."
        logger.info("LLM returned CANNOT_GENERATE: %s", reason)
        raise UnsupportedQuestionError(reason)

    return sql