'use client'

import { useQuery } from '@tanstack/react-query'
import { Settings, CheckCircle, XCircle, ExternalLink, Key, Server, Share2 } from 'lucide-react'
import { api } from '@/lib/api'

const API_DOCS: Record<string, { url: string; description: string }> = {
  anthropic: {
    url: 'https://console.anthropic.com/',
    description: 'Генерация сценариев с Claude',
  },
  elevenlabs: {
    url: 'https://elevenlabs.io/app/settings/api-keys',
    description: 'Синтез голоса',
  },
  heygen: {
    url: 'https://app.heygen.com/settings/api',
    description: 'AI аватары для видео',
  },
  fal: {
    url: 'https://fal.ai/dashboard/keys',
    description: 'Kling AI для генерации видео',
  },
  openai: {
    url: 'https://platform.openai.com/api-keys',
    description: 'Whisper для транскрипции',
  },
  youtube: {
    url: 'https://console.developers.google.com/',
    description: 'YouTube Data API v3',
  },
  tiktok: {
    url: 'https://developers.tiktok.com/',
    description: 'TikTok Content Posting API',
  },
  vk: {
    url: 'https://vk.com/apps?act=manage',
    description: 'VK API для Clips',
  },
  telegram: {
    url: 'https://t.me/BotFather',
    description: 'Telegram Bot API',
  },
  instagram: {
    url: 'https://developers.facebook.com/',
    description: 'Instagram Graph API',
  },
}

export default function SettingsPage() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get('/api/v1/system/status').then(r => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  const aiServices = status?.configuration?.ai_services || {}
  const publishingPlatforms = status?.configuration?.publishing_platforms || {}

  const connectedAI = Object.values(aiServices).filter(Boolean).length
  const totalAI = Object.keys(aiServices).length
  const connectedPublish = Object.values(publishingPlatforms).filter(Boolean).length
  const totalPublish = Object.keys(publishingPlatforms).length

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Settings className="w-8 h-8 mr-3 text-primary-600" />
          Настройки
        </h1>
        <p className="text-gray-600 mt-1">
          Конфигурация API ключей и сервисов
        </p>
      </div>

      {/* Overview */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Server className="w-6 h-6 text-primary-600 mr-3" />
            <h3 className="font-semibold">AI сервисы</h3>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {connectedAI} / {totalAI}
          </div>
          <div className="text-sm text-gray-500">подключено</div>
          <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all"
              style={{ width: `${(connectedAI / totalAI) * 100}%` }}
            />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Share2 className="w-6 h-6 text-green-600 mr-3" />
            <h3 className="font-semibold">Платформы публикации</h3>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {connectedPublish} / {totalPublish}
          </div>
          <div className="text-sm text-gray-500">подключено</div>
          <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-600 rounded-full transition-all"
              style={{ width: `${(connectedPublish / totalPublish) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* AI Services */}
      <div className="card mb-6">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center">
            <Key className="w-5 h-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold">AI сервисы</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            API ключи для генерации контента
          </p>
        </div>
        <div className="divide-y divide-gray-100">
          {Object.entries(aiServices).map(([key, configured]) => (
            <ServiceRow
              key={key}
              name={key}
              configured={configured as boolean}
              info={API_DOCS[key]}
            />
          ))}
        </div>
      </div>

      {/* Publishing Platforms */}
      <div className="card mb-6">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center">
            <Share2 className="w-5 h-5 text-green-600 mr-2" />
            <h2 className="text-lg font-semibold">Платформы публикации</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            API доступ для автопубликации
          </p>
        </div>
        <div className="divide-y divide-gray-100">
          {Object.entries(publishingPlatforms).map(([key, configured]) => (
            <ServiceRow
              key={key}
              name={key}
              configured={configured as boolean}
              info={API_DOCS[key]}
            />
          ))}
        </div>
      </div>

      {/* Configuration Instructions */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4">Как настроить</h2>
        <div className="prose prose-sm text-gray-600">
          <p>
            Для настройки API ключей отредактируйте файл <code className="bg-gray-100 px-2 py-0.5 rounded">.env</code> в корне проекта:
          </p>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm mt-4">
{`# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте файл и добавьте ваши API ключи
nano .env

# Перезапустите сервисы
docker-compose down && docker-compose up -d`}
          </pre>

          <div className="mt-6 space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Обязательные сервисы:</h4>
              <ul className="text-blue-800 space-y-1">
                <li>• <strong>Anthropic</strong> — генерация сценариев с Claude</li>
                <li>• <strong>ElevenLabs</strong> — синтез голоса</li>
                <li>• <strong>HeyGen</strong> — создание AI аватаров</li>
              </ul>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Опциональные сервисы:</h4>
              <ul className="text-gray-700 space-y-1">
                <li>• <strong>FAL.ai</strong> — Kling AI для генерации видео (альтернатива аватарам)</li>
                <li>• <strong>OpenAI</strong> — Whisper для улучшенной транскрипции</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ServiceRow({
  name,
  configured,
  info,
}: {
  name: string
  configured: boolean
  info?: { url: string; description: string }
}) {
  const displayName = name.charAt(0).toUpperCase() + name.slice(1).replace('_', ' ')

  return (
    <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
      <div className="flex items-center">
        {configured ? (
          <CheckCircle className="w-5 h-5 text-green-600 mr-3 flex-shrink-0" />
        ) : (
          <XCircle className="w-5 h-5 text-gray-300 mr-3 flex-shrink-0" />
        )}
        <div>
          <p className="font-medium text-gray-900">{displayName}</p>
          {info?.description && (
            <p className="text-sm text-gray-500">{info.description}</p>
          )}
        </div>
      </div>
      <div className="flex items-center space-x-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          configured
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-500'
        }`}>
          {configured ? 'Подключено' : 'Не настроено'}
        </span>
        {info?.url && (
          <a
            href={info.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-sm flex items-center"
          >
            Получить ключ
            <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        )}
      </div>
    </div>
  )
}
