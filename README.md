# Content Factory

Полностью автоматизированный конвейер для создания вертикальных видео с AI.

## Возможности

- **AI-генерация сценариев** — Claude создает вирусные скрипты
- **Синтез голоса** — ElevenLabs с поддержкой 32+ языков
- **AI-аватары** — HeyGen для talking head видео
- **AI-видео** — Kling AI через FAL.ai для креативного контента
- **Автосубтитры** — Whisper + FFmpeg в стиле TikTok
- **Автопостинг** — YouTube Shorts, TikTok, Reels, VK Clips, Telegram
- **Планировщик** — 5 видео в неделю на полном автомате
- **Веб-интерфейс** — современный дашборд для управления

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repo>
cd content_factory

# Первоначальная настройка
./scripts/setup.sh
```

### 2. Добавьте API ключи

Откройте `.env` и добавьте ваши ключи:

```env
# Обязательные
ANTHROPIC_API_KEY=sk-ant-api03-...
ELEVENLABS_API_KEY=...
HEYGEN_API_KEY=...

# Опциональные
FAL_API_KEY=...
OPENAI_API_KEY=sk-...

# Публикация (добавьте нужные платформы)
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
TIKTOK_CLIENT_KEY=...
VK_ACCESS_TOKEN=...
TELEGRAM_BOT_TOKEN=...
```

### 3. Запуск

```bash
./scripts/start.sh
```

Откройте http://localhost:3000

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Interface                          │
│                    (Next.js + React)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│                   (REST API + WebSocket)                     │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │      Redis      │ │  Celery Worker  │
│   (Data Store)  │ │    (Queue)      │ │   (Tasks)       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │          AI Services Pipeline          │
          ├───────────────────────────────────────┤
          │  1. Claude → Script Generation        │
          │  2. ElevenLabs → Voice Synthesis      │
          │  3. HeyGen/Kling → Video Generation   │
          │  4. FFmpeg → Subtitles + Render       │
          └───────────────────────────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │           Auto-Publishing              │
          ├───────────────────────────────────────┤
          │  YouTube │ TikTok │ VK │ TG │ IG     │
          └───────────────────────────────────────┘
```

## Пайплайн генерации видео

1. **Генерация сценария** — Claude создает вирусный скрипт с хуком
2. **Озвучка** — ElevenLabs синтезирует естественную речь
3. **Видео** — HeyGen создает аватар или Kling генерирует AI-видео
4. **Субтитры** — Whisper транскрибирует, FFmpeg рендерит
5. **Публикация** — Автоматически на все платформы

## API Endpoints

| Endpoint | Описание |
|----------|----------|
| `POST /api/v1/videos/generate` | Запустить генерацию видео |
| `GET /api/v1/videos` | Список всех видео |
| `POST /api/v1/content-plans` | Создать контент-план |
| `POST /api/v1/publishing/publish` | Опубликовать видео |
| `GET /api/v1/system/status` | Статус системы |

Полная документация: http://localhost:8000/docs

## Получение API ключей

### Anthropic (Claude)
1. Зайдите на https://console.anthropic.com/
2. Создайте API ключ

### ElevenLabs
1. Зайдите на https://elevenlabs.io/
2. Перейдите в Settings → API Keys

### HeyGen
1. Зайдите на https://app.heygen.com/
2. Перейдите в Settings → API

### FAL.ai (Kling)
1. Зайдите на https://fal.ai/
2. Dashboard → Keys

### YouTube
1. Google Cloud Console → APIs → YouTube Data API v3
2. Создайте OAuth 2.0 credentials

### TikTok
1. TikTok for Developers → Create App
2. Add Content Posting API

### VK
1. https://vk.com/apps?act=manage
2. Создайте Standalone-приложение

### Telegram
1. Напишите @BotFather
2. /newbot → получите токен

## Команды Docker

```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка
docker-compose build --no-cache
```

## Структура проекта

```
content_factory/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, DB
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   ├── ai/          # AI integrations
│   │   │   ├── video/       # Video processing
│   │   │   └── publishers/  # Platform publishers
│   │   └── workers/         # Celery tasks
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   └── lib/                 # Utilities
├── docker-compose.yml
├── .env.example
└── scripts/
    ├── setup.sh
    └── start.sh
```

## Troubleshooting

### Видео не генерируется
- Проверьте API ключи в Settings
- Посмотрите логи: `docker-compose logs celery_worker`

### Не публикуется
- Проверьте токены платформ
- Убедитесь что видео завершено (статус: completed)

### Медленная генерация
- HeyGen может занимать 5-10 минут
- Kling через FAL.ai — 2-5 минут

## Лицензия

MIT
