'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Zap, Sparkles, Video, Send, Loader2, Image, Film, Layers, Settings2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

export default function GeneratePage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  // Basic settings
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('technology')
  const [style, setStyle] = useState('educational')
  const [tone, setTone] = useState('professional')
  const [duration, setDuration] = useState(45)

  // Custom content options
  const [useCustomScript, setUseCustomScript] = useState(false)
  const [customScriptText, setCustomScriptText] = useState('')
  const [customImagePrompt, setCustomImagePrompt] = useState('')

  // Video type and output mode
  const [videoType, setVideoType] = useState('avatar')
  const [outputMode, setOutputMode] = useState('avatar_only')

  // Insert settings
  const [insertPercentage, setInsertPercentage] = useState(50)
  const [useStockFootage, setUseStockFootage] = useState(false)
  const [stockSearchQuery, setStockSearchQuery] = useState('')

  // Publishing
  const [autoPublish, setAutoPublish] = useState(true)
  const [platforms, setPlatforms] = useState(['youtube', 'tiktok', 'vk', 'telegram'])

  // Advanced options visibility
  const [showAdvanced, setShowAdvanced] = useState(false)

  const generateMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/videos/generate', data)
      return response.data
    },
    onSuccess: () => {
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

    if (!topic.trim() && !customScriptText.trim()) {
      toast.error('Введите тему или свой текст для видео')
      return
    }

    generateMutation.mutate({
      topic,
      niche,
      style,
      tone,
      video_type: videoType,
      output_mode: outputMode,
      duration_seconds: duration,
      use_custom_script: useCustomScript,
      custom_script_text: useCustomScript ? customScriptText : null,
      custom_image_prompt: customImagePrompt || null,
      insert_percentage: insertPercentage / 100,
      use_stock_footage: useStockFootage,
      stock_search_query: useStockFootage ? stockSearchQuery : null,
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
        {/* Content Source */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-yellow-500" />
              Контент
            </h2>
            <label className="flex items-center text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={useCustomScript}
                onChange={(e) => setUseCustomScript(e.target.checked)}
                className="mr-2 rounded border-gray-300"
              />
              Использовать свой текст
            </label>
          </div>

          {useCustomScript ? (
            <div className="space-y-4">
              <div>
                <label className="label">Ваш сценарий / текст для озвучки</label>
                <textarea
                  value={customScriptText}
                  onChange={(e) => setCustomScriptText(e.target.value)}
                  placeholder="Введите полный текст, который будет озвучен. Можете использовать [PAUSE] для пауз..."
                  className="input h-40 resize-none"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Этот текст будет озвучен напрямую через ElevenLabs
                </p>
              </div>

              <div>
                <label className="label">Заголовок видео</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Название для публикации"
                  className="input"
                />
              </div>
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
                required
              />
              <p className="text-sm text-gray-500 mt-2">
                AI сам напишет вирусный сценарий на эту тему
              </p>
            </div>
          )}
        </div>

        {/* Settings - only show for AI-generated scripts */}
        {!useCustomScript && (
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Настройки контента</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Ниша</label>
                <select value={niche} onChange={(e) => setNiche(e.target.value)} className="input">
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
                <select value={style} onChange={(e) => setStyle(e.target.value)} className="input">
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
                <select value={tone} onChange={(e) => setTone(e.target.value)} className="input">
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
                  className="w-full h-2 bg-gray-200 rounded-lg cursor-pointer accent-primary-600"
                />
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              type="button"
              onClick={() => { setVideoType('avatar'); setOutputMode('avatar_only'); }}
              className={`p-4 border-2 rounded-xl text-left transition-all ${
                videoType === 'avatar' && outputMode === 'avatar_only'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">🎭</div>
              <div className="font-semibold">Только аватар</div>
              <div className="text-sm text-gray-500">Говорящая голова HeyGen</div>
            </button>

            <button
              type="button"
              onClick={() => { setVideoType('avatar_inserts'); setOutputMode('avatar_inserts'); }}
              className={`p-4 border-2 rounded-xl text-left transition-all ${
                videoType === 'avatar_inserts'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">🎭🖼️</div>
              <div className="font-semibold">Аватар + вставки</div>
              <div className="text-sm text-gray-500">Аватар с AI-картинками</div>
            </button>

            <button
              type="button"
              onClick={() => { setVideoType('images_slideshow'); setOutputMode('inserts_only'); }}
              className={`p-4 border-2 rounded-xl text-left transition-all ${
                videoType === 'images_slideshow'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">🖼️</div>
              <div className="font-semibold">Только картинки</div>
              <div className="text-sm text-gray-500">Слайдшоу с озвучкой</div>
            </button>
          </div>
        </div>

        {/* Image/Insert Settings - show when using inserts */}
        {(videoType === 'avatar_inserts' || videoType === 'images_slideshow') && (
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Image className="w-5 h-5 mr-2 text-green-500" />
              Настройки изображений
            </h2>

            <div className="space-y-4">
              {/* Custom image prompt */}
              <div>
                <label className="label">Базовый промпт для изображений (опционально)</label>
                <textarea
                  value={customImagePrompt}
                  onChange={(e) => setCustomImagePrompt(e.target.value)}
                  placeholder="Например: минималистичный стиль, тёмный фон, неоновые акценты, футуристичный..."
                  className="input h-20 resize-none"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Этот стиль будет добавлен ко всем генерируемым изображениям
                </p>
              </div>

              {/* Insert percentage */}
              {videoType === 'avatar_inserts' && (
                <div>
                  <label className="label">
                    Процент вставок: {insertPercentage}%
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="90"
                    value={insertPercentage}
                    onChange={(e) => setInsertPercentage(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg cursor-pointer accent-primary-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>10% (больше аватара)</span>
                    <span>90% (больше картинок)</span>
                  </div>
                </div>
              )}

              {/* Stock footage option */}
              <div className="pt-4 border-t border-gray-200">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useStockFootage}
                    onChange={(e) => setUseStockFootage(e.target.checked)}
                    className="w-5 h-5 rounded border-gray-300 text-primary-600"
                  />
                  <span className="ml-3">
                    <span className="font-medium">Использовать видеостоки</span>
                    <span className="block text-sm text-gray-500">Pexels, Pixabay — бесплатные видео</span>
                  </span>
                </label>

                {useStockFootage && (
                  <div className="mt-3">
                    <label className="label">Поисковый запрос для стоков</label>
                    <input
                      type="text"
                      value={stockSearchQuery}
                      onChange={(e) => setStockSearchQuery(e.target.value)}
                      placeholder="Например: technology, business meeting, nature..."
                      className="input"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Publishing */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Send className="w-5 h-5 mr-2 text-blue-500" />
            Публикация
          </h2>

          <label className="flex items-center mb-4 cursor-pointer">
            <input
              type="checkbox"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              className="w-5 h-5 rounded border-gray-300 text-primary-600"
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
          <li>Claude напишет вирусный сценарий {useCustomScript && '(или использует ваш текст)'}</li>
          <li>ElevenLabs озвучит текст естественным голосом</li>
          {(videoType === 'avatar_inserts' || videoType === 'images_slideshow') && (
            <li>AI сгенерирует изображения для каждой сцены</li>
          )}
          {videoType.includes('avatar') && <li>HeyGen создаст видео с аватаром</li>}
          <li>Автоматически добавятся субтитры</li>
          {autoPublish && <li>Видео опубликуется на выбранных платформах</li>}
        </ol>
      </div>
    </div>
  )
}
