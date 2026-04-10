from openai import OpenAI
from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)


def chat(system_prompt: str, user_prompt: str = "") -> str:
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    response = _client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
        messages=messages,
    )
    return response.choices[0].message.content.strip()