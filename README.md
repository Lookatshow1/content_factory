# content_factory

Автономный контент‑завод для вертикальных роликов 9:16. Пайплайн запускается по расписанию и проходит стадии:

`idea -> research -> script -> storyboard -> tts -> captions -> render_final -> publish_outbox`.

## Быстрый старт

```bash
cp .env.example .env
# заполните ключи и настройки
make up
make migrate
make seed
```

Проверка health:

```bash
curl http://127.0.0.1:8000/health
```

## Как проверить

### Smoke‑прогон

```bash
make smoke
```

Скрипт создаст job, дождётся статуса `done`, скачает `ClipFinal` из MinIO и проверит ffprobe (h264 + aac, 1080x1920).

### Ручные curl

```bash
curl "http://127.0.0.1:8000/jobs?limit=5"
curl "http://127.0.0.1:8000/jobs/<job_id>"
curl "http://127.0.0.1:8000/artifacts/<artifact_id>/download"
curl "http://127.0.0.1:8000/publish/jobs?limit=10"
```

### Метрики и здоровье

```bash
curl "http://127.0.0.1:8000/admin/health"
curl "http://127.0.0.1:8000/admin/metrics"
```

## Архитектура

- **API** (FastAPI) — health, jobs, artifacts, publish.
- **Worker** (Celery) — шаги пайплайна и публикация.
- **Scheduler** (APScheduler) — запускает jobs 3 раза в день по `RUN_TIMES`.
- **Postgres** — данные, артефакты, outbox.
- **MinIO** — хранение медиа (mp4, аудио, субтитры).
- **Redis** — брокер и backend Celery.

## Провайдеры

Полный список переменных в `docs/providers.md`.

### LLM

Используется OpenAI‑совместимый клиент с primary/fallback.

- **Yandex** (primary): `YANDEX_BASE_URL`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`, `YANDEX_MODEL`.
- **OpenRouter** (fallback): `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`.

### TTS

- **ElevenLabs**: `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (опционально).

### Видео

- **FFmpeg** (по умолчанию): локальный рендер.
- **HeyGen** (опционально): `VIDEO_BACKEND=heygen`, `HEYGEN_API_KEY`.

### Публикация

- VK: `PUBLISH_VK_ENABLED=true`, `VK_ACCESS_TOKEN`, `VK_GROUP_ID`.
- TikTok: `PUBLISH_TIKTOK_ENABLED=true`, `TIKTOK_ACCESS_TOKEN`.

## Тесты

```bash
make test
```

E2E (ручной):

```bash
make test_e2e
```

## Логи

```bash
make logs
```

## Примечания

- Секреты держим только в `.env` или секретах окружения. В git не коммитим.
- Для полноценной генерации нужны реальные ключи LLM/TTS.
- Старый пайплайн поддержан: `PIPELINE_VERSION=v1|v2|v3`.
