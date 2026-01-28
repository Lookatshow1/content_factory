'use client'

import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Eye, ThumbsUp, MessageCircle, Share2, Video } from 'lucide-react'
import { api } from '@/lib/api'

const PLATFORM_CONFIG: Record<string, { icon: string; name: string; color: string }> = {
  youtube: { icon: '📺', name: 'YouTube', color: 'bg-red-500' },
  tiktok: { icon: '🎵', name: 'TikTok', color: 'bg-gray-900' },
  instagram: { icon: '📷', name: 'Instagram', color: 'bg-gradient-to-r from-purple-500 to-pink-500' },
  vk: { icon: '💬', name: 'VK', color: 'bg-blue-500' },
  telegram: { icon: '✈️', name: 'Telegram', color: 'bg-sky-500' },
}

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['publishing-stats'],
    queryFn: () => api.get('/api/v1/publishing/stats').then(r => r.data),
  })

  const { data: videoStats } = useQuery({
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

  const totalPublished = stats?.total_published || 0
  const totalViews = stats?.total_views || 0
  const totalLikes = stats?.total_likes || 0
  const totalComments = stats?.total_comments || 0
  const videoCounts = videoStats?.statistics?.videos || {}
  const totalVideos = Object.values(videoCounts).reduce((a: number, b: any) => a + (b || 0), 0)

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <BarChart3 className="w-8 h-8 mr-3 text-primary-600" />
          Аналитика
        </h1>
        <p className="text-gray-600 mt-1">
          Статистика по всем платформам
        </p>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-8">
        <StatCard
          title="Всего видео"
          value={totalVideos}
          icon={Video}
          color="blue"
        />
        <StatCard
          title="Опубликовано"
          value={totalPublished}
          icon={Share2}
          color="green"
        />
        <StatCard
          title="Просмотры"
          value={totalViews.toLocaleString()}
          icon={Eye}
          color="purple"
        />
        <StatCard
          title="Лайки"
          value={totalLikes.toLocaleString()}
          icon={ThumbsUp}
          color="pink"
        />
        <StatCard
          title="Комментарии"
          value={totalComments.toLocaleString()}
          icon={MessageCircle}
          color="yellow"
        />
      </div>

      {/* Platform Breakdown */}
      <div className="card mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Статистика по платформам</h2>
        </div>
        <div className="p-6">
          {!stats?.by_platform || Object.keys(stats.by_platform).length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">Данных пока нет</p>
              <p className="text-sm text-gray-400">
                Начните публиковать видео, чтобы видеть статистику
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(stats.by_platform).map(([platform, data]: [string, any]) => {
                const config = PLATFORM_CONFIG[platform]
                const maxViews = Math.max(
                  ...Object.values(stats.by_platform).map((d: any) => d.views || 0)
                )
                const percentage = maxViews > 0 ? (data.views / maxViews) * 100 : 0

                return (
                  <div key={platform}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{config?.icon || '📱'}</span>
                        <div>
                          <p className="font-medium text-gray-900">{config?.name || platform}</p>
                          <p className="text-sm text-gray-500">{data.count} видео</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-gray-900">
                          {data.views?.toLocaleString() || 0}
                        </p>
                        <p className="text-sm text-gray-500">
                          {data.likes?.toLocaleString() || 0} лайков
                        </p>
                      </div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${config?.color || 'bg-primary-600'} rounded-full transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Video Status Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h3 className="font-semibold mb-4">Статусы видео</h3>
          <div className="space-y-3">
            {[
              { key: 'completed', label: 'Завершено', color: 'bg-green-500' },
              { key: 'generating_script', label: 'Генерация скрипта', color: 'bg-blue-500' },
              { key: 'generating_audio', label: 'Генерация аудио', color: 'bg-indigo-500' },
              { key: 'generating_video', label: 'Генерация видео', color: 'bg-purple-500' },
              { key: 'rendering', label: 'Рендеринг', color: 'bg-orange-500' },
              { key: 'failed', label: 'Ошибки', color: 'bg-red-500' },
              { key: 'pending', label: 'В очереди', color: 'bg-gray-400' },
            ].map(({ key, label, color }) => {
              const count = videoCounts[key] || 0
              const percentage = totalVideos > 0 ? (count / totalVideos) * 100 : 0

              return (
                <div key={key} className="flex items-center">
                  <div className={`w-3 h-3 rounded-full ${color} mr-3`} />
                  <span className="text-gray-600 flex-1">{label}</span>
                  <span className="font-medium text-gray-900">{count}</span>
                  <span className="text-gray-400 text-sm ml-2 w-12 text-right">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
            Советы по росту
          </h3>
          <ul className="space-y-3 text-gray-600">
            <li className="flex items-start">
              <span className="text-green-500 mr-3 font-bold">1.</span>
              <span>Публикуйте в одно время каждый день для лучшего охвата</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-3 font-bold">2.</span>
              <span>Используйте трендовые темы и хэштеги в вашей нише</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-3 font-bold">3.</span>
              <span>Первые 3 секунды — ключ к удержанию зрителей</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-3 font-bold">4.</span>
              <span>Кросс-постинг на все платформы увеличивает охват</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-3 font-bold">5.</span>
              <span>Анализируйте лучшие темы и создавайте больше похожего контента</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Engagement Rate */}
      {totalViews > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold mb-4">Показатели вовлеченности</h3>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">
                {((totalLikes / totalViews) * 100).toFixed(1)}%
              </div>
              <div className="text-gray-500">Лайки / Просмотры</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {((totalComments / totalViews) * 100).toFixed(2)}%
              </div>
              <div className="text-gray-500">Комментарии / Просмотры</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {totalPublished > 0 ? Math.round(totalViews / totalPublished).toLocaleString() : 0}
              </div>
              <div className="text-gray-500">Среднее просмотров на видео</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color }: {
  title: string
  value: string | number
  icon: any
  color: 'blue' | 'green' | 'pink' | 'yellow' | 'purple'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    pink: 'bg-pink-50 text-pink-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
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
