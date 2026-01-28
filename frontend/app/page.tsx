'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Video,
  CheckCircle,
  Clock,
  AlertCircle,
  Zap,
  Play,
} from 'lucide-react'
import { api } from '@/lib/api'
import Link from 'next/link'

export default function Dashboard() {
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get('/api/v1/system/status').then(r => r.data),
    refetchInterval: 10000,
    retry: 1,
  })

  const { data: videos, isLoading: videosLoading } = useQuery({
    queryKey: ['recent-videos'],
    queryFn: () => api.get('/api/v1/videos?per_page=5').then(r => r.data),
    retry: 1,
  })

  const isLoading = statusLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    )
  }

  const videoStats = status?.statistics?.videos || {}
  const apiConfig = status?.configuration?.ai_services || {}
  const publishConfig = status?.configuration?.publishing_platforms || {}

  const totalVideos = Object.values(videoStats).reduce((a: number, b: any) => a + (b || 0), 0)
  const processingCount =
    (videoStats.generating_script || 0) +
    (videoStats.generating_audio || 0) +
    (videoStats.generating_video || 0) +
    (videoStats.rendering || 0) +
    (videoStats.adding_subtitles || 0)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Контент-завод для автоматического создания вертикальных видео
        </p>
      </div>

      {/* Quick Action */}
      <div className="mb-8">
        <Link
          href="/generate"
          className="inline-flex items-center px-6 py-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all hover:scale-[1.02]"
        >
          <Zap className="w-6 h-6 mr-3" />
          <div>
            <div className="font-bold text-lg">Создать видео</div>
            <div className="text-primary-200 text-sm">Запустить генерацию с AI</div>
          </div>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Всего видео"
          value={totalVideos}
          icon={Video}
          color="blue"
        />
        <StatCard
          title="Завершено"
          value={videoStats.completed || 0}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="В процессе"
          value={processingCount}
          icon={Clock}
          color="yellow"
        />
        <StatCard
          title="Ошибки"
          value={videoStats.failed || 0}
          icon={AlertCircle}
          color="red"
        />
      </div>

      {/* API Status & Recent Videos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Status */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Статус API</h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">AI сервисы</h3>
              <div className="space-y-2">
                <ApiStatusRow name="Anthropic (Claude)" connected={apiConfig.anthropic} />
                <ApiStatusRow name="ElevenLabs" connected={apiConfig.elevenlabs} />
                <ApiStatusRow name="HeyGen" connected={apiConfig.heygen} />
                <ApiStatusRow name="OpenAI" connected={apiConfig.openai} />
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Публикация</h3>
              <div className="space-y-2">
                <ApiStatusRow name="YouTube" connected={publishConfig.youtube} />
                <ApiStatusRow name="TikTok" connected={publishConfig.tiktok} />
                <ApiStatusRow name="VK" connected={publishConfig.vk} />
                <ApiStatusRow name="Telegram" connected={publishConfig.telegram} />
                <ApiStatusRow name="Instagram" connected={publishConfig.instagram} />
              </div>
            </div>
          </div>
        </div>

        {/* Recent Videos */}
        <div className="card">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Последние видео</h2>
            <Link href="/videos" className="text-primary-600 hover:underline text-sm">
              Все видео →
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {videosLoading ? (
              <div className="p-8 text-center text-gray-500">Загрузка...</div>
            ) : !videos?.items?.length ? (
              <div className="p-8 text-center">
                <Video className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Нет видео</p>
                <Link href="/generate" className="text-primary-600 hover:underline text-sm mt-2 inline-block">
                  Создать первое видео
                </Link>
              </div>
            ) : (
              videos.items.map((video: any) => (
                <VideoRow key={video.id} video={video} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color }: {
  title: string
  value: number
  icon: any
  color: 'blue' | 'green' | 'yellow' | 'red'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="card p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-xl ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

function ApiStatusRow({ name, connected }: { name: string; connected: boolean }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-gray-700">{name}</span>
      <span className={`flex items-center text-sm ${connected ? 'text-green-600' : 'text-gray-400'}`}>
        <div className={`w-2 h-2 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-gray-300'}`} />
        {connected ? 'Подключено' : 'Не настроено'}
      </span>
    </div>
  )
}

function VideoRow({ video }: { video: any }) {
  const statusColors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    generating_script: 'bg-blue-100 text-blue-600',
    generating_audio: 'bg-blue-100 text-blue-600',
    generating_video: 'bg-purple-100 text-purple-600',
    adding_subtitles: 'bg-indigo-100 text-indigo-600',
    rendering: 'bg-yellow-100 text-yellow-600',
    completed: 'bg-green-100 text-green-600',
    failed: 'bg-red-100 text-red-600',
  }

  const statusLabels: Record<string, string> = {
    pending: 'В очереди',
    generating_script: 'Генерация скрипта',
    generating_audio: 'Генерация аудио',
    generating_video: 'Генерация видео',
    adding_subtitles: 'Добавление субтитров',
    rendering: 'Рендеринг',
    completed: 'Готово',
    failed: 'Ошибка',
  }

  return (
    <div className="p-4 flex items-center justify-between hover:bg-gray-50">
      <div className="flex items-center min-w-0">
        <div className="w-12 h-20 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
          {video.thumbnail_path ? (
            <img
              src={`/api/v1/media/${video.thumbnail_path}`}
              alt=""
              className="w-full h-full object-cover rounded-lg"
            />
          ) : (
            <Play className="w-5 h-5 text-gray-400" />
          )}
        </div>
        <div className="ml-4 min-w-0">
          <p className="font-medium text-gray-900 truncate">{video.title}</p>
          <p className="text-sm text-gray-500 truncate">{video.topic || 'Без темы'}</p>
        </div>
      </div>
      <span className={`px-3 py-1 rounded-full text-xs font-medium flex-shrink-0 ml-4 ${statusColors[video.status] || statusColors.pending}`}>
        {statusLabels[video.status] || video.status}
      </span>
    </div>
  )
}
