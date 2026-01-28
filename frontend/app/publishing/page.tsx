'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Share2, RefreshCw, ExternalLink, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

const PLATFORM_CONFIG: Record<string, { icon: string; name: string; color: string }> = {
  youtube: { icon: '📺', name: 'YouTube Shorts', color: 'bg-red-50 text-red-700' },
  tiktok: { icon: '🎵', name: 'TikTok', color: 'bg-gray-900 text-white' },
  instagram: { icon: '📷', name: 'Instagram Reels', color: 'bg-pink-50 text-pink-700' },
  vk: { icon: '💬', name: 'VK Clips', color: 'bg-blue-50 text-blue-700' },
  telegram: { icon: '✈️', name: 'Telegram', color: 'bg-sky-50 text-sky-700' },
}

const STATUS_CONFIG: Record<string, { icon: any; className: string; label: string }> = {
  pending: { icon: Clock, className: 'bg-gray-100 text-gray-600', label: 'В очереди' },
  uploading: { icon: Loader2, className: 'bg-blue-100 text-blue-600', label: 'Загрузка' },
  processing: { icon: Loader2, className: 'bg-yellow-100 text-yellow-600', label: 'Обработка' },
  published: { icon: CheckCircle, className: 'bg-green-100 text-green-600', label: 'Опубликовано' },
  failed: { icon: XCircle, className: 'bg-red-100 text-red-600', label: 'Ошибка' },
  scheduled: { icon: Clock, className: 'bg-purple-100 text-purple-600', label: 'Запланировано' },
}

export default function PublishingPage() {
  const queryClient = useQueryClient()

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['publishing-tasks'],
    queryFn: () => api.get('/api/v1/publishing/tasks?limit=50').then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: stats } = useQuery({
    queryKey: ['publishing-stats'],
    queryFn: () => api.get('/api/v1/publishing/stats').then(r => r.data),
  })

  const retryMutation = useMutation({
    mutationFn: (taskId: number) => api.post(`/api/v1/publishing/tasks/${taskId}/retry`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publishing-tasks'] })
      toast.success('Повторная публикация запущена')
    },
    onError: () => toast.error('Ошибка при повторной попытке'),
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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Share2 className="w-8 h-8 mr-3 text-primary-600" />
          Публикации
        </h1>
        <p className="text-gray-600 mt-1">
          Отслеживание публикаций на всех платформах
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6">
          <div className="text-3xl font-bold text-gray-900">{totalPublished}</div>
          <div className="text-gray-500">Опубликовано</div>
        </div>
        <div className="card p-6">
          <div className="text-3xl font-bold text-gray-900">{totalViews.toLocaleString()}</div>
          <div className="text-gray-500">Всего просмотров</div>
        </div>
        <div className="card p-6">
          <div className="text-3xl font-bold text-gray-900">{totalLikes.toLocaleString()}</div>
          <div className="text-gray-500">Всего лайков</div>
        </div>
      </div>

      {/* Platform Stats */}
      {stats?.by_platform && Object.keys(stats.by_platform).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {Object.entries(stats.by_platform).map(([platform, data]: [string, any]) => {
            const config = PLATFORM_CONFIG[platform]
            return (
              <div key={platform} className="card p-4">
                <div className="flex items-center mb-3">
                  <span className="text-2xl mr-2">{config?.icon || '📱'}</span>
                  <span className="font-medium">{config?.name || platform}</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">{data.count}</div>
                <div className="text-sm text-gray-500">
                  {data.views?.toLocaleString() || 0} просмотров
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Tasks Table */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">История публикаций</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Платформа</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Видео</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Статус</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Дата</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Статистика</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(!tasks || tasks.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <Share2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">Публикаций пока нет</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Создайте видео и опубликуйте его на платформах
                    </p>
                  </td>
                </tr>
              )}
              {tasks?.map((task: any) => {
                const platformConfig = PLATFORM_CONFIG[task.platform]
                const statusConfig = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending
                const StatusIcon = statusConfig.icon

                return (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{platformConfig?.icon || '📱'}</span>
                        <span className="font-medium">{platformConfig?.name || task.platform}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-900">Видео #{task.video_id}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${statusConfig.className}`}>
                        <StatusIcon className={`w-4 h-4 mr-1 ${task.status === 'uploading' || task.status === 'processing' ? 'animate-spin' : ''}`} />
                        {statusConfig.label}
                      </span>
                      {task.error_message && (
                        <p className="text-xs text-red-600 mt-1 max-w-[200px] truncate">
                          {task.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                      {task.published_at
                        ? new Date(task.published_at).toLocaleDateString('ru-RU', {
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '-'}
                    </td>
                    <td className="px-6 py-4">
                      {task.status === 'published' && (
                        <div className="text-sm">
                          <span className="text-gray-900 font-medium">{task.views || 0}</span>
                          <span className="text-gray-500"> просм.</span>
                          <span className="mx-2 text-gray-300">·</span>
                          <span className="text-gray-900 font-medium">{task.likes || 0}</span>
                          <span className="text-gray-500"> лайков</span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end space-x-2">
                        {task.platform_url && (
                          <a
                            href={task.platform_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                            title="Открыть на платформе"
                          >
                            <ExternalLink className="w-5 h-5" />
                          </a>
                        )}
                        {task.status === 'failed' && (
                          <button
                            onClick={() => retryMutation.mutate(task.id)}
                            disabled={retryMutation.isPending}
                            className="p-2 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg disabled:opacity-50"
                            title="Повторить"
                          >
                            <RefreshCw className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
