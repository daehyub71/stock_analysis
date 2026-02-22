import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'
import { toast } from 'sonner'
import { stockApi, alertsApi } from '@/services/api'
import { useStockStore } from '@/stores/useStockStore'
import { StockTable, FilterPanel } from '@/components/dashboard'
import { LoadingPage, ErrorDisplay } from '@/components/common'
import { sendBrowserNotification } from '@/lib/notifications'
import { cn, formatNumber } from '@/lib/utils'

export default function Dashboard() {
  const { filter, sort, setSort, page, pageSize, searchQuery } = useStockStore()
  const alertShown = useRef(false)

  // 종목 리스트 조회
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['stocks', filter, sort, page, pageSize, searchQuery],
    queryFn: () =>
      stockApi.getStocks({
        filter,
        sort,
        page,
        pageSize,
        search: searchQuery,
      }),
  })

  // 업종 목록 조회
  const { data: sectors = [] } = useQuery({
    queryKey: ['sectors'],
    queryFn: () => stockApi.getSectors(),
  })

  // 점수 변화 알림 (페이지 로드 시 1회)
  const { data: alertData } = useQuery({
    queryKey: ['scoreChanges'],
    queryFn: () => alertsApi.getScoreChanges(5),
    staleTime: 1000 * 60 * 5,
  })

  useEffect(() => {
    if (alertData && alertData.count > 0 && !alertShown.current) {
      alertShown.current = true
      const upCount = alertData.changes.filter(c => c.change > 0).length
      const downCount = alertData.changes.filter(c => c.change < 0).length
      toast.info(`점수 변화 알림: ${alertData.count}개 종목 (상승 ${upCount}, 하락 ${downCount})`)
      sendBrowserNotification(
        '종목분석 점수 변화',
        `${alertData.count}개 종목의 점수가 변화했습니다. (상승 ${upCount}, 하락 ${downCount})`
      )
    }
  }, [alertData])

  if (error) {
    return <ErrorDisplay error={error as Error} onRetry={() => refetch()} />
  }

  // 임시 통계 데이터 (실제로는 API에서 가져옴)
  const stats = {
    totalStocks: data?.total || 44,
    avgScore: 65.2,
    topGrade: 'A+',
    topGradeCount: 3,
    upCount: 28,
    downCount: 16,
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">대시보드</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">VIP한국형가치투자 포트폴리오 분석</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span>마지막 업데이트:</span>
          <span className="font-medium text-gray-700 dark:text-gray-300">
            {new Date().toLocaleDateString('ko-KR')}
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="분석 종목"
          value={formatNumber(stats.totalStocks)}
          suffix="개"
          icon={<BarChart3 className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="평균 점수"
          value={stats.avgScore.toFixed(1)}
          suffix="점"
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          title="상승 종목"
          value={formatNumber(stats.upCount)}
          suffix="개"
          icon={<TrendingUp className="w-5 h-5" />}
          color="red"
          change="+3"
        />
        <StatCard
          title="하락 종목"
          value={formatNumber(stats.downCount)}
          suffix="개"
          icon={<TrendingDown className="w-5 h-5" />}
          color="blue"
          change="-2"
        />
      </div>

      {/* Filter */}
      <FilterPanel sectors={sectors} />

      {/* Stock Table */}
      {isLoading ? (
        <LoadingPage />
      ) : (
        <StockTable
          stocks={data?.items || []}
          sort={sort}
          onSort={setSort}
          isLoading={isLoading}
        />
      )}

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={data.totalPages}
          onPageChange={(p) => useStockStore.getState().setPage(p)}
        />
      )}
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  title: string
  value: string
  suffix?: string
  icon: React.ReactNode
  color: 'blue' | 'green' | 'red' | 'amber'
  change?: string
}

function StatCard({ title, value, suffix, icon, color, change }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/30 text-blue-600',
    green: 'bg-green-50 dark:bg-green-900/30 text-green-600',
    red: 'bg-red-50 dark:bg-red-900/30 text-red-600',
    amber: 'bg-amber-50 dark:bg-amber-900/30 text-amber-600',
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-500 dark:text-gray-400">{title}</span>
        <div className={cn('p-2 rounded-lg', colorClasses[color])}>{icon}</div>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</span>
        {suffix && <span className="text-gray-500 dark:text-gray-400">{suffix}</span>}
      </div>
      {change && (
        <p
          className={cn(
            'mt-1 text-sm',
            change.startsWith('+') ? 'text-red-500' : 'text-blue-500'
          )}
        >
          전일 대비 {change}
        </p>
      )}
    </div>
  )
}

// Pagination Component
interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
  const visiblePages = pages.filter(
    (p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 2
  )

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        이전
      </button>

      {visiblePages.map((page, i) => {
        const prevPage = visiblePages[i - 1]
        const showEllipsis = prevPage && page - prevPage > 1

        return (
          <div key={page} className="flex items-center">
            {showEllipsis && <span className="px-2 text-gray-400">...</span>}
            <button
              onClick={() => onPageChange(page)}
              className={cn(
                'w-10 h-10 text-sm rounded-lg',
                currentPage === page
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              )}
            >
              {page}
            </button>
          </div>
        )
      })}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        다음
      </button>
    </div>
  )
}
