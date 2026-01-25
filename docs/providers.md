# Providers and ENV

Ниже перечислены переменные окружения для включения провайдеров.

## LLM (OpenAI‑compatible)

### Yandex (primary)

```
LLM_PROVIDER_PRIMARY=yandex
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net/v1
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_MODEL=gpt://<folder_id>/yandexgpt/latest

LLM_MODEL_RESEARCHER=${YANDEX_MODEL}
LLM_MODEL_WRITER=${YANDEX_MODEL}
LLM_MODEL_EDITOR=${YANDEX_MODEL}
LLM_MODEL_JUDGE=${YANDEX_MODEL}
```

### OpenRouter (fallback)

```
LLM_PROVIDER_FALLBACK=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_HTTP_REFERER=https://your-domain
OPENROUTER_X_TITLE=content-factory
LLM_MODEL_FALLBACK=${OPENROUTER_MODEL}
```

## TTS (ElevenLabs)

```
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=  # опционально
ELEVENLABS_MODEL=eleven_multilingual_v2
```

## Видео

### FFmpeg (default)

```
VIDEO_BACKEND=ffmpeg
```

### HeyGen (optional)

```
VIDEO_BACKEND=heygen
HEYGEN_API_KEY=...
HEYGEN_BASE_URL=https://api.heygen.com
```

## Публикация

### VK

```
PUBLISH_VK_ENABLED=true
VK_ACCESS_TOKEN=...
VK_GROUP_ID=...
VK_API_VERSION=5.131
```

### TikTok

```
PUBLISH_TIKTOK_ENABLED=true
TIKTOK_ACCESS_TOKEN=...
```

## Прочее

```
RUN_TIMES=09:30,13:30,18:30
PIPELINE_VERSION=v3
PIPELINE_ALLOWED=v1,v2,v3
```
