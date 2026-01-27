'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Share2, RefreshCw, ExternalLink, CheckCircle, XCircle, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

const PLATFORM_ICONS: Record<string, string> = {
  youtube: '📺',
  tiktok: '🎵',
  instagram: '📷',
  vk: '💬',
  telegram: '✈️',
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
      toast.success('Retrying...')
    },
    onError: () => toast.error('Failed to retry'),
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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Publishing</h1>
        <p className="text-gray-600 mt-1">
          Track and manage video publishing across platforms
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {Object.entries(stats.by_platform || {}).map(([platform, data]: [string, any]) => (
            <div key={platform} className="card p-4">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">{PLATFORM_ICONS[platform]}</span>
                <span className="font-medium capitalize">{platform}</span>
              </div>
              <div className="text-2xl font-bold">{data.count}</div>
              <div className="text-sm text-gray-500">{data.views?.toLocaleString()} views</div>
            </div>
          ))}
        </div>
      )}

      {/* Tasks Table */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold">Publishing Tasks</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Platform</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Video</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Published</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Stats</th>
                <th className="text-right px-6 py-3 text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tasks?.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No publishing tasks yet
                  </td>
                </tr>
              )}
              {tasks?.map((task: any) => (
                <tr key={task.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <span className="text-2xl mr-2">{PLATFORM_ICONS[task.platform]}</span>
                      <span className="capitalize">{task.platform}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-900">Video #{task.video_id}</span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={task.status} />
                    {task.error_message && (
                      <p className="text-xs text-red-600 mt-1 max-w-xs truncate">
                        {task.error_message}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {task.published_at
                      ? new Date(task.published_at).toLocaleString()
                      : '-'}
                  </td>
                  <td className="px-6 py-4">
                    {task.status === 'published' && (
                      <div className="text-sm">
                        <span className="text-gray-900">{task.views}</span>
                        <span className="text-gray-500"> views</span>
                        <span className="mx-1">·</span>
                        <span className="text-gray-900">{task.likes}</span>
                        <span className="text-gray-500"> likes</span>
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
                          className="p-2 text-gray-400 hover:text-primary-600"
                          title="Open"
                        >
                          <ExternalLink className="w-5 h-5" />
                        </a>
                      )}
                      {task.status === 'failed' && (
                        <button
                          onClick={() => retryMutation.mutate(task.id)}
                          className="p-2 text-gray-400 hover:text-yellow-600"
                          title="Retry"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: any; className: string; label: string }> = {
    pending: { icon: Clock, className: 'bg-gray-100 text-gray-600', label: 'Pending' },
    uploading: { icon: Clock, className: 'bg-blue-100 text-blue-600', label: 'Uploading' },
    processing: { icon: Clock, className: 'bg-yellow-100 text-yellow-600', label: 'Processing' },
    published: { icon: CheckCircle, className: 'bg-green-100 text-green-600', label: 'Published' },
    failed: { icon: XCircle, className: 'bg-red-100 text-red-600', label: 'Failed' },
    scheduled: { icon: Clock, className: 'bg-purple-100 text-purple-600', label: 'Scheduled' },
  }

  const { icon: Icon, className, label } = config[status] || config.pending

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${className}`}>
      <Icon className="w-4 h-4 mr-1" />
      {label}
    </span>
  )
}
