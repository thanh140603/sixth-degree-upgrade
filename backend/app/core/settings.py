from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "sixth-degree-py"
    environment: str = "local"
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8080
    cors_allow_origins: str = "*"

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    celery_broker_url: str
    celery_result_backend: str

    wiki_user_agent: str = "SixthDegreePyBot/1.0 (Educational Project)"
    wiki_max_workers: int = 10
    wiki_max_retries: int = 3

    wiki_sync_cron_minute: str = "0"
    wiki_sync_cron_hour: str = "3"

    seed_file_path: str = "/app/seed_names.txt"
    graph_json_path: str = "/app/app/graph.json"


settings = Settings()

