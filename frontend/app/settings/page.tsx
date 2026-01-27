'use client'

import { useQuery } from '@tanstack/react-query'
import { Settings, CheckCircle, XCircle, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'

const API_DOCS = {
  anthropic: 'https://console.anthropic.com/',
  elevenlabs: 'https://elevenlabs.io/app/settings/api-keys',
  heygen: 'https://app.heygen.com/settings/api',
  fal: 'https://fal.ai/dashboard/keys',
  openai: 'https://platform.openai.com/api-keys',
  youtube: 'https://console.developers.google.com/',
  tiktok: 'https://developers.tiktok.com/',
  vk: 'https://vk.com/apps?act=manage',
  telegram: 'https://t.me/BotFather',
  instagram: 'https://developers.facebook.com/',
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

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Configure API keys and system settings
        </p>
      </div>

      {/* AI Services */}
      <div className="card mb-6">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">AI Services</h2>
          <p className="text-sm text-gray-500 mt-1">
            Configure API keys for content generation
          </p>
        </div>
        <div className="divide-y divide-gray-200">
          {Object.entries(aiServices).map(([key, configured]) => (
            <ServiceRow
              key={key}
              name={key}
              configured={configured as boolean}
              docsUrl={API_DOCS[key as keyof typeof API_DOCS]}
            />
          ))}
        </div>
      </div>

      {/* Publishing Platforms */}
      <div className="card mb-6">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Publishing Platforms</h2>
          <p className="text-sm text-gray-500 mt-1">
            Configure API access for auto-publishing
          </p>
        </div>
        <div className="divide-y divide-gray-200">
          {Object.entries(publishingPlatforms).map(([key, configured]) => (
            <ServiceRow
              key={key}
              name={key}
              configured={configured as boolean}
              docsUrl={API_DOCS[key as keyof typeof API_DOCS]}
            />
          ))}
        </div>
      </div>

      {/* Configuration Instructions */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <div className="prose prose-sm text-gray-600">
          <p>
            To configure API keys, edit the <code>.env</code> file in the project root:
          </p>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
{`# Copy from .env.example
cp .env.example .env

# Edit the file and add your API keys
nano .env

# Then restart the services
docker-compose down && docker-compose up -d`}
          </pre>
          <p className="mt-4">
            Required API keys for basic functionality:
          </p>
          <ul>
            <li><strong>Anthropic</strong> - Script generation with Claude</li>
            <li><strong>ElevenLabs</strong> - Voice synthesis</li>
            <li><strong>HeyGen</strong> - Avatar video generation</li>
          </ul>
          <p>
            Optional services:
          </p>
          <ul>
            <li><strong>FAL.ai</strong> - Kling AI video generation (alternative to avatars)</li>
            <li><strong>OpenAI</strong> - Whisper for transcription</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function ServiceRow({
  name,
  configured,
  docsUrl,
}: {
  name: string
  configured: boolean
  docsUrl?: string
}) {
  return (
    <div className="px-6 py-4 flex items-center justify-between">
      <div className="flex items-center">
        {configured ? (
          <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
        ) : (
          <XCircle className="w-5 h-5 text-gray-400 mr-3" />
        )}
        <div>
          <p className="font-medium capitalize">{name.replace('_', ' ')}</p>
          <p className="text-sm text-gray-500">
            {configured ? 'Connected' : 'Not configured'}
          </p>
        </div>
      </div>
      {docsUrl && (
        <a
          href={docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-600 hover:underline text-sm flex items-center"
        >
          Get API Key
          <ExternalLink className="w-4 h-4 ml-1" />
        </a>
      )}
    </div>
  )
}
