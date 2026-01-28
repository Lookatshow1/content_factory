'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Video, Play, Trash2, RefreshCw, Share2, Download, Eye, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import Link from 'next/link'

const STATUS_LABELS: Record<string, string> = {
  pending: 'В очереди',
  generating_script: 'Генерация скрипта',
  script_ready: 'Скрипт готов',
  generating_audio: 'Генерация аудио',
  audio_ready: 'Аудио готово',
  generating_video: 'Генерация видео',
  video_ready: 'Видео готово',
  adding_subtitles: 'Добавление субтитров',
  rendering: 'Рендеринг',
  completed: 'Завершено',
  failed: 'Ошибка',
}

export default function VideosPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [selectedVideo, setSelectedVideo] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['videos', page],
    queryFn: () => api.get(`/api/v1/videos?page=${page}&per_page=10`).then(r => r.data),
    refetchInterval: 5000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/videos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      toast.success('Видео удалено')
    },
    onError: () => toast.error('Ошибка при удалении'),
  })

  const regenerateMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/videos/${id}/regenerate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      toast.success('Перегенерация запущена')
    },
    onError: () => toast.error('Ошибка при перегенерации'),
  })

  const publishMutation = useMutation({
    mutationFn: (videoId: number) => api.post('/api/v1/publishing/publish', {
      video_id: videoId,
      platforms: ['youtube', 'tiktok', 'vk', 'telegram'],
    }),
    onSuccess: () => {
      toast.success('Публикация запущена')
    },
    onError: () => toast.error('Ошибка при публикации'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Video className="w-8 h-8 mr-3 text-primary-600" />
            Мои видео
          </h1>
          <p className="text-gray-600 mt-1">
            Управление сгенерированными видео
          </p>
        </div>
        <Link href="/generate" className="btn-primary">
          Создать видео
        </Link>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Видео</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Тема</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Статус</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Тип</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Дата</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <Video className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Видео пока нет</p>
                    <Link href="/generate" className="btn-primary">
                      Создать первое видео
                    </Link>
                  </td>
                </tr>
              )}
              {data?.items?.map((video: any) => (
                <tr key={video.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-16 h-24 bg-gray-200 rounded-lg mr-4 flex items-center justify-center overflow-hidden flex-shrink-0">
                        {video.thumbnail_path ? (
                          <img
                            src={`/api/v1/media/${video.thumbnail_path}`}
                            alt={video.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Video className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 truncate max-w-[200px]">{video.title || 'Без названия'}</p>
                        <p className="text-sm text-gray-500">{video.duration_seconds} сек</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-900 truncate max-w-[150px] block">{video.topic || '-'}</span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={video.status} />
                    {video.error_message && (
                      <p className="text-xs text-red-600 mt-1 line-clamp-1 max-w-[150px]">
                        {video.error_message}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-600">
                      {video.video_type === 'avatar' ? 'AI Аватар' : 'AI Видео'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                    {new Date(video.created_at).toLocaleDateString('ru-RU')}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end space-x-1">
                      {/* View Script */}
                      {video.script_text && (
                        <button
                          onClick={() => setSelectedVideo(video)}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                          title="Просмотреть скрипт"
                        >
                          <FileText className="w-5 h-5" />
                        </button>
                      )}

                      {/* Preview */}
                      {video.status === 'completed' && video.video_final_path && (
                        <button
                          onClick={() => window.open(`/api/v1/media/${video.video_final_path}`, '_blank')}
                          className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                          title="Просмотр"
                        >
                          <Play className="w-5 h-5" />
                        </button>
                      )}

                      {/* Download */}
                      {video.status === 'completed' && video.video_final_path && (
                        <a
                          href={`/api/v1/media/${video.video_final_path}`}
                          download
                          className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg"
                          title="Скачать"
                        >
                          <Download className="w-5 h-5" />
                        </a>
                      )}

                      {/* Publish */}
                      {video.status === 'completed' && (
                        <button
                          onClick={() => publishMutation.mutate(video.id)}
                          disabled={publishMutation.isPending}
                          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg disabled:opacity-50"
                          title="Опубликовать"
                        >
                          <Share2 className="w-5 h-5" />
                        </button>
                      )}

                      {/* Regenerate */}
                      {video.status === 'failed' && (
                        <button
                          onClick={() => regenerateMutation.mutate(video.id)}
                          disabled={regenerateMutation.isPending}
                          className="p-2 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg disabled:opacity-50"
                          title="Перегенерировать"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </button>
                      )}

                      {/* Delete */}
                      <button
                        onClick={() => {
                          if (confirm('Удалить это видео?')) {
                            deleteMutation.mutate(video.id)
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                        title="Удалить"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Страница {data.page} из {data.pages} ({data.total} видео)
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary disabled:opacity-50"
              >
                Назад
              </button>
              <button
                onClick={() => setPage(p => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="btn-secondary disabled:opacity-50"
              >
                Вперед
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Script Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Сценарий видео</h2>
              <button
                onClick={() => setSelectedVideo(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                &times;
              </button>
            </div>
            <div className="p-6 overflow-auto max-h-[60vh]">
              <div className="mb-4">
                <span className="text-sm text-gray-500">Тема:</span>
                <p className="font-medium">{selectedVideo.topic}</p>
              </div>
              <div className="mb-4">
                <span className="text-sm text-gray-500">Заголовок:</span>
                <p className="font-medium">{selectedVideo.title}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Скрипт:</span>
                <pre className="mt-2 p-4 bg-gray-50 rounded-lg text-sm whitespace-pre-wrap font-sans">
                  {selectedVideo.script_text}
                </pre>
              </div>
            </div>
            <div className="p-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedVideo(null)}
                className="btn-secondary"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const isProcessing = ['generating_script', 'generating_audio', 'generating_video', 'rendering', 'adding_subtitles'].includes(status)

  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    generating_script: 'bg-blue-100 text-blue-600',
    script_ready: 'bg-blue-100 text-blue-600',
    generating_audio: 'bg-indigo-100 text-indigo-600',
    audio_ready: 'bg-indigo-100 text-indigo-600',
    generating_video: 'bg-purple-100 text-purple-600',
    video_ready: 'bg-purple-100 text-purple-600',
    adding_subtitles: 'bg-yellow-100 text-yellow-600',
    rendering: 'bg-orange-100 text-orange-600',
    completed: 'bg-green-100 text-green-600',
    failed: 'bg-red-100 text-red-600',
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {isProcessing && (
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-2" />
      )}
      {STATUS_LABELS[status] || status}
    </span>
  )
}
