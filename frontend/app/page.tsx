'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Video,
  Upload,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  Eye,
  ThumbsUp
} from 'lucide-react'
import { api } from '@/lib/api'
import Link from 'next/link'

export default function Dashboard() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get('/api/v1/system/status').then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: videos } = useQuery({
    queryKey: ['recent-videos'],
    queryFn: () => api.get('/api/v1/videos?per_page=5').then(r => r.data),
  })

  const { data: publishingStats } = useQuery({
    queryKey: ['publishing-stats'],
    queryFn: () => api.get('/api/v1/publishing/stats').then(r => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  const videoStats = status?.statistics?.videos || {}
  const isConfigured = status?.ready

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Automated video production pipeline
        </p>
      </div>

      {/* Configuration Alert */}
      {!isConfigured && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3" />
          <div>
            <h3 className="font-medium text-yellow-800">Configuration Required</h3>
            <p className="text-sm text-yellow-700 mt-1">
              Some API keys are missing. Go to{' '}
              <Link href="/settings" className="underline">Settings</Link>
              {' '}to configure your services.
            </p>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Videos"
          value={Object.values(videoStats).reduce((a: number, b: any) => a + (b || 0), 0)}
          icon={Video}
          color="blue"
        />
        <StatCard
          title="Completed"
          value={videoStats.completed || 0}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Processing"
          value={
            (videoStats.generating_script || 0) +
            (videoStats.generating_audio || 0) +
            (videoStats.generating_video || 0) +
            (videoStats.rendering || 0)
          }
          icon={Clock}
          color="yellow"
        />
        <StatCard
          title="Published"
          value={publishingStats?.total_published || 0}
          icon={Upload}
          color="purple"
        />
      </div>

      {/* Publishing Stats */}
      {publishingStats && publishingStats.total_published > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="Total Views"
            value={publishingStats.total_views?.toLocaleString() || 0}
            icon={Eye}
            color="blue"
          />
          <StatCard
            title="Total Likes"
            value={publishingStats.total_likes?.toLocaleString() || 0}
            icon={ThumbsUp}
            color="pink"
          />
          <StatCard
            title="Engagement Rate"
            value={
              publishingStats.total_views > 0
                ? `${((publishingStats.total_likes / publishingStats.total_views) * 100).toFixed(1)}%`
                : '0%'
            }
            icon={TrendingUp}
            color="green"
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              href="/generate"
              className="btn-primary w-full justify-center"
            >
              Generate New Video
            </Link>
            <Link
              href="/plans"
              className="btn-secondary w-full justify-center"
            >
              Create Content Plan
            </Link>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">API Status</h2>
          <div className="space-y-2">
            {Object.entries(status?.configuration?.ai_services || {}).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="capitalize">{key.replace('_', ' ')}</span>
                <span className={value ? 'text-green-600' : 'text-gray-400'}>
                  {value ? 'Connected' : 'Not configured'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Videos */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Videos</h2>
            <Link href="/videos" className="text-primary-600 hover:underline text-sm">
              View all
            </Link>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {videos?.items?.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              No videos yet. Generate your first video!
            </div>
          )}
          {videos?.items?.map((video: any) => (
            <div key={video.id} className="p-4 flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-16 h-28 bg-gray-200 rounded-lg mr-4 flex items-center justify-center">
                  {video.thumbnail_path ? (
                    <img
                      src={`/media/${video.thumbnail_path}`}
                      alt={video.title}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    <Video className="w-6 h-6 text-gray-400" />
                  )}
                </div>
                <div>
                  <h3 className="font-medium">{video.title}</h3>
                  <p className="text-sm text-gray-500">{video.topic}</p>
                </div>
              </div>
              <StatusBadge status={video.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color }: {
  title: string
  value: number | string
  icon: any
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'pink'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
    pink: 'bg-pink-50 text-pink-600',
  }

  return (
    <div className="card p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    generating_script: 'bg-blue-100 text-blue-600',
    generating_audio: 'bg-blue-100 text-blue-600',
    generating_video: 'bg-blue-100 text-blue-600',
    rendering: 'bg-yellow-100 text-yellow-600',
    completed: 'bg-green-100 text-green-600',
    failed: 'bg-red-100 text-red-600',
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm ${styles[status] || styles.pending}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
