import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  PlayCircle,
  Search,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Target,
  Loader2,
} from 'lucide-react'
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
  ReferenceLine,
} from 'recharts'
import { stockApi, backtestApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, formatNumber, formatPercent } from '@/lib/utils'
import type { BacktestResponse } from '@/types'

export default function BacktestingPage() {
  const [selectedStock, setSelectedStock] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')

  // 파라미터
  const [startDate, setStartDate] = useState('2025-06-01')
  const [endDate, setEndDate] = useState('2026-02-01')
  const [initialCapital, setInitialCapital] = useState(10_000_000)
  const [buyThreshold, setBuyThreshold] = useState(20)
  const [sellThreshold, setSellThreshold] = useState(12)

  // 결과
  const [result, setResult] = useState<BacktestResponse | null>(null)

  // 종목 리스트
  const { data: stocksData, isLoading: stocksLoading } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  // 선택 종목의 데이터 기간 조회
  const { data: dateRange } = useQuery({
    queryKey: ['backtest-date-range', selectedStock],
    queryFn: () => backtestApi.getDateRange(selectedStock),
    enabled: !!selectedStock,
  })

  // 백테스트 실행
  const backtestMutation = useMutation({
    mutationFn: () =>
      backtestApi.runBacktest(selectedStock, {
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        buy_threshold: buyThreshold,
        sell_threshold: sellThreshold,
      }),
    onSuccess: (data) => {
      setResult(data)
    },
  })

  const stocks = stocksData?.items || []
  const filteredStocks = stocks.filter(
    (s) =>
      s.name.includes(searchQuery) || s.code.includes(searchQuery)
  )

  const handleRun = () => {
    if (!selectedStock) return
    backtestMutation.mutate()
  }

  const handleSelectStock = (code: string) => {
    setSelectedStock(code)
    setResult(null)
  }

  if (stocksLoading) return <LoadingPage />

  const metrics = result?.metrics
  const benchmark = result?.benchmark

  // Buy&Hold 곡선 계산
  const chartData = result?.dailyData?.map((d) => {
    const firstPrice = result.dailyData[0]?.price || 1
    const buyHoldValue = Math.round(
      (initialCapital / firstPrice) * d.price
    )
    return {
      ...d,
      buyHoldValue,
    }
  })

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">백테스팅</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          기술분석 점수 기반 매수/매도 시뮬레이션 (기술분석 30점 기준)
        </p>
      </div>

      {/* 상단: 종목 선택 + 파라미터 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 종목 선택 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">종목 선택</h3>
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="종목명/코드 검색"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            />
          </div>
          <div className="max-h-[280px] overflow-y-auto space-y-0.5">
            {filteredStocks.map((stock) => (
              <button
                key={stock.code}
                onClick={() => handleSelectStock(stock.code)}
                className={cn(
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                  selectedStock === stock.code
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 font-medium'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                )}
              >
                <span className="font-medium">{stock.name}</span>
                <span className="text-gray-400 ml-1 text-xs">{stock.code}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 파라미터 설정 */}
        <div className="lg:col-span-3 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">전략 파라미터</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">시작일</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">종료일</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">초기 투자금</label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                step={1000000}
                min={1000000}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                매수 기준 ({buyThreshold}/30)
              </label>
              <input
                type="range"
                min={5}
                max={30}
                value={buyThreshold}
                onChange={(e) => setBuyThreshold(Number(e.target.value))}
                className="w-full mt-2"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                매도 기준 ({sellThreshold}/30)
              </label>
              <input
                type="range"
                min={0}
                max={30}
                value={sellThreshold}
                onChange={(e) => setSellThreshold(Number(e.target.value))}
                className="w-full mt-2"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleRun}
                disabled={!selectedStock || backtestMutation.isPending}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {backtestMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <PlayCircle className="w-4 h-4" />
                )}
                <span>{backtestMutation.isPending ? '실행 중...' : '백테스트 실행'}</span>
              </button>
            </div>
          </div>
          {dateRange && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
              {dateRange.stockName} 데이터 기간: {dateRange.startDate} ~ {dateRange.endDate}
            </p>
          )}
          {backtestMutation.isError && (
            <p className="text-xs text-red-500 mt-2">
              오류: {(backtestMutation.error as Error)?.message || '백테스트 실행 실패'}
            </p>
          )}
        </div>
      </div>

      {/* 결과가 없으면 안내 */}
      {!result && !backtestMutation.isPending && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>종목을 선택하고 파라미터를 설정한 후 백테스트를 실행하세요</p>
        </div>
      )}

      {/* 결과 표시 */}
      {result && metrics && (
        <>
          {/* 성과 지표 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <MetricCard
              label="총 수익률"
              value={formatPercent(metrics.totalReturn)}
              positive={metrics.totalReturn >= 0}
              icon={<TrendingUp className="w-4 h-4" />}
            />
            <MetricCard
              label="연환산 수익률"
              value={formatPercent(metrics.annualizedReturn)}
              positive={metrics.annualizedReturn >= 0}
              icon={<BarChart3 className="w-4 h-4" />}
            />
            <MetricCard
              label="MDD"
              value={`-${metrics.maxDrawdown.toFixed(1)}%`}
              positive={false}
              icon={<TrendingDown className="w-4 h-4" />}
            />
            <MetricCard
              label="샤프비율"
              value={metrics.sharpeRatio.toFixed(2)}
              positive={metrics.sharpeRatio > 0}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              label="승률"
              value={`${metrics.winRate.toFixed(0)}%`}
              positive={metrics.winRate >= 50}
              icon={<Target className="w-4 h-4" />}
            />
            <MetricCard
              label="매매 횟수"
              value={`${metrics.tradeCount}회`}
              neutral
            />
            <MetricCard
              label="최종 자산"
              value={`${formatNumber(metrics.finalValue)}원`}
              positive={metrics.finalValue > initialCapital}
            />
            <MetricCard
              label="vs Buy&Hold"
              value={formatPercent(benchmark?.buyHoldReturn || 0)}
              positive={(benchmark?.buyHoldReturn || 0) >= 0}
              highlight
            />
          </div>

          {/* 수익률 곡선 차트 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              포트폴리오 가치 추이
              <span className="font-normal text-gray-400 ml-2">
                {result.stockName} ({result.stockCode})
              </span>
            </h3>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <defs>
                  <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(d) => d.slice(5)}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${(v / 10000).toFixed(0)}만`}
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `${formatNumber(value)}원`,
                    name === 'portfolioValue' ? '전략' : 'Buy&Hold',
                  ]}
                  labelFormatter={(label) => `날짜: ${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="portfolioValue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#portfolioGradient)"
                  name="portfolioValue"
                />
                <Line
                  type="monotone"
                  dataKey="buyHoldValue"
                  stroke="#9ca3af"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                  name="buyHoldValue"
                />
                <ReferenceLine
                  y={initialCapital}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{ value: '초기자본', position: 'left', fill: '#ef4444', fontSize: 11 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* 기술분석 점수 차트 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">기술분석 점수 추이 (30점 만점)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={result.dailyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(d) => d.slice(5)}
                />
                <YAxis domain={[0, 30]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)}점`, '기술분석']}
                  labelFormatter={(label) => `날짜: ${label}`}
                />
                <ReferenceLine
                  y={buyThreshold}
                  stroke="#22c55e"
                  strokeDasharray="3 3"
                  label={{ value: `매수 ${buyThreshold}`, position: 'right', fill: '#22c55e', fontSize: 10 }}
                />
                <ReferenceLine
                  y={sellThreshold}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{ value: `매도 ${sellThreshold}`, position: 'right', fill: '#ef4444', fontSize: 10 }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 매매 내역 테이블 */}
          {result.trades.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  매매 내역 ({result.trades.length}건)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">구분</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">날짜</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">가격</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">수량</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">점수</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">포트폴리오</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">수익률</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {result.trades.map((trade, i) => (
                      <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded text-xs font-medium',
                              trade.type === 'buy'
                                ? 'bg-red-50 text-red-600'
                                : 'bg-blue-50 text-blue-600'
                            )}
                          >
                            {trade.type === 'buy' ? '매수' : '매도'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{trade.date}</td>
                        <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                          {formatNumber(trade.price)}원
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                          {formatNumber(trade.shares)}주
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                          {trade.score.toFixed(1)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                          {formatNumber(trade.portfolioValue)}원
                        </td>
                        <td className="px-4 py-3 text-right">
                          {trade.profitPct !== undefined ? (
                            <span
                              className={cn(
                                'font-medium',
                                trade.profitPct >= 0 ? 'text-red-500' : 'text-blue-500'
                              )}
                            >
                              {formatPercent(trade.profitPct)}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// 지표 카드 컴포넌트
function MetricCard({
  label,
  value,
  positive,
  neutral,
  icon,
  highlight,
}: {
  label: string
  value: string
  positive?: boolean
  neutral?: boolean
  icon?: React.ReactNode
  highlight?: boolean
}) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-4',
        highlight ? 'border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-900/30' : 'border-gray-100 dark:border-gray-700'
      )}
    >
      <div className="flex items-center gap-1.5 mb-1">
        {icon && <span className="text-gray-400">{icon}</span>}
        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <div
        className={cn(
          'text-lg font-bold',
          neutral
            ? 'text-gray-700 dark:text-gray-300'
            : positive
              ? 'text-red-500'
              : 'text-blue-500'
        )}
      >
        {value}
      </div>
    </div>
  )
}
