from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str
    openai_max_tokens: int
    openai_temperature: float

    # App
    max_rows: int

    class Config:
        env_file = ".env"


settings = Settings()
