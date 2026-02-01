import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  PieChart,
  History,
  GitCompare,
  Settings,
  HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  { label: '대시보드', path: '/', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: '순위', path: '/ranking', icon: <TrendingUp className="w-5 h-5" /> },
  { label: '포트폴리오', path: '/portfolio', icon: <PieChart className="w-5 h-5" /> },
  { label: '히스토리', path: '/history', icon: <History className="w-5 h-5" /> },
  { label: '비교', path: '/compare', icon: <GitCompare className="w-5 h-5" /> },
]

const bottomItems: NavItem[] = [
  { label: '설정', path: '/settings', icon: <Settings className="w-5 h-5" /> },
  { label: '도움말', path: '/help', icon: <HelpCircle className="w-5 h-5" /> },
]

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <nav className="flex flex-col h-full p-4">
        {/* Main Navigation */}
        <div className="flex-1 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>

        {/* Divider */}
        <div className="my-4 border-t border-gray-200" />

        {/* Bottom Navigation */}
        <div className="space-y-1">
          {bottomItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>

        {/* Portfolio Info */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">분석 대상</p>
          <p className="text-sm font-medium text-gray-900">VIP한국형가치투자</p>
          <p className="text-xs text-gray-500">44개 종목</p>
        </div>
      </nav>
    </aside>
  )
}
