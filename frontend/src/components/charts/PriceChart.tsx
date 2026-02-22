import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { stockApi } from '@/services/api'
import { Loader2 } from 'lucide-react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface PriceChartProps {
  stockCode: string
  currentPrice?: number
  ma5?: number
  ma20?: number
  ma60?: number
  ma120?: number
}

interface ChartDataPoint {
  date: string
  close: number
  ma5?: number
  ma20?: number
  ma60?: number
  ma120?: number
}

// Calculate moving average
function calculateMA(data: number[], period: number): (number | undefined)[] {
  const result: (number | undefined)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(undefined)
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(Math.round(sum / period))
    }
  }
  return result
}

// Format date for display
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// Format price for tooltip
function formatPrice(value: number): string {
  return value.toLocaleString('ko-KR') + '원'
}

export default function PriceChart({
  stockCode,
  currentPrice,
  ma5,
  ma20,
  ma60,
  ma120,
}: PriceChartProps) {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const chartTheme = useChartTheme()

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch 1 year of price data (approximately 250 trading days)
        const prices = await stockApi.getPriceHistory(stockCode, 250)

        if (!prices || prices.length === 0) {
          setError('가격 데이터가 없습니다')
          return
        }

        // Prices come in reverse order (newest first), so reverse them
        const sortedPrices = [...prices].reverse()

        // Extract close prices for MA calculation
        const closePrices = sortedPrices.map(p => p.close)

        // Calculate MAs
        const ma5Values = calculateMA(closePrices, 5)
        const ma20Values = calculateMA(closePrices, 20)
        const ma60Values = calculateMA(closePrices, 60)
        const ma120Values = calculateMA(closePrices, 120)

        // Build chart data
        const data: ChartDataPoint[] = sortedPrices.map((price, index) => ({
          date: price.date,
          close: price.close,
          ma5: ma5Values[index],
          ma20: ma20Values[index],
          ma60: ma60Values[index],
          ma120: ma120Values[index],
        }))

        setChartData(data)
      } catch (err) {
        console.error('Price fetch error:', err)
        setError('가격 데이터를 불러오지 못했습니다')
      } finally {
        setLoading(false)
      }
    }

    if (stockCode) {
      fetchData()
    }
  }, [stockCode])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-500 dark:text-gray-400">차트 로딩중...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <span className="text-gray-500 dark:text-gray-400">{error}</span>
      </div>
    )
  }

  // Calculate Y-axis domain
  const allPrices = chartData.flatMap(d => [
    d.close,
    d.ma5,
    d.ma20,
    d.ma60,
    d.ma120,
  ].filter(v => v !== undefined)) as number[]

  const minPrice = Math.min(...allPrices) * 0.95
  const maxPrice = Math.max(...allPrices) * 1.05

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">📈 1년 주가 차트</h4>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-gray-700 dark:bg-gray-300"></span> 주가
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-red-400"></span> MA5
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-orange-400"></span> MA20
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-green-500"></span> MA60
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-500"></span> MA120
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 11, fill: chartTheme.textColor }}
            interval="preserveStartEnd"
            minTickGap={50}
          />
          <YAxis
            domain={[minPrice, maxPrice]}
            tickFormatter={(v) => (v / 1000).toFixed(0) + 'K'}
            tick={{ fontSize: 11, fill: chartTheme.textColor }}
            width={50}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              formatPrice(value),
              name === 'close' ? '종가' : name.toUpperCase(),
            ]}
            labelFormatter={(label) => `날짜: ${label}`}
            contentStyle={{ fontSize: 12, backgroundColor: chartTheme.tooltipBg, border: '1px solid ' + chartTheme.tooltipBorder, borderRadius: '8px' }}
          />

          {/* Current price reference line */}
          {currentPrice && (
            <ReferenceLine
              y={currentPrice}
              stroke="#6366f1"
              strokeDasharray="5 5"
              label={{
                value: `현재가 ${formatPrice(currentPrice)}`,
                position: 'right',
                fontSize: 10,
                fill: '#6366f1',
              }}
            />
          )}

          {/* MA lines (drawn first, so price line is on top) */}
          <Line
            type="monotone"
            dataKey="ma120"
            stroke="#3b82f6"
            strokeWidth={1}
            dot={false}
            name="MA120"
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma60"
            stroke="#22c55e"
            strokeWidth={1}
            dot={false}
            name="MA60"
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma20"
            stroke="#f97316"
            strokeWidth={1}
            dot={false}
            name="MA20"
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma5"
            stroke="#f87171"
            strokeWidth={1}
            dot={false}
            name="MA5"
            connectNulls={false}
          />

          {/* Price line (on top) */}
          <Line
            type="monotone"
            dataKey="close"
            stroke={chartTheme.priceStroke}
            strokeWidth={1.5}
            dot={false}
            name="close"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Current MA values from indicators */}
      {(ma5 || ma20 || ma60 || ma120) && (
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 bg-red-50 dark:bg-red-900/30 rounded">
              <span className="text-gray-500 dark:text-gray-400">MA5</span>
              <p className="font-medium text-red-600">
                {ma5 ? ma5.toLocaleString() : '-'}
              </p>
            </div>
            <div className="p-2 bg-orange-50 dark:bg-orange-900/30 rounded">
              <span className="text-gray-500 dark:text-gray-400">MA20</span>
              <p className="font-medium text-orange-600">
                {ma20 ? ma20.toLocaleString() : '-'}
              </p>
            </div>
            <div className="p-2 bg-green-50 dark:bg-green-900/30 rounded">
              <span className="text-gray-500 dark:text-gray-400">MA60</span>
              <p className="font-medium text-green-600">
                {ma60 ? ma60.toLocaleString() : '-'}
              </p>
            </div>
            <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded">
              <span className="text-gray-500 dark:text-gray-400">MA120</span>
              <p className="font-medium text-blue-600">
                {ma120 ? ma120.toLocaleString() : '-'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
