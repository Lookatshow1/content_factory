'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Video, Play, Trash2, RefreshCw, Share2, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import Link from 'next/link'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  generating_script: 'Generating Script',
  script_ready: 'Script Ready',
  generating_audio: 'Generating Audio',
  audio_ready: 'Audio Ready',
  generating_video: 'Generating Video',
  video_ready: 'Video Ready',
  adding_subtitles: 'Adding Subtitles',
  rendering: 'Rendering',
  completed: 'Completed',
  failed: 'Failed',
}

export default function VideosPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['videos', page],
    queryFn: () => api.get(`/api/v1/videos?page=${page}&per_page=10`).then(r => r.data),
    refetchInterval: 5000, // Refresh every 5 seconds to see progress
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/videos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      toast.success('Video deleted')
    },
    onError: () => toast.error('Failed to delete video'),
  })

  const regenerateMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/videos/${id}/regenerate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      toast.success('Regeneration started')
    },
    onError: () => toast.error('Failed to regenerate'),
  })

  const publishMutation = useMutation({
    mutationFn: (videoId: number) => api.post('/api/v1/publishing/publish', {
      video_id: videoId,
      platforms: ['youtube', 'tiktok', 'vk', 'telegram'],
    }),
    onSuccess: () => {
      toast.success('Publishing started')
    },
    onError: () => toast.error('Failed to publish'),
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
          <h1 className="text-3xl font-bold text-gray-900">Videos</h1>
          <p className="text-gray-600 mt-1">
            Manage your generated videos
          </p>
        </div>
        <Link href="/generate" className="btn-primary">
          Generate New
        </Link>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Video</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Topic</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Type</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-500">Created</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No videos yet. Start by generating your first video!
                  </td>
                </tr>
              )}
              {data?.items?.map((video: any) => (
                <tr key={video.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-16 h-24 bg-gray-200 rounded-lg mr-4 flex items-center justify-center overflow-hidden">
                        {video.thumbnail_path ? (
                          <img
                            src={`/media/${video.thumbnail_path}`}
                            alt={video.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Video className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 line-clamp-1">{video.title}</p>
                        <p className="text-sm text-gray-500">{video.duration_seconds}s</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-900">{video.topic || '-'}</span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={video.status} />
                    {video.error_message && (
                      <p className="text-xs text-red-600 mt-1 line-clamp-1">
                        {video.error_message}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="capitalize">{video.video_type}</span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(video.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end space-x-2">
                      {video.status === 'completed' && (
                        <>
                          <button
                            onClick={() => window.open(`/media/${video.video_final_path}`, '_blank')}
                            className="p-2 text-gray-400 hover:text-gray-600"
                            title="Preview"
                          >
                            <Play className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => publishMutation.mutate(video.id)}
                            className="p-2 text-gray-400 hover:text-primary-600"
                            title="Publish"
                          >
                            <Share2 className="w-5 h-5" />
                          </button>
                        </>
                      )}
                      {video.status === 'failed' && (
                        <button
                          onClick={() => regenerateMutation.mutate(video.id)}
                          className="p-2 text-gray-400 hover:text-yellow-600"
                          title="Regenerate"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm('Delete this video?')) {
                            deleteMutation.mutate(video.id)
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-red-600"
                        title="Delete"
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
              Page {data.page} of {data.pages} ({data.total} videos)
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="btn-secondary"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const isProcessing = ['generating_script', 'generating_audio', 'generating_video', 'rendering', 'adding_subtitles'].includes(status)

  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    generating_script: 'bg-blue-100 text-blue-600',
    script_ready: 'bg-blue-100 text-blue-600',
    generating_audio: 'bg-blue-100 text-blue-600',
    audio_ready: 'bg-blue-100 text-blue-600',
    generating_video: 'bg-purple-100 text-purple-600',
    video_ready: 'bg-purple-100 text-purple-600',
    adding_subtitles: 'bg-yellow-100 text-yellow-600',
    rendering: 'bg-yellow-100 text-yellow-600',
    completed: 'bg-green-100 text-green-600',
    failed: 'bg-red-100 text-red-600',
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${styles[status] || styles.pending}`}>
      {isProcessing && (
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-2" />
      )}
      {STATUS_LABELS[status] || status}
    </span>
  )
}
