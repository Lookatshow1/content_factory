from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TZ: str = "Europe/Amsterdam"
    RUN_TIMES: str = "09:30,13:30,18:30"

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "svf"

    API_BASE_URL: str = "http://api:8000"

    LLM_PROVIDER_PRIMARY: str = "yandex"
    LLM_PROVIDER_FALLBACK: str = "openrouter"
    LLM_MAX_TOKENS: int = 1200
    LLM_TEMPERATURE: float = 0.6
    LLM_TIMEOUT: int = 60

    YANDEX_BASE_URL: str = "https://llm.api.cloud.yandex.net/v1"
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""
    YANDEX_MODEL: str = "gpt://__FOLDER__/yandexgpt/latest"

    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_HTTP_REFERER: str = ""
    OPENROUTER_X_TITLE: str = ""

    LLM_MODEL_RESEARCHER: str = ""
    LLM_MODEL_WRITER: str = ""
    LLM_MODEL_EDITOR: str = ""
    LLM_MODEL_JUDGE: str = ""
    LLM_MODEL_FALLBACK: str = ""

    REPEAT_SIMILARITY_THRESHOLD: float = 0.55
    SERIES_MODE: str = "round_robin"
    FACT_MODE: str = "bank_only"


settings = Settings()
