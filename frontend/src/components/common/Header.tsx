import { Link } from 'react-router-dom'
import { BarChart3, Search, Bell, Settings } from 'lucide-react'
import { useState } from 'react'
import { useStockStore } from '@/stores/useStockStore'
import { debounce } from '@/lib/utils'

export default function Header() {
  const [searchInput, setSearchInput] = useState('')
  const setSearchQuery = useStockStore((s) => s.setSearchQuery)

  const handleSearch = debounce((value: string) => {
    setSearchQuery(value)
  }, 300)

  const onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchInput(value)
    handleSearch(value)
  }

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <BarChart3 className="w-8 h-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">
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
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
            <Bell className="w-5 h-5" />
          </button>
          <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
            <Settings className="w-5 h-5" />
          </button>
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-primary-600">VIP</span>
          </div>
        </div>
      </div>
    </header>
  )
}
