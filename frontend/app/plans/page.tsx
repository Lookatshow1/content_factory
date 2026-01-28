'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Trash2, Play, Pause, Clock, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

const NICHE_LABELS: Record<string, string> = {
  technology: 'Технологии',
  business: 'Бизнес',
  finance: 'Финансы',
  health: 'Здоровье',
  education: 'Образование',
  lifestyle: 'Лайфстайл',
  entertainment: 'Развлечения',
  science: 'Наука',
}

const STYLE_LABELS: Record<string, string> = {
  educational: 'Образовательный',
  entertaining: 'Развлекательный',
  motivational: 'Мотивационный',
  news: 'Новостной',
  tutorial: 'Туториал',
  storytelling: 'Сторителлинг',
}

const DAY_LABELS: Record<number, string> = {
  0: 'Пн',
  1: 'Вт',
  2: 'Ср',
  3: 'Чт',
  4: 'Пт',
  5: 'Сб',
  6: 'Вс',
}

export default function PlansPage() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)

  const { data: plans, isLoading } = useQuery({
    queryKey: ['content-plans'],
    queryFn: () => api.get('/api/v1/content-plans').then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/content-plans/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] })
      toast.success('План удален')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      api.post(`/api/v1/content-plans/${id}/${active ? 'activate' : 'deactivate'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] })
      toast.success('План обновлен')
    },
  })

  const runNowMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/content-plans/${id}/run-now`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] })
      toast.success('Генерация запущена!')
    },
    onError: () => toast.error('Ошибка при запуске'),
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
            <Calendar className="w-8 h-8 mr-3 text-primary-600" />
            Контент-планы
          </h1>
          <p className="text-gray-600 mt-1">
            Автоматическая генерация видео по расписанию
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-5 h-5 mr-2" />
          Создать план
        </button>
      </div>

      {(!plans || plans.length === 0) && (
        <div className="card p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">Контент-планов пока нет</h3>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            Создайте контент-план, чтобы автоматически генерировать видео по расписанию.
            Система сама будет создавать и публиковать контент.
          </p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-5 h-5 mr-2" />
            Создать первый план
          </button>
        </div>
      )}

      <div className="grid gap-6">
        {plans?.map((plan: any) => (
          <div key={plan.id} className="card overflow-hidden">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center">
                    <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                    <span className={`ml-3 px-3 py-1 rounded-full text-xs font-medium ${
                      plan.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {plan.is_active ? 'Активен' : 'На паузе'}
                    </span>
                  </div>
                  {plan.description && (
                    <p className="text-gray-600 mt-1">{plan.description}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {/* Run Now */}
                  <button
                    onClick={() => runNowMutation.mutate(plan.id)}
                    disabled={runNowMutation.isPending}
                    className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg disabled:opacity-50"
                    title="Запустить сейчас"
                  >
                    <Zap className="w-5 h-5" />
                  </button>
                  {/* Toggle */}
                  <button
                    onClick={() => toggleMutation.mutate({
                      id: plan.id,
                      active: !plan.is_active,
                    })}
                    className={`p-2 rounded-lg ${
                      plan.is_active
                        ? 'text-yellow-600 hover:bg-yellow-50'
                        : 'text-green-600 hover:bg-green-50'
                    }`}
                    title={plan.is_active ? 'Поставить на паузу' : 'Активировать'}
                  >
                    {plan.is_active ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </button>
                  {/* Delete */}
                  <button
                    onClick={() => {
                      if (confirm('Удалить этот контент-план?')) {
                        deleteMutation.mutate(plan.id)
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    title="Удалить"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Settings Grid */}
            <div className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <span className="text-sm text-gray-500 block mb-1">Ниша</span>
                  <span className="font-medium">{NICHE_LABELS[plan.niche] || plan.niche}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block mb-1">Видео в неделю</span>
                  <span className="font-medium">{plan.videos_per_week}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block mb-1">Время публикации</span>
                  <span className="font-medium">{plan.publish_time || '12:00'}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block mb-1">Тип видео</span>
                  <span className="font-medium">
                    {plan.video_type === 'avatar' ? 'AI Аватар' : 'AI Видео'}
                  </span>
                </div>
              </div>

              {/* Topics */}
              {plan.topics?.length > 0 && (
                <div className="mt-6">
                  <span className="text-sm text-gray-500 block mb-2">Темы для генерации:</span>
                  <div className="flex flex-wrap gap-2">
                    {plan.topics.map((topic: string, i: number) => (
                      <span key={i} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Platforms */}
              <div className="mt-6">
                <span className="text-sm text-gray-500 block mb-2">Платформы для публикации:</span>
                <div className="flex flex-wrap gap-2">
                  {plan.platforms?.map((platform: string) => (
                    <span key={platform} className="px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-sm font-medium">
                      {platform === 'youtube' && '📺 YouTube'}
                      {platform === 'tiktok' && '🎵 TikTok'}
                      {platform === 'vk' && '💬 VK'}
                      {platform === 'telegram' && '✈️ Telegram'}
                      {platform === 'instagram' && '📷 Instagram'}
                    </span>
                  ))}
                </div>
              </div>

              {/* Upcoming */}
              {plan.items?.filter((i: any) => !i.is_published).length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                    <Clock className="w-4 h-4 mr-2" />
                    Запланировано
                  </h4>
                  <div className="space-y-2">
                    {plan.items
                      .filter((item: any) => !item.is_published)
                      .slice(0, 5)
                      .map((item: any) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="text-gray-900">{item.topic}</span>
                          <span className="text-sm text-gray-500">
                            {new Date(item.scheduled_date).toLocaleDateString('ru-RU', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Create Plan Modal */}
      {showCreate && (
        <CreatePlanModal onClose={() => setShowCreate(false)} />
      )}
    </div>
  )
}

function CreatePlanModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    name: '',
    description: '',
    niche: 'technology',
    topics: '',
    style: 'educational',
    video_type: 'avatar',
    videos_per_week: 5,
    publish_days: [0, 1, 2, 3, 4],
    publish_time: '12:00',
    platforms: ['youtube', 'tiktok', 'vk', 'telegram'],
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/content-plans', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] })
      toast.success('Контент-план создан!')
      onClose()
    },
    onError: () => toast.error('Ошибка при создании плана'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      topics: form.topics.split('\n').filter(t => t.trim()),
    })
  }

  const togglePlatform = (platform: string) => {
    setForm(f => ({
      ...f,
      platforms: f.platforms.includes(platform)
        ? f.platforms.filter(p => p !== platform)
        : [...f.platforms, platform],
    }))
  }

  const toggleDay = (day: number) => {
    setForm(f => ({
      ...f,
      publish_days: f.publish_days.includes(day)
        ? f.publish_days.filter(d => d !== day)
        : [...f.publish_days, day].sort(),
    }))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold">Создать контент-план</h2>
          <p className="text-gray-500 text-sm mt-1">
            Настройте автоматическую генерацию видео
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div>
              <label className="label">Название плана</label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="input"
                required
                placeholder="Например: AI новости каждый день"
              />
            </div>

            <div>
              <label className="label">Описание</label>
              <textarea
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className="input"
                rows={2}
                placeholder="Краткое описание плана (опционально)"
              />
            </div>
          </div>

          {/* Content Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Ниша</label>
              <select
                value={form.niche}
                onChange={e => setForm(f => ({ ...f, niche: e.target.value }))}
                className="input"
              >
                {Object.entries(NICHE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Стиль</label>
              <select
                value={form.style}
                onChange={e => setForm(f => ({ ...f, style: e.target.value }))}
                className="input"
              >
                {Object.entries(STYLE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Topics */}
          <div>
            <label className="label">Темы для генерации (по одной на строку)</label>
            <textarea
              value={form.topics}
              onChange={e => setForm(f => ({ ...f, topics: e.target.value }))}
              className="input"
              rows={4}
              placeholder="Новости AI и нейросетей&#10;Обзоры новых технологий&#10;Туториалы по программированию&#10;Советы по продуктивности"
            />
            <p className="text-sm text-gray-500 mt-1">
              Видео будут генерироваться по очереди из этих тем
            </p>
          </div>

          {/* Schedule */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Видео в неделю</label>
              <input
                type="number"
                min="1"
                max="21"
                value={form.videos_per_week}
                onChange={e => setForm(f => ({ ...f, videos_per_week: Number(e.target.value) }))}
                className="input"
              />
            </div>
            <div>
              <label className="label">Время публикации</label>
              <input
                type="time"
                value={form.publish_time}
                onChange={e => setForm(f => ({ ...f, publish_time: e.target.value }))}
                className="input"
              />
            </div>
          </div>

          {/* Days */}
          <div>
            <label className="label">Дни публикации</label>
            <div className="flex gap-2">
              {Object.entries(DAY_LABELS).map(([day, label]) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => toggleDay(Number(day))}
                  className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                    form.publish_days.includes(Number(day))
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Video Type */}
          <div>
            <label className="label">Тип видео</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setForm(f => ({ ...f, video_type: 'avatar' }))}
                className={`p-4 border-2 rounded-xl text-left transition-all ${
                  form.video_type === 'avatar'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">🎭</div>
                <div className="font-semibold">AI Аватар</div>
                <div className="text-sm text-gray-500">HeyGen</div>
              </button>
              <button
                type="button"
                onClick={() => setForm(f => ({ ...f, video_type: 'ai_generated' }))}
                className={`p-4 border-2 rounded-xl text-left transition-all ${
                  form.video_type === 'ai_generated'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">🎬</div>
                <div className="font-semibold">AI Видео</div>
                <div className="text-sm text-gray-500">Kling AI</div>
              </button>
            </div>
          </div>

          {/* Platforms */}
          <div>
            <label className="label">Платформы для публикации</label>
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'youtube', name: 'YouTube', icon: '📺' },
                { id: 'tiktok', name: 'TikTok', icon: '🎵' },
                { id: 'vk', name: 'VK', icon: '💬' },
                { id: 'telegram', name: 'Telegram', icon: '✈️' },
                { id: 'instagram', name: 'Instagram', icon: '📷' },
              ].map((platform) => (
                <button
                  key={platform.id}
                  type="button"
                  onClick={() => togglePlatform(platform.id)}
                  className={`px-4 py-2 rounded-lg border-2 transition-all ${
                    form.platforms.includes(platform.id)
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <span className="mr-2">{platform.icon}</span>
                  {platform.name}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button type="button" onClick={onClose} className="btn-secondary">
              Отмена
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !form.name}
              className="btn-primary disabled:opacity-50"
            >
              {createMutation.isPending ? 'Создание...' : 'Создать план'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
