'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Video,
  Calendar,
  Share2,
  Settings,
  Zap,
  BarChart3
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Главная', href: '/', icon: LayoutDashboard },
  { name: 'Видео', href: '/videos', icon: Video },
  { name: 'Создать', href: '/generate', icon: Zap },
  { name: 'Контент-планы', href: '/plans', icon: Calendar },
  { name: 'Публикации', href: '/publishing', icon: Share2 },
  { name: 'Аналитика', href: '/analytics', icon: BarChart3 },
  { name: 'Настройки', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-800">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
          <Zap className="w-6 h-6 text-white" />
        </div>
        <div className="ml-3">
          <span className="text-lg font-bold">Content Factory</span>
          <span className="block text-xs text-gray-400">AI Video Generator</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-4 py-3 rounded-lg transition-all',
                isActive
                  ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/30'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <item.icon className={clsx(
                'w-5 h-5 mr-3',
                isActive && 'text-white'
              )} />
              {item.name}
              {item.href === '/generate' && (
                <span className="ml-auto text-xs bg-primary-500 px-2 py-0.5 rounded-full">
                  AI
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Quick Stats */}
      <div className="p-4 mx-4 mb-4 bg-gray-800 rounded-xl">
        <div className="text-xs text-gray-400 mb-2">Быстрая статистика</div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <div className="text-gray-400">Видео</div>
            <div className="font-bold text-white">—</div>
          </div>
          <div>
            <div className="text-gray-400">Опубликовано</div>
            <div className="font-bold text-white">—</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center text-sm text-gray-400">
          <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse" />
          Система активна
        </div>
      </div>
    </aside>
  )
}
