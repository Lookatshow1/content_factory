'use client'

import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Eye, ThumbsUp, MessageCircle, Share } from 'lucide-react'
import { api } from '@/lib/api'

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({
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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-1">
          Track performance across all platforms
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Published"
          value={stats?.total_published || 0}
          icon={Share}
          color="blue"
        />
        <StatCard
          title="Total Views"
          value={(stats?.total_views || 0).toLocaleString()}
          icon={Eye}
          color="green"
        />
        <StatCard
          title="Total Likes"
          value={(stats?.total_likes || 0).toLocaleString()}
          icon={ThumbsUp}
          color="pink"
        />
        <StatCard
          title="Total Comments"
          value={(stats?.total_comments || 0).toLocaleString()}
          icon={MessageCircle}
          color="yellow"
        />
      </div>

      {/* Platform Breakdown */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Performance by Platform</h2>
        </div>
        <div className="p-6">
          {!stats?.by_platform || Object.keys(stats.by_platform).length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No publishing data yet. Start publishing videos to see analytics.
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(stats.by_platform).map(([platform, data]: [string, any]) => (
                <PlatformRow
                  key={platform}
                  platform={platform}
                  data={data}
                  maxViews={Math.max(
                    ...Object.values(stats.by_platform).map((d: any) => d.views || 0)
                  )}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="mt-8 card p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
          Growth Tips
        </h2>
        <ul className="space-y-3 text-gray-600">
          <li className="flex items-start">
            <span className="text-green-500 mr-2">1.</span>
            Post consistently at the same time each day for best engagement
          </li>
          <li className="flex items-start">
            <span className="text-green-500 mr-2">2.</span>
            Use trending topics and hashtags relevant to your niche
          </li>
          <li className="flex items-start">
            <span className="text-green-500 mr-2">3.</span>
            Hook viewers in the first 3 seconds with a strong opening
          </li>
          <li className="flex items-start">
            <span className="text-green-500 mr-2">4.</span>
            Cross-post to all platforms to maximize reach
          </li>
          <li className="flex items-start">
            <span className="text-green-500 mr-2">5.</span>
            Analyze which topics perform best and double down on them
          </li>
        </ul>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color }: {
  title: string
  value: string | number
  icon: any
  color: 'blue' | 'green' | 'pink' | 'yellow'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    pink: 'bg-pink-50 text-pink-600',
    yellow: 'bg-yellow-50 text-yellow-600',
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

const PLATFORM_ICONS: Record<string, string> = {
  youtube: '📺',
  tiktok: '🎵',
  instagram: '📷',
  vk: '💬',
  telegram: '✈️',
}

function PlatformRow({
  platform,
  data,
  maxViews,
}: {
  platform: string
  data: { count: number; views: number; likes: number }
  maxViews: number
}) {
  const percentage = maxViews > 0 ? (data.views / maxViews) * 100 : 0

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <span className="text-2xl mr-3">{PLATFORM_ICONS[platform]}</span>
          <div>
            <p className="font-medium capitalize">{platform}</p>
            <p className="text-sm text-gray-500">{data.count} videos</p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-bold">{data.views?.toLocaleString()} views</p>
          <p className="text-sm text-gray-500">{data.likes?.toLocaleString()} likes</p>
        </div>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-600 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
