import logging
from fastapi import APIRouter
from app.schemas import AskRequest, AskResponse
from app.config import settings
from app.services.input_preprocessor import preprocess, InputValidationError
from app.services.sql_generator import generate_sql, UnsupportedQuestionError
from app.services.sql_validator import validate_sql, SQLValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:

    # ── Step 1: Preprocess input ───────────────────────────────────────────────
    try:
        question = preprocess(request.question)
    except InputValidationError as e:
        return AskResponse(status="error", error=str(e))

    logger.info("Question received: %s", question)

    # ── Step 2: Generate SQL ───────────────────────────────────────────────────
    try:
        sql = generate_sql(question)
    except UnsupportedQuestionError as e:
        return AskResponse(status="error", error=str(e))
    except Exception:
        logger.exception("SQL generation failed.")
        return AskResponse(status="error", error="SQL generation failed. Check logs.")

    logger.info("Generated SQL: %s", sql)

    # ── Step 3: Validate SQL ───────────────────────────────────────────────────
    try:
        validate_sql(sql)
    except SQLValidationError as e:
        logger.warning("SQL validation failed: %s | SQL: %s", e, sql)
        return AskResponse(status="error", error=f"SQL failed validation: {e}")

    logger.info("SQL passed validation.")

    # Phase 2 response — SQL generated and validated, not yet executed
    return AskResponse(
        status="success",
        sql=sql if settings.app_show_sql else None,
    )
