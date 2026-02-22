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

const MAX_COMPARE_STOCKS = 6

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">종목 비교</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">최대 {MAX_COMPARE_STOCKS}개 종목을 비교할 수 있습니다</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {selectedCodes.length}/{MAX_COMPARE_STOCKS} 종목 선택됨
          </span>
        </div>
      </div>

      {/* Stock Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">비교할 종목 선택</h3>
        <div className="flex flex-wrap gap-3">
          {/* Selected Stocks */}
          {selectedCodes.map((code) => {
            const stock = allStocks.find((s) => s.code === code)
            return (
              <div
                key={code}
                className="flex items-center gap-2 px-3 py-2 bg-primary-50 dark:bg-primary-900/30 text-primary-700 rounded-lg"
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
                className="flex items-center gap-2 px-3 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 rounded-lg hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>종목 추가</span>
              </button>

              {/* Search Dropdown */}
              {showSearch && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                  <div className="p-3 border-b border-gray-100 dark:border-gray-700">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="종목명 또는 코드 검색..."
                        className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
                        autoFocus
                      />
                    </div>
                  </div>
                  <div className="max-h-60 overflow-y-auto">
                    {filteredStocks.slice(0, 10).map((stock) => (
                      <button
                        key={stock.code}
                        onClick={() => addStock(stock.code)}
                        className="w-full px-4 py-2.5 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-between"
                      >
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">{stock.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{stock.code}</p>
                        </div>
                        <span className="text-xs text-gray-400">{stock.market}</span>
                      </button>
                    ))}
                    {filteredStocks.length === 0 && (
                      <p className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {comparisonLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">분석 데이터를 불러오는 중...</p>
            </div>
          ) : comparisonData ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-48">
                      항목
                    </th>
                    {comparisonData.map((stock) => (
                      <th
                        key={stock.code}
                        className="px-6 py-4 text-center text-sm font-medium text-gray-900 dark:text-gray-100 min-w-40"
                      >
                        <div>{stock.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 font-normal">{stock.code}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {/* 현재가 */}
                  <CompareRow label="현재가">
                    {comparisonData.map((stock) => (
                      <td key={stock.code} className="px-6 py-4 text-center">
                        <span className="font-mono font-medium text-gray-900 dark:text-gray-100">
                          {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400">원</span>
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
                        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
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

                  {/* Separator - 기본분석 지표 */}
                  <SectionHeader colSpan={comparisonData.length + 1} title="기본분석 지표" />

                  <CompareRow label="PER" subLabel="주가수익비율">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.per
                      const score = stock.analysis.details.fundamental.details?.per?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className="font-medium text-gray-900 dark:text-gray-100">{val != null ? val.toFixed(1) : '-'}배</div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/8</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="PBR" subLabel="주가순자산비율">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.pbr
                      const score = stock.analysis.details.fundamental.details?.pbr?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className="font-medium text-gray-900 dark:text-gray-100">{val != null ? val.toFixed(2) : '-'}배</div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/7</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="PSR" subLabel="주가매출비율">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.psr
                      const score = stock.analysis.details.fundamental.details?.psr?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className="font-medium text-gray-900 dark:text-gray-100">{val != null ? val.toFixed(2) : '-'}배</div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/5</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="ROE" subLabel="자기자본이익률">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.roe
                      const score = stock.analysis.details.fundamental.details?.roe?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val > 0 ? 'text-green-600' : val != null && val < 0 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(1) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/5</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="매출성장률" subLabel="전년 대비">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.revenueGrowth
                      const score = stock.analysis.details.fundamental.details?.revenueGrowth?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val > 0 ? 'text-green-600' : val != null && val < 0 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? (val > 0 ? '+' : '') + val.toFixed(1) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/6</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="영업이익성장률" subLabel="전년 대비">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.opGrowth
                      const score = stock.analysis.details.fundamental.details?.opGrowth?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val > 0 ? 'text-green-600' : val != null && val < 0 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? (val > 0 ? '+' : '') + val.toFixed(1) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/6</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="영업이익률" subLabel="수익성">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.opMargin
                      const score = stock.analysis.details.fundamental.details?.opMargin?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val >= 10 ? 'text-green-600' : val != null && val < 0 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(1) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/5</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="부채비율" subLabel="안정성">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.debtRatio
                      const score = stock.analysis.details.fundamental.details?.debtRatio?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val <= 100 ? 'text-green-600' : val != null && val > 200 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(0) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/4</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="유동비율" subLabel="안정성">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.fundamental.financials?.currentRatio
                      const score = stock.analysis.details.fundamental.details?.currentRatio?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val >= 150 ? 'text-green-600' : val != null && val < 100 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(0) : '-'}%
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/4</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  {/* Separator - 기술분석 지표 */}
                  <SectionHeader colSpan={comparisonData.length + 1} title="기술분석 지표" />

                  <CompareRow label="RSI(14)" subLabel="과매수/과매도">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.technical.indicators?.rsi14
                      const score = stock.analysis.details.technical.details?.rsi?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val >= 70 ? 'text-red-600' : val != null && val <= 30 ? 'text-green-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(1) : '-'}
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/5</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="MACD" subLabel="추세 강도">
                    {comparisonData.map((stock) => {
                      const macd = stock.analysis.details.technical.indicators?.macd
                      const signal = stock.analysis.details.technical.indicators?.macdSignal
                      const score = stock.analysis.details.technical.details?.macd?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium text-sm', macd != null && signal != null && macd > signal ? 'text-green-600' : 'text-red-600')}>
                            {macd != null ? macd.toFixed(0) : '-'}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">Signal {signal != null ? signal.toFixed(0) : '-'}</div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/5</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="MA 배열" subLabel="이동평균 추세">
                    {comparisonData.map((stock) => {
                      const ind = stock.analysis.details.technical.indicators
                      const score = stock.analysis.details.technical.details?.maArrangement?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                            <div>MA20 {ind?.ma20 ? formatNumber(ind.ma20) : '-'}</div>
                            <div>MA60 {ind?.ma60 ? formatNumber(ind.ma60) : '-'}</div>
                            <div>MA120 {ind?.ma120 ? formatNumber(ind.ma120) : '-'}</div>
                          </div>
                          <div className="text-xs text-gray-400 mt-1">점수 {score?.toFixed(1) || '-'}/6</div>
                        </td>
                      )
                    })}
                  </CompareRow>

                  <CompareRow label="거래량 비율" subLabel="20일 평균 대비">
                    {comparisonData.map((stock) => {
                      const val = stock.analysis.details.technical.indicators?.volumeRatio
                      const score = stock.analysis.details.technical.details?.volume?.score
                      return (
                        <td key={stock.code} className="px-6 py-3 text-center">
                          <div className={cn('font-medium', val != null && val >= 1.5 ? 'text-green-600' : val != null && val < 0.5 ? 'text-red-600' : 'text-gray-900 dark:text-gray-100')}>
                            {val != null ? val.toFixed(2) : '-'}배
                          </div>
                          <div className="text-xs text-gray-400">점수 {score?.toFixed(1) || '-'}/8</div>
                        </td>
                      )
                    })}
                  </CompareRow>
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      )}

      {/* Empty State */}
      {selectedCodes.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <ArrowUpDown className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">종목을 선택해주세요</h3>
          <p className="text-gray-500 dark:text-gray-400">
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
    <tr className={highlight ? 'bg-primary-50/50 dark:bg-primary-900/20' : ''}>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          {section && (
            <span className="text-xs text-gray-400">{section}</span>
          )}
          <span className={cn('font-medium', highlight ? 'text-gray-900 dark:text-gray-100' : 'text-gray-700 dark:text-gray-300')}>
            {label}
          </span>
        </div>
        {subLabel && <p className="text-xs text-gray-400 mt-0.5">{subLabel}</p>}
      </td>
      {children}
    </tr>
  )
}

function SectionHeader({ colSpan, title }: { colSpan: number; title: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="bg-gray-50 dark:bg-gray-700/50 px-6 py-2">
        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{title}</span>
      </td>
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
        <span className="font-medium text-gray-900 dark:text-gray-100">{score.toFixed(1)}</span>
        <span className="text-xs text-gray-400">/{max}</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full', colorClasses[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
