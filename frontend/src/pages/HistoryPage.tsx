import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, RefreshCw, Search } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { stockApi, analysisApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, getGradeColor, getGradeBgColor } from '@/lib/utils'

interface HistoryItem {
  date: string
  score: number
}

const PERIOD_OPTIONS = [
  { label: '7일', value: 7 },
  { label: '30일', value: 30 },
  { label: '90일', value: 90 },
  { label: '1년', value: 365 },
]

export default function HistoryPage() {
  const [selectedStock, setSelectedStock] = useState<string>('')
  const [period, setPeriod] = useState(30)
  const [searchQuery, setSearchQuery] = useState('')

  // 전체 종목 리스트 조회
  const { data: stocksData, isLoading: stocksLoading } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  // 선택된 종목의 히스토리 조회
  const {
    data: historyData,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['history', selectedStock, period],
    queryFn: () => analysisApi.getHistory(selectedStock, period),
    enabled: !!selectedStock,
  })

  // 전체 포트폴리오 히스토리 (평균 점수)
  const { data: portfolioHistory } = useQuery({
    queryKey: ['portfolioHistory', period],
    queryFn: async () => {
      // 모의 데이터 생성 (실제로는 API에서 가져옴)
      const baseDate = new Date()
      const history: { date: string; avgScore: number; topScore: number; bottomScore: number }[] = []
      let baseScore = 55

      for (let i = period; i >= 0; i--) {
        const date = new Date(baseDate)
        date.setDate(date.getDate() - i)
        baseScore += (Math.random() - 0.5) * 2
        baseScore = Math.max(40, Math.min(70, baseScore))

        history.push({
          date: date.toISOString().split('T')[0],
          avgScore: Math.round(baseScore * 10) / 10,
          topScore: Math.round((baseScore + 15 + Math.random() * 5) * 10) / 10,
          bottomScore: Math.round((baseScore - 15 - Math.random() * 5) * 10) / 10,
        })
      }

      return history
    },
  })

  const isLoading = stocksLoading

  if (isLoading) {
    return <LoadingPage />
  }

  const allStocks = stocksData?.items || []
  const filteredStocks = allStocks.filter(
    (stock) =>
      stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.code.includes(searchQuery)
  )

  // 히스토리 통계 계산
  const calculateStats = (history: HistoryItem[]) => {
    if (!history || history.length === 0) return null
    const scores = history.map((h) => h.score)
    return {
      current: scores[scores.length - 1],
      change: scores[scores.length - 1] - scores[0],
      avg: scores.reduce((a, b) => a + b, 0) / scores.length,
      max: Math.max(...scores),
      min: Math.min(...scores),
    }
  }

  const stats = historyData ? calculateStats(historyData) : null

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">분석 히스토리</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">시간에 따른 분석 점수 변화를 확인하세요</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Period Selector */}
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPeriod(opt.value)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-md transition-colors',
                  period === opt.value
                    ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Portfolio Overview Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">포트폴리오 점수 추이</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">VIP한국형가치투자 전체 종목 평균</p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary-500" />
              <span className="text-gray-600 dark:text-gray-400">평균 점수</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="text-gray-600 dark:text-gray-400">최고 점수</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <span className="text-gray-600 dark:text-gray-400">최저 점수</span>
            </div>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={portfolioHistory || []}>
              <defs>
                <linearGradient id="avgGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
              <YAxis
                domain={[30, 80]}
                tick={{ fontSize: 12, fill: '#6b7280' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                formatter={(value: number) => [value.toFixed(1) + '점', '']}
                labelFormatter={(label) => new Date(label).toLocaleDateString('ko-KR')}
              />
              <Area
                type="monotone"
                dataKey="topScore"
                stroke="#22c55e"
                strokeWidth={1}
                fill="transparent"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="avgScore"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#avgGradient)"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="bottomScore"
                stroke="#ef4444"
                strokeWidth={1}
                fill="transparent"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stock Selector */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">종목 선택</h3>

          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="종목명 또는 코드..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            />
          </div>

          {/* Stock List */}
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {filteredStocks.map((stock) => (
              <button
                key={stock.code}
                onClick={() => setSelectedStock(stock.code)}
                className={cn(
                  'w-full px-3 py-2.5 text-left rounded-lg transition-colors',
                  selectedStock === stock.code
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{stock.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{stock.code}</p>
                  </div>
                  {stock.analysis && (
                    <span
                      className={cn(
                        'text-xs px-2 py-0.5 rounded font-medium',
                        getGradeBgColor(stock.analysis.grade),
                        getGradeColor(stock.analysis.grade)
                      )}
                    >
                      {stock.analysis.grade}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* History Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          {selectedStock ? (
            <>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {allStocks.find((s) => s.code === selectedStock)?.name || selectedStock}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{selectedStock}</p>
                </div>
                <button
                  onClick={() => refetchHistory()}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {/* Stats Cards */}
              {stats && (
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">현재 점수</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.current.toFixed(1)}</p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">기간 변화</p>
                    <p
                      className={cn(
                        'text-xl font-bold',
                        stats.change >= 0 ? 'text-green-600' : 'text-red-600'
                      )}
                    >
                      {stats.change >= 0 ? '+' : ''}
                      {stats.change.toFixed(1)}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">평균</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.avg.toFixed(1)}</p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">최고/최저</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                      <span className="text-green-600">{stats.max.toFixed(1)}</span>
                      <span className="text-gray-400 mx-1">/</span>
                      <span className="text-red-600">{stats.min.toFixed(1)}</span>
                    </p>
                  </div>
                </div>
              )}

              {/* Chart */}
              {historyLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
                </div>
              ) : historyData ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={historyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        tickFormatter={(value) => {
                          const date = new Date(value)
                          return `${date.getMonth() + 1}/${date.getDate()}`
                        }}
                      />
                      <YAxis
                        domain={['dataMin - 5', 'dataMax + 5']}
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                        }}
                        formatter={(value: number) => [value.toFixed(1) + '점', '점수']}
                        labelFormatter={(label) => new Date(label).toLocaleDateString('ko-KR')}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={{ fill: '#6366f1', strokeWidth: 0, r: 3 }}
                        activeDot={{ r: 5, fill: '#6366f1' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
                  데이터를 불러올 수 없습니다
                </div>
              )}

              {/* History Table */}
              {historyData && historyData.length > 0 && (
                <div className="mt-6 border-t border-gray-100 dark:border-gray-700 pt-6">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">상세 히스토리</h4>
                  <div className="max-h-48 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                          <th className="pb-2 font-medium">날짜</th>
                          <th className="pb-2 font-medium text-right">점수</th>
                          <th className="pb-2 font-medium text-right">변화</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
                        {historyData.slice().reverse().map((item, idx, arr) => {
                          const prevScore = arr[idx + 1]?.score || item.score
                          const change = item.score - prevScore
                          return (
                            <tr key={item.date}>
                              <td className="py-2 text-gray-700 dark:text-gray-300">
                                {new Date(item.date).toLocaleDateString('ko-KR')}
                              </td>
                              <td className="py-2 text-right font-medium text-gray-900 dark:text-gray-100">
                                {item.score.toFixed(1)}
                              </td>
                              <td
                                className={cn(
                                  'py-2 text-right font-medium',
                                  change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-400'
                                )}
                              >
                                {change !== 0 && (change > 0 ? '+' : '')}
                                {change.toFixed(1)}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
              <Calendar className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
              <p>왼쪽에서 종목을 선택해주세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
