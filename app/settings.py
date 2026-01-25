from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TZ: str = "Europe/Amsterdam"
    RUN_TIMES: str = "09:30,13:30,18:30"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@postgres:5432/svf"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
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

    GOOGLE_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-1.5-pro-latest"

    LLM_MODEL_RESEARCHER: str = ""
    LLM_MODEL_WRITER: str = ""
    LLM_MODEL_EDITOR: str = ""
    LLM_MODEL_JUDGE: str = ""
    LLM_MODEL_FALLBACK: str = ""

    TTS_PROVIDER: str = "stub"
    TTS_TIMEOUT: int = 60
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
    ELEVENLABS_STABILITY: float = 0.5
    ELEVENLABS_SIMILARITY: float = 0.75

    VIDEO_BACKEND: str = "ffmpeg"
    HEYGEN_API_KEY: str = ""
    HEYGEN_BASE_URL: str = "https://api.heygen.com"
    HEYGEN_POLL_INTERVAL: int = 20
    HEYGEN_MAX_POLLS: int = 10

    REPEAT_SIMILARITY_THRESHOLD: float = 0.55
    SERIES_MODE: str = "round_robin"
    FACT_MODE: str = "bank_only"
    FORCE_RUBRIC_ID: str = ""

    PIPELINE_VERSION: str = "v3"
    PIPELINE_ALLOWED: str = "v1,v2,v3"

    PUBLISH_VK_ENABLED: bool = False
    PUBLISH_TIKTOK_ENABLED: bool = False
    VK_ACCESS_TOKEN: str = ""
    VK_GROUP_ID: str = ""
    VK_API_VERSION: str = "5.131"
    TIKTOK_ACCESS_TOKEN: str = ""
    TIKTOK_APP_ID: str = ""
    TIKTOK_APP_SECRET: str = ""


settings = Settings()
