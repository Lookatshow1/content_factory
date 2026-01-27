'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Trash2, Play, Pause, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

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
      toast.success('Plan deleted')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      api.post(`/api/v1/content-plans/${id}/${active ? 'activate' : 'deactivate'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] })
      toast.success('Plan updated')
    },
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
          <h1 className="text-3xl font-bold text-gray-900">Content Plans</h1>
          <p className="text-gray-600 mt-1">
            Automate video generation on a schedule
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-5 h-5 mr-2" />
          Create Plan
        </button>
      </div>

      {plans?.length === 0 && (
        <div className="card p-12 text-center">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No content plans yet</h3>
          <p className="text-gray-500 mb-6">
            Create a content plan to automatically generate videos on a schedule.
          </p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            Create Your First Plan
          </button>
        </div>
      )}

      <div className="grid gap-6">
        {plans?.map((plan: any) => (
          <div key={plan.id} className="card p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center">
                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  <span className={`ml-3 px-2 py-1 rounded-full text-xs ${
                    plan.is_active ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {plan.is_active ? 'Active' : 'Paused'}
                  </span>
                </div>
                <p className="text-gray-600 mt-1">{plan.description}</p>
              </div>
              <div className="flex items-center space-x-2">
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
                  title={plan.is_active ? 'Pause' : 'Activate'}
                >
                  {plan.is_active ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this plan?')) {
                      deleteMutation.mutate(plan.id)
                    }
                  }}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                  title="Delete"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Niche:</span>
                <span className="ml-2 font-medium capitalize">{plan.niche}</span>
              </div>
              <div>
                <span className="text-gray-500">Videos/week:</span>
                <span className="ml-2 font-medium">{plan.videos_per_week}</span>
              </div>
              <div>
                <span className="text-gray-500">Publish time:</span>
                <span className="ml-2 font-medium">{plan.publish_time}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-2 font-medium capitalize">{plan.video_type}</span>
              </div>
            </div>

            {plan.topics?.length > 0 && (
              <div className="mt-4">
                <span className="text-sm text-gray-500">Topics:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {plan.topics.map((topic: string, i: number) => (
                    <span key={i} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4">
              <span className="text-sm text-gray-500">Platforms:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {plan.platforms.map((platform: string) => (
                  <span key={platform} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm capitalize">
                    {platform}
                  </span>
                ))}
              </div>
            </div>

            {/* Scheduled items */}
            {plan.items?.filter((i: any) => !i.is_published).length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Upcoming</h4>
                <div className="space-y-2">
                  {plan.items
                    .filter((item: any) => !item.is_published)
                    .slice(0, 3)
                    .map((item: any) => (
                      <div key={item.id} className="flex items-center justify-between text-sm">
                        <span>{item.topic}</span>
                        <span className="text-gray-500">
                          {new Date(item.scheduled_date).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
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
      toast.success('Plan created!')
      onClose()
    },
    onError: () => toast.error('Failed to create plan'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      topics: form.topics.split('\n').filter(t => t.trim()),
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Create Content Plan</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="label">Plan Name</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="input"
              required
              placeholder="e.g., AI News Weekly"
            />
          </div>

          <div>
            <label className="label">Description</label>
            <textarea
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              className="input"
              rows={2}
              placeholder="Brief description of this content plan"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Niche</label>
              <select
                value={form.niche}
                onChange={e => setForm(f => ({ ...f, niche: e.target.value }))}
                className="input"
              >
                <option value="technology">Technology</option>
                <option value="business">Business</option>
                <option value="finance">Finance</option>
                <option value="health">Health</option>
                <option value="education">Education</option>
              </select>
            </div>
            <div>
              <label className="label">Videos per Week</label>
              <input
                type="number"
                min="1"
                max="21"
                value={form.videos_per_week}
                onChange={e => setForm(f => ({ ...f, videos_per_week: Number(e.target.value) }))}
                className="input"
              />
            </div>
          </div>

          <div>
            <label className="label">Topics (one per line)</label>
            <textarea
              value={form.topics}
              onChange={e => setForm(f => ({ ...f, topics: e.target.value }))}
              className="input"
              rows={4}
              placeholder="AI news and trends&#10;Machine learning tutorials&#10;Tech industry updates"
            />
            <p className="text-sm text-gray-500 mt-1">
              Videos will rotate through these topics
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Publish Time</label>
              <input
                type="time"
                value={form.publish_time}
                onChange={e => setForm(f => ({ ...f, publish_time: e.target.value }))}
                className="input"
              />
            </div>
            <div>
              <label className="label">Video Type</label>
              <select
                value={form.video_type}
                onChange={e => setForm(f => ({ ...f, video_type: e.target.value }))}
                className="input"
              >
                <option value="avatar">AI Avatar</option>
                <option value="ai_generated">AI Generated</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Plan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
