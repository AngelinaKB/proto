import re
from app.config import settings

class InputValidationError(Exception):
    pass

def preprocess(question: str) -> str:
    question = question.strip()
    if not question:
        raise InputValidationError("Question cannot be empty.")
    question = re.sub(r" +", " ", question)
    if len(question) > settings.app_max_query_length:
        raise InputValidationError(
            f"Question exceeds maximum length of {settings.app_max_query_length} characters."
        )
    return question
