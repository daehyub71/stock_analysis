import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Trophy, Medal } from 'lucide-react'
import { stockApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, formatNumber, formatPercent, getGradeColor, getGradeBgColor, getPriceChangeColor } from '@/lib/utils'
import type { Stock, AnalysisResult } from '@/types'

interface StockWithAnalysis extends Stock {
  analysis: AnalysisResult
}

type RankingCategory = 'total' | 'technical' | 'fundamental' | 'sentiment' | 'momentum'

export default function RankingPage() {
  const [category, setCategory] = useState<RankingCategory>('total')

  // 종목 데이터 조회
  const { data: stocksData, isLoading } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  if (isLoading) {
    return <LoadingPage />
  }

  const allStocks = (stocksData?.items || []) as StockWithAnalysis[]

  // 카테고리별 정렬
  const getSortedStocks = (cat: RankingCategory) => {
    return [...allStocks].sort((a, b) => {
      switch (cat) {
        case 'total':
          return (b.analysis?.totalScore || 0) - (a.analysis?.totalScore || 0)
        case 'technical':
          return (
            (b.analysis?.scoreBreakdown?.technical?.score || 0) -
            (a.analysis?.scoreBreakdown?.technical?.score || 0)
          )
        case 'fundamental':
          return (
            (b.analysis?.scoreBreakdown?.fundamental?.score || 0) -
            (a.analysis?.scoreBreakdown?.fundamental?.score || 0)
          )
        case 'sentiment':
          return (
            (b.analysis?.scoreBreakdown?.sentiment?.score || 0) -
            (a.analysis?.scoreBreakdown?.sentiment?.score || 0)
          )
        case 'momentum':
          return (b.priceChangeRate || 0) - (a.priceChangeRate || 0)
        default:
          return 0
      }
    })
  }

  const sortedStocks = getSortedStocks(category)
  const top3 = sortedStocks.slice(0, 3)
  const rest = sortedStocks.slice(3)

  const getCategoryLabel = (cat: RankingCategory) => {
    const labels: Record<RankingCategory, string> = {
      total: '종합 점수',
      technical: '기술분석',
      fundamental: '기본분석',
      sentiment: '감정분석',
      momentum: '등락률',
    }
    return labels[cat]
  }

  const getScore = (stock: StockWithAnalysis, cat: RankingCategory) => {
    switch (cat) {
      case 'total':
        return stock.analysis?.totalScore || 0
      case 'technical':
        return stock.analysis?.scoreBreakdown?.technical?.score || 0
      case 'fundamental':
        return stock.analysis?.scoreBreakdown?.fundamental?.score || 0
      case 'sentiment':
        return stock.analysis?.scoreBreakdown?.sentiment?.score || 0
      case 'momentum':
        return stock.priceChangeRate || 0
      default:
        return 0
    }
  }

  const getMaxScore = (cat: RankingCategory) => {
    switch (cat) {
      case 'total':
        return 100
      case 'technical':
        return 30
      case 'fundamental':
        return 50
      case 'sentiment':
        return 20
      case 'momentum':
        return null
      default:
        return 100
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">순위</h1>
          <p className="text-gray-500 mt-1">분석 점수 기준 종목 순위</p>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(['total', 'technical', 'fundamental', 'sentiment', 'momentum'] as RankingCategory[]).map(
          (cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors',
                category === cat
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {getCategoryLabel(cat)}
            </button>
          )
        )}
      </div>

      {/* Top 3 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {top3.map((stock, idx) => (
          <Link
            key={stock.code}
            to={`/stocks/${stock.code}`}
            className={cn(
              'relative p-6 rounded-xl border-2 transition-transform hover:scale-105',
              idx === 0
                ? 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-300'
                : idx === 1
                ? 'bg-gradient-to-br from-gray-50 to-slate-100 border-gray-300'
                : 'bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200'
            )}
          >
            {/* Rank Badge */}
            <div
              className={cn(
                'absolute -top-3 -left-3 w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-lg',
                idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : 'bg-orange-400'
              )}
            >
              {idx + 1}
            </div>

            {/* Content */}
            <div className="mt-2">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-bold text-gray-900">{stock.name}</h3>
                  <p className="text-sm text-gray-500">{stock.code}</p>
                </div>
                {stock.analysis && (
                  <span
                    className={cn(
                      'px-2 py-1 text-sm font-bold rounded',
                      getGradeBgColor(stock.analysis.grade),
                      getGradeColor(stock.analysis.grade)
                    )}
                  >
                    {stock.analysis.grade}
                  </span>
                )}
              </div>

              <div className="flex items-end justify-between">
                <div>
                  <p className="text-sm text-gray-500">{getCategoryLabel(category)}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {category === 'momentum' ? (
                      <span className={getPriceChangeColor(getScore(stock, category))}>
                        {formatPercent(getScore(stock, category))}
                      </span>
                    ) : (
                      <>
                        {getScore(stock, category).toFixed(1)}
                        <span className="text-lg text-gray-400">
                          /{getMaxScore(category)}
                        </span>
                      </>
                    )}
                  </p>
                </div>
                {idx === 0 && <Trophy className="w-12 h-12 text-yellow-500" />}
                {idx === 1 && <Medal className="w-12 h-12 text-gray-400" />}
                {idx === 2 && <Medal className="w-12 h-12 text-orange-400" />}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Ranking Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-16">
                순위
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                종목
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                현재가
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                등락률
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                등급
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                {getCategoryLabel(category)}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rest.map((stock, idx) => (
              <tr key={stock.code} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <span className="w-8 h-8 inline-flex items-center justify-center bg-gray-100 rounded-full text-sm font-medium text-gray-600">
                    {idx + 4}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link
                    to={`/stocks/${stock.code}`}
                    className="block hover:text-primary-600"
                  >
                    <p className="font-medium text-gray-900">{stock.name}</p>
                    <p className="text-xs text-gray-500">{stock.code}</p>
                  </Link>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="font-mono text-gray-900">
                    {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={cn(
                      'font-mono',
                      getPriceChangeColor(stock.priceChangeRate || 0)
                    )}
                  >
                    {stock.priceChangeRate !== undefined
                      ? formatPercent(stock.priceChangeRate)
                      : '-'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {stock.analysis && (
                    <span
                      className={cn(
                        'px-2 py-0.5 text-xs font-bold rounded',
                        getGradeBgColor(stock.analysis.grade),
                        getGradeColor(stock.analysis.grade)
                      )}
                    >
                      {stock.analysis.grade}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {category === 'momentum' ? (
                    <span
                      className={cn(
                        'font-bold',
                        getPriceChangeColor(getScore(stock, category))
                      )}
                    >
                      {formatPercent(getScore(stock, category))}
                    </span>
                  ) : (
                    <span className="font-bold text-gray-900">
                      {getScore(stock, category).toFixed(1)}
                      <span className="text-gray-400 font-normal">
                        /{getMaxScore(category)}
                      </span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
