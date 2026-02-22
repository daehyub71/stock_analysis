import { Link } from 'react-router-dom'
import { BarChart3, Search, Bell, Sun, Moon, Monitor } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useStockStore } from '@/stores/useStockStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { alertsApi } from '@/services/api'
import { debounce } from '@/lib/utils'

export default function Header() {
  const [searchInput, setSearchInput] = useState('')
  const setSearchQuery = useStockStore((s) => s.setSearchQuery)
  const { mode, setMode } = useThemeStore()

  // 점수 변화 개수 조회 (bell badge)
  const { data: alertData } = useQuery({
    queryKey: ['scoreChanges'],
    queryFn: () => alertsApi.getScoreChanges(5),
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60 * 5,
  })
  const alertCount = alertData?.count || 0

  const handleSearch = debounce((value: string) => {
    setSearchQuery(value)
  }, 300)

  const onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchInput(value)
    handleSearch(value)
  }

  const cycleTheme = () => {
    const next = mode === 'light' ? 'dark' : mode === 'dark' ? 'system' : 'light'
    setMode(next)
  }

  const ThemeIcon = mode === 'light' ? Sun : mode === 'dark' ? Moon : Monitor

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 z-50 transition-colors">
      <div className="flex items-center justify-between h-full px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <BarChart3 className="w-8 h-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
            종목분석 대시보드
          </span>
        </Link>

        {/* Search */}
        <div className="flex-1 max-w-xl mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchInput}
              onChange={onSearchChange}
              placeholder="종목명 또는 종목코드 검색..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button
            onClick={cycleTheme}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            title={`테마: ${mode === 'light' ? '라이트' : mode === 'dark' ? '다크' : '시스템'}`}
          >
            <ThemeIcon className="w-5 h-5" />
          </button>
          <Link
            to="/settings"
            className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <Bell className="w-5 h-5" />
            {alertCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                {alertCount > 9 ? '9+' : alertCount}
              </span>
            )}
          </Link>
          <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/40 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-primary-600 dark:text-primary-400">VIP</span>
          </div>
        </div>
      </div>
    </header>
  )
}
