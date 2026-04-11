from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.0

    # Postgres
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # App
    app_max_sql_limit: int = 500
    app_default_sql_limit: int = 100
    app_show_sql: bool = True
    app_max_query_length: int = 1000
    app_allowed_tables: str
    app_table_columns: str

    # CORS
    app_cors_origins: str = "*"
    app_cors_methods: str = "*"
    app_cors_headers: str = "*"

    # DB connection pool
    app_db_pool_min: int = 1
    app_db_pool_max: int = 10

    @property
    def allowed_tables(self) -> List[str]:
        return [t.strip().lower() for t in self.app_allowed_tables.split(",") if t.strip()]

    @property
    def column_map(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for entry in self.app_table_columns.split("|"):
            entry = entry.strip()
            if not entry or ":" not in entry:
                continue
            table, _, cols_raw = entry.partition(":")
            cols = [c.strip() for c in cols_raw.split(",") if c.strip()]
            result[table.strip().lower()] = cols
        return result

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def cors_methods(self) -> List[str]:
        return [m.strip() for m in self.app_cors_methods.split(",") if m.strip()]

    @property
    def cors_headers(self) -> List[str]:
        return [h.strip() for h in self.app_cors_headers.split(",") if h.strip()]

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
