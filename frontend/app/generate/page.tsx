'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Zap, Sparkles, Volume2, Video, Send, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

export default function GeneratePage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  // Form state
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('technology')
  const [style, setStyle] = useState('educational')
  const [tone, setTone] = useState('professional')
  const [duration, setDuration] = useState(45)
  const [videoType, setVideoType] = useState('avatar')
  const [autoPublish, setAutoPublish] = useState(true)
  const [platforms, setPlatforms] = useState(['youtube', 'tiktok', 'vk', 'telegram'])

  // Custom prompt for more control
  const [useCustomPrompt, setUseCustomPrompt] = useState(false)
  const [customPrompt, setCustomPrompt] = useState('')

  const generateMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/videos/generate', data)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Генерация запущена!')
      queryClient.invalidateQueries({ queryKey: ['recent-videos'] })
      router.push('/videos')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Ошибка при запуске генерации'
      toast.error(message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!topic.trim() && !customPrompt.trim()) {
      toast.error('Введите тему для видео')
      return
    }

    generateMutation.mutate({
      topic: useCustomPrompt ? customPrompt : topic,
      niche,
      style,
      tone,
      video_type: videoType,
      duration_seconds: duration,
      auto_publish: autoPublish,
      platforms: autoPublish ? platforms : [],
    })
  }

  const togglePlatform = (platformId: string) => {
    setPlatforms(prev =>
      prev.includes(platformId)
        ? prev.filter(p => p !== platformId)
        : [...prev, platformId]
    )
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Zap className="w-8 h-8 mr-3 text-primary-600" />
          Создать видео
        </h1>
        <p className="text-gray-600 mt-1">
          AI автоматически создаст сценарий, озвучку, видео и субтитры
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic Input */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-yellow-500" />
              Тема видео
            </h2>
            <label className="flex items-center text-sm text-gray-600">
              <input
                type="checkbox"
                checked={useCustomPrompt}
                onChange={(e) => setUseCustomPrompt(e.target.checked)}
                className="mr-2 rounded border-gray-300"
              />
              Свой промпт
            </label>
          </div>

          {useCustomPrompt ? (
            <div>
              <label className="label">Полный промпт для генерации</label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Напишите детальный промпт для Claude. Опишите тему, стиль, ключевые моменты, которые должны быть в видео..."
                className="input h-32 resize-none"
                required={useCustomPrompt}
              />
              <p className="text-sm text-gray-500 mt-2">
                Claude получит этот промпт напрямую для генерации сценария
              </p>
            </div>
          ) : (
            <div>
              <label className="label">О чём будет видео?</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Например: 5 нейросетей которые изменят 2025 год"
                className="input text-lg"
                required={!useCustomPrompt}
              />
              <p className="text-sm text-gray-500 mt-2">
                AI сам напишет вирусный сценарий на эту тему
              </p>
            </div>
          )}
        </div>

        {/* Settings */}
        {!useCustomPrompt && (
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Настройки контента</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Ниша</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="input"
                >
                  <option value="technology">Технологии</option>
                  <option value="business">Бизнес</option>
                  <option value="finance">Финансы</option>
                  <option value="education">Образование</option>
                  <option value="health">Здоровье</option>
                  <option value="lifestyle">Лайфстайл</option>
                  <option value="entertainment">Развлечения</option>
                  <option value="science">Наука</option>
                </select>
              </div>

              <div>
                <label className="label">Стиль</label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="input"
                >
                  <option value="educational">Образовательный</option>
                  <option value="entertaining">Развлекательный</option>
                  <option value="motivational">Мотивационный</option>
                  <option value="news">Новостной</option>
                  <option value="tutorial">Туториал</option>
                  <option value="storytelling">Сторителлинг</option>
                </select>
              </div>

              <div>
                <label className="label">Тон</label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="input"
                >
                  <option value="professional">Профессиональный</option>
                  <option value="casual">Разговорный</option>
                  <option value="energetic">Энергичный</option>
                  <option value="calm">Спокойный</option>
                  <option value="humorous">С юмором</option>
                </select>
              </div>

              <div>
                <label className="label">Длительность: {duration} сек</label>
                <input
                  type="range"
                  min="20"
                  max="60"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>20 сек</span>
                  <span>60 сек</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Video Type */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Video className="w-5 h-5 mr-2 text-purple-500" />
            Тип видео
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setVideoType('avatar')}
              className={`p-4 border-2 rounded-xl text-left transition-all ${
                videoType === 'avatar'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">🎭</div>
              <div className="font-semibold">AI Аватар</div>
              <div className="text-sm text-gray-500">
                Говорящая голова через HeyGen
              </div>
            </button>

            <button
              type="button"
              onClick={() => setVideoType('ai_generated')}
              className={`p-4 border-2 rounded-xl text-left transition-all ${
                videoType === 'ai_generated'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">🎬</div>
              <div className="font-semibold">AI Видео</div>
              <div className="text-sm text-gray-500">
                Генерация через Kling AI
              </div>
            </button>
          </div>
        </div>

        {/* Publishing */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Send className="w-5 h-5 mr-2 text-green-500" />
            Публикация
          </h2>

          <label className="flex items-center mb-4">
            <input
              type="checkbox"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="ml-3 text-gray-700">Автопубликация после генерации</span>
          </label>

          {autoPublish && (
            <div>
              <p className="text-sm text-gray-500 mb-3">Выберите платформы:</p>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'youtube', name: 'YouTube Shorts', icon: '📺' },
                  { id: 'tiktok', name: 'TikTok', icon: '🎵' },
                  { id: 'vk', name: 'VK Clips', icon: '💬' },
                  { id: 'telegram', name: 'Telegram', icon: '✈️' },
                  { id: 'instagram', name: 'Instagram', icon: '📷' },
                ].map((platform) => (
                  <button
                    key={platform.id}
                    type="button"
                    onClick={() => togglePlatform(platform.id)}
                    className={`px-4 py-2 rounded-lg border-2 transition-all ${
                      platforms.includes(platform.id)
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
          )}
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={generateMutation.isPending}
            className="btn-primary px-8 py-4 text-lg disabled:opacity-50"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Запускаем...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5 mr-2" />
                Создать видео
              </>
            )}
          </button>
        </div>
      </form>

      {/* Info */}
      <div className="mt-8 p-4 bg-blue-50 rounded-xl text-sm text-blue-800">
        <strong>Как это работает:</strong>
        <ol className="mt-2 space-y-1 list-decimal list-inside">
          <li>Claude напишет вирусный сценарий с хуком</li>
          <li>ElevenLabs озвучит текст естественным голосом</li>
          <li>HeyGen или Kling создаст видео</li>
          <li>Автоматически добавятся субтитры в стиле TikTok</li>
          <li>Видео опубликуется на выбранных платформах</li>
        </ol>
      </div>
    </div>
  )
}
