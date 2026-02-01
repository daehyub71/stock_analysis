import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, X, ArrowUpDown, Search } from 'lucide-react'
import { stockApi, analysisApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, formatNumber, formatPercent, getGradeColor, getGradeBgColor, getPriceChangeColor } from '@/lib/utils'
import type { Stock, AnalysisResult } from '@/types'

interface StockWithAnalysis extends Stock {
  analysis: AnalysisResult
}

const MAX_COMPARE_STOCKS = 4

export default function ComparePage() {
  const [selectedCodes, setSelectedCodes] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  // 전체 종목 리스트 조회
  const { data: stocksData, isLoading: stocksLoading } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  // 선택된 종목들의 분석 결과 조회
  const { data: comparisonData, isLoading: comparisonLoading } = useQuery({
    queryKey: ['comparison', selectedCodes],
    queryFn: async () => {
      const results = await Promise.all(
        selectedCodes.map(async (code) => {
          const stock = stocksData?.items.find((s) => s.code === code)
          const analysis = await analysisApi.getAnalysis(code)
          return { ...stock, analysis } as StockWithAnalysis
        })
      )
      return results
    },
    enabled: selectedCodes.length > 0 && !!stocksData,
  })

  const isLoading = stocksLoading

  if (isLoading) {
    return <LoadingPage />
  }

  const allStocks = stocksData?.items || []
  const filteredStocks = allStocks.filter(
    (stock) =>
      !selectedCodes.includes(stock.code) &&
      (stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.code.includes(searchQuery))
  )

  const addStock = (code: string) => {
    if (selectedCodes.length < MAX_COMPARE_STOCKS && !selectedCodes.includes(code)) {
      setSelectedCodes([...selectedCodes, code])
    }
    setShowSearch(false)
    setSearchQuery('')
  }

  const removeStock = (code: string) => {
    setSelectedCodes(selectedCodes.filter((c) => c !== code))
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">종목 비교</h1>
          <p className="text-gray-500 mt-1">최대 {MAX_COMPARE_STOCKS}개 종목을 비교할 수 있습니다</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">
            {selectedCodes.length}/{MAX_COMPARE_STOCKS} 종목 선택됨
          </span>
        </div>
      </div>

      {/* Stock Selection */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">비교할 종목 선택</h3>
        <div className="flex flex-wrap gap-3">
          {/* Selected Stocks */}
          {selectedCodes.map((code) => {
            const stock = allStocks.find((s) => s.code === code)
            return (
              <div
                key={code}
                className="flex items-center gap-2 px-3 py-2 bg-primary-50 text-primary-700 rounded-lg"
              >
                <span className="font-medium">{stock?.name || code}</span>
                <span className="text-sm text-primary-500">{code}</span>
                <button
                  onClick={() => removeStock(code)}
                  className="p-0.5 hover:bg-primary-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )
          })}

          {/* Add Button */}
          {selectedCodes.length < MAX_COMPARE_STOCKS && (
            <div className="relative">
              <button
                onClick={() => setShowSearch(!showSearch)}
                className="flex items-center gap-2 px-3 py-2 border-2 border-dashed border-gray-300 text-gray-500 rounded-lg hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>종목 추가</span>
              </button>

              {/* Search Dropdown */}
              {showSearch && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-3 border-b border-gray-100">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="종목명 또는 코드 검색..."
                        className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        autoFocus
                      />
                    </div>
                  </div>
                  <div className="max-h-60 overflow-y-auto">
                    {filteredStocks.slice(0, 10).map((stock) => (
                      <button
                        key={stock.code}
                        onClick={() => addStock(stock.code)}
                        className="w-full px-4 py-2.5 text-left hover:bg-gray-50 flex items-center justify-between"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{stock.name}</p>
                          <p className="text-xs text-gray-500">{stock.code}</p>
                        </div>
                        <span className="text-xs text-gray-400">{stock.market}</span>
                      </button>
                    ))}
                    {filteredStocks.length === 0 && (
                      <p className="px-4 py-3 text-sm text-gray-500 text-center">
                        검색 결과가 없습니다
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Comparison Table */}
      {selectedCodes.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {comparisonLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-500">분석 데이터를 불러오는 중...</p>
            </div>
          ) : comparisonData ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                      항목
                    </th>
                    {comparisonData.map((stock) => (
                      <th
                        key={stock.code}
                        className="px-6 py-4 text-center text-sm font-medium text-gray-900 min-w-40"
                      >
                        <div>{stock.name}</div>
                        <div className="text-xs text-gray-500 font-normal">{stock.code}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {/* 현재가 */}
                  <CompareRow label="현재가">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <span className="font-mono font-medium text-gray-900">
                          {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}
                        </span>
                        <span className="text-gray-500">원</span>
                      </td>
                    ))}
                  </CompareRow>

                  {/* 등락률 */}
                  <CompareRow label="등락률">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <span
                          className={cn(
                            'font-mono font-medium',
                            getPriceChangeColor(stock.priceChangeRate || 0)
                          )}
                        >
                          {stock.priceChangeRate !== undefined
                            ? formatPercent(stock.priceChangeRate)
                            : '-'}
                        </span>
                      </td>
                    ))}
                  </CompareRow>

                  {/* 총점 */}
                  <CompareRow label="총점" highlight>
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <span className="text-2xl font-bold text-gray-900">
                          {stock.analysis.totalScore.toFixed(1)}
                        </span>
                        <span className="text-gray-400">/100</span>
                      </td>
                    ))}
                  </CompareRow>

                  {/* 등급 */}
                  <CompareRow label="등급" highlight>
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <span
                          className={cn(
                            'inline-block px-3 py-1 text-sm font-bold rounded',
                            getGradeBgColor(stock.analysis.grade),
                            getGradeColor(stock.analysis.grade)
                          )}
                        >
                          {stock.analysis.grade}
                        </span>
                      </td>
                    ))}
                  </CompareRow>

                  {/* 기술분석 */}
                  <CompareRow label="기술분석" subLabel="30점 만점">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <ScoreBar
                          score={stock.analysis.scoreBreakdown.technical.score}
                          max={30}
                          color="blue"
                        />
                      </td>
                    ))}
                  </CompareRow>

                  {/* 기본분석 */}
                  <CompareRow label="기본분석" subLabel="50점 만점">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <ScoreBar
                          score={stock.analysis.scoreBreakdown.fundamental.score}
                          max={50}
                          color="green"
                        />
                      </td>
                    ))}
                  </CompareRow>

                  {/* 감정분석 */}
                  <CompareRow label="감정분석" subLabel="20점 만점">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <ScoreBar
                          score={stock.analysis.scoreBreakdown.sentiment.score}
                          max={20}
                          color="purple"
                        />
                      </td>
                    ))}
                  </CompareRow>

                  {/* Separator */}
                  <tr>
                    <td colSpan={comparisonData.length + 1} className="bg-gray-50 h-2" />
                  </tr>

                  {/* 기술지표 세부 */}
                  <CompareRow label="MA 배열" section="기술">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.technical.details?.maArrangement?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/6</span>
                      </td>
                    ))}
                  </CompareRow>

                  <CompareRow label="RSI" section="기술">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.technical.details?.rsi?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/5</span>
                      </td>
                    ))}
                  </CompareRow>

                  <CompareRow label="MACD" section="기술">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.technical.details?.macd?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/5</span>
                      </td>
                    ))}
                  </CompareRow>

                  {/* 기본분석 세부 */}
                  <CompareRow label="PER" section="기본">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.fundamental.details?.per?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/8</span>
                      </td>
                    ))}
                  </CompareRow>

                  <CompareRow label="PBR" section="기본">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.fundamental.details?.pbr?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/7</span>
                      </td>
                    ))}
                  </CompareRow>

                  <CompareRow label="ROE" section="기본">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-3 text-center">
                        <span className="text-sm">
                          {stock.analysis.details.fundamental.details?.roe?.score?.toFixed(1) || '-'}
                        </span>
                        <span className="text-xs text-gray-400">/5</span>
                      </td>
                    ))}
                  </CompareRow>
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      )}

      {/* Empty State */}
      {selectedCodes.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <ArrowUpDown className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">종목을 선택해주세요</h3>
          <p className="text-gray-500">
            위의 "종목 추가" 버튼을 클릭하여 비교할 종목을 선택하세요
          </p>
        </div>
      )}
    </div>
  )
}

// Helper Components
interface CompareRowProps {
  label: string
  subLabel?: string
  section?: string
  highlight?: boolean
  children: React.ReactNode
}

function CompareRow({ label, subLabel, section, highlight, children }: CompareRowProps) {
  return (
    <tr className={highlight ? 'bg-primary-50/50' : ''}>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          {section && (
            <span className="text-xs text-gray-400">{section}</span>
          )}
          <span className={cn('font-medium', highlight ? 'text-gray-900' : 'text-gray-700')}>
            {label}
          </span>
        </div>
        {subLabel && <p className="text-xs text-gray-400 mt-0.5">{subLabel}</p>}
      </td>
      {children}
    </tr>
  )
}

interface ScoreBarProps {
  score: number
  max: number
  color: 'blue' | 'green' | 'purple' | 'orange'
}

function ScoreBar({ score, max, color }: ScoreBarProps) {
  const percentage = (score / max) * 100
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-center gap-2 mb-1">
        <span className="font-medium text-gray-900">{score.toFixed(1)}</span>
        <span className="text-xs text-gray-400">/{max}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full', colorClasses[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
