import openai
from backend.config import settings
from backend.prompt import build_sql_prompt


client = openai.OpenAI(api_key=settings.openai_api_key)


class LLMError(Exception):
    pass


def generate_sql(question: str) -> str:
    """
    Send the question to GPT and return the generated SQL string.
    Raises LLMError if the call fails or GPT cannot generate a valid query.
    """
    prompt = build_sql_prompt(question, max_rows=settings.max_rows)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
    except openai.OpenAIError as e:
        raise LLMError(f"OpenAI API error: {e}") from e

    raw = response.choices[0].message.content.strip()

    if raw.upper().startswith("CANNOT_GENERATE"):
        reason = raw.split(":", 1)[-1].strip()
        raise LLMError(f"Could not generate SQL: {reason}")

    return raw
