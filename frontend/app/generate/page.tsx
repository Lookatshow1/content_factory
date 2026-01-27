'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Zap, Wand2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

const VIDEO_TYPES = [
  { id: 'avatar', name: 'AI Avatar', description: 'Talking head with HeyGen' },
  { id: 'ai_generated', name: 'AI Video', description: 'Generated with Kling AI' },
]

const NICHES = [
  'technology',
  'business',
  'finance',
  'health',
  'education',
  'entertainment',
  'lifestyle',
  'science',
]

const STYLES = [
  'educational',
  'entertaining',
  'motivational',
  'news',
  'tutorial',
  'storytelling',
]

const PLATFORMS = [
  { id: 'youtube', name: 'YouTube Shorts', icon: '📺' },
  { id: 'tiktok', name: 'TikTok', icon: '🎵' },
  { id: 'instagram', name: 'Instagram Reels', icon: '📷' },
  { id: 'vk', name: 'VK Clips', icon: '💬' },
  { id: 'telegram', name: 'Telegram', icon: '✈️' },
]

export default function GeneratePage() {
  const router = useRouter()
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('technology')
  const [style, setStyle] = useState('educational')
  const [videoType, setVideoType] = useState('avatar')
  const [duration, setDuration] = useState(45)
  const [autoPublish, setAutoPublish] = useState(true)
  const [platforms, setPlatforms] = useState(['youtube', 'tiktok', 'vk', 'telegram'])

  const { data: voices } = useQuery({
    queryKey: ['voices'],
    queryFn: () => api.get('/api/v1/system/voices').then(r => r.data.voices),
  })

  const { data: avatars } = useQuery({
    queryKey: ['avatars'],
    queryFn: () => api.get('/api/v1/system/avatars').then(r => r.data.avatars),
  })

  const [voiceId, setVoiceId] = useState('')
  const [avatarId, setAvatarId] = useState('')

  const generateMutation = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/videos/generate', data),
    onSuccess: (response) => {
      toast.success('Video generation started!')
      router.push(`/videos`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start generation')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) {
      toast.error('Please enter a topic')
      return
    }

    generateMutation.mutate({
      topic,
      niche,
      style,
      video_type: videoType,
      duration_seconds: duration,
      voice_id: voiceId || undefined,
      avatar_id: avatarId || undefined,
      auto_publish: autoPublish,
      platforms,
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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Zap className="w-8 h-8 mr-3 text-primary-600" />
          Generate Video
        </h1>
        <p className="text-gray-600 mt-1">
          Create a new video automatically with AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Topic */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Content</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Topic *</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., How AI is changing the world in 2025"
                className="input"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Describe what the video should be about
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Niche</label>
                <select
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="input"
                >
                  {NICHES.map(n => (
                    <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1)}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Style</label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="input"
                >
                  {STYLES.map(s => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Video Type */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Video Type</h2>

          <div className="grid grid-cols-2 gap-4">
            {VIDEO_TYPES.map(type => (
              <button
                key={type.id}
                type="button"
                onClick={() => setVideoType(type.id)}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  videoType === type.id
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-medium">{type.name}</h3>
                <p className="text-sm text-gray-500">{type.description}</p>
              </button>
            ))}
          </div>

          <div className="mt-4">
            <label className="label">Duration (seconds)</label>
            <input
              type="range"
              min="15"
              max="60"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-500">
              <span>15s</span>
              <span className="font-medium">{duration}s</span>
              <span>60s</span>
            </div>
          </div>

          {/* Voice selection */}
          {voices && (
            <div className="mt-4">
              <label className="label">Voice</label>
              <select
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
                className="input"
              >
                <option value="">Default (Rachel)</option>
                {voices.map((voice: any) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name} ({voice.gender})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Avatar selection for avatar type */}
          {videoType === 'avatar' && avatars && (
            <div className="mt-4">
              <label className="label">Avatar</label>
              <select
                value={avatarId}
                onChange={(e) => setAvatarId(e.target.value)}
                className="input"
              >
                <option value="">Default (Angela)</option>
                {avatars.map((avatar: any) => (
                  <option key={avatar.id} value={avatar.id}>
                    {avatar.name} - {avatar.style}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Publishing */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Publishing</h2>

          <div className="flex items-center mb-4">
            <input
              type="checkbox"
              id="autoPublish"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="autoPublish" className="ml-2 text-gray-700">
              Auto-publish when ready
            </label>
          </div>

          {autoPublish && (
            <div>
              <label className="label mb-2">Platforms</label>
              <div className="flex flex-wrap gap-2">
                {PLATFORMS.map(platform => (
                  <button
                    key={platform.id}
                    type="button"
                    onClick={() => togglePlatform(platform.id)}
                    className={`px-4 py-2 rounded-lg border transition-colors ${
                      platforms.includes(platform.id)
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
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
            className="btn-primary px-8 py-3 text-lg"
          >
            {generateMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
                Starting...
              </>
            ) : (
              <>
                <Wand2 className="w-5 h-5 mr-2" />
                Generate Video
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
