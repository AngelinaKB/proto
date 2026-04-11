from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.0

    # Database 1
    db1_host: str
    db1_port: int = 5432
    db1_name: str
    db1_user: str
    db1_password: str
    db1_tables: str  # comma-separated table names routed to this DB

    # Database 2
    db2_host: str
    db2_port: int = 5432
    db2_name: str
    db2_user: str
    db2_password: str
    db2_tables: str  # comma-separated table names routed to this DB

    # App
    app_max_sql_limit: int = 500
    app_default_sql_limit: int = 100
    app_show_sql: bool = True
    app_max_query_length: int = 1000
    app_allowed_tables: str
    app_table_columns: str
    app_timestamp_cast_columns: str = ""

    # CORS
    app_cors_origins: str = "*"
    app_cors_methods: str = "*"
    app_cors_headers: str = "*"

    # DB connection pool (per database)
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
    def timestamp_cast_columns(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        if not self.app_timestamp_cast_columns:
            return result
        for entry in self.app_timestamp_cast_columns.split("|"):
            entry = entry.strip()
            if not entry or ":" not in entry:
                continue
            table, _, cols_raw = entry.partition(":")
            cols = [c.strip() for c in cols_raw.split(",") if c.strip()]
            result[table.strip().lower()] = cols
        return result

    @property
    def db_routing(self) -> Dict[str, dict]:
        """
        Returns a map of table_name -> DB connection kwargs.
        Used by db_executor to pick the right pool per query.
        """
        routing: Dict[str, dict] = {}
        for db_num, tables_raw, host, port, name, user, password in [
            (1, self.db1_tables, self.db1_host, self.db1_port, self.db1_name, self.db1_user, self.db1_password),
            (2, self.db2_tables, self.db2_host, self.db2_port, self.db2_name, self.db2_user, self.db2_password),
        ]:
            for table in tables_raw.split(","):
                table = table.strip().lower()
                if table:
                    routing[table] = dict(
                        host=host, port=port, dbname=name,
                        user=user, password=password,
                    )
        return routing

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def cors_methods(self) -> List[str]:
        return [m.strip() for m in self.app_cors_methods.split(",") if m.strip()]

    @property
    def cors_headers(self) -> List[str]:
        return [h.strip() for h in self.app_cors_headers.split(",") if h.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
