import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronUp, ChevronDown, Check, Info } from 'lucide-react'
import { cn, formatNumber, formatPercent, getGradeColor, getGradeBgColor, getPriceChangeColor } from '@/lib/utils'
import type { Stock, AnalysisResult, SortOption } from '@/types'
import { useStockStore } from '@/stores/useStockStore'
import AnalysisDetailModal from './AnalysisDetailModal'

interface StockWithAnalysis extends Stock {
  analysis: AnalysisResult
}

interface StockTableProps {
  stocks: StockWithAnalysis[]
  isLoading?: boolean
  sort: SortOption
  onSort: (sort: SortOption) => void
}

type SortField = SortOption['field']

export default function StockTable({ stocks, isLoading, sort, onSort }: StockTableProps) {
  const { selectedStocks, toggleStock } = useStockStore()
  const [modalStock, setModalStock] = useState<{ code: string; name: string } | null>(null)

  const handleSort = (field: SortField) => {
    if (sort.field === field) {
      onSort({ field, direction: sort.direction === 'asc' ? 'desc' : 'asc' })
    } else {
      onSort({ field, direction: 'desc' })
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sort.field !== field) return null
    return sort.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    )
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th className="w-12 px-4 py-3">
                  <span className="sr-only">선택</span>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center gap-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    종목
                    <SortIcon field="name" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('sector')}
                    className="flex items-center gap-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    업종
                    <SortIcon field="sector" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    현재가
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleSort('priceChangeRate')}
                    className="flex items-center gap-1 ml-auto text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    등락률
                    <SortIcon field="priceChangeRate" />
                  </button>
                </th>
                <th className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleSort('totalScore')}
                    className="flex items-center gap-1 mx-auto text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    점수
                    <SortIcon field="totalScore" />
                  </button>
                </th>
                <th className="px-4 py-3 text-center">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    등급
                  </span>
                </th>
                <th className="px-4 py-3">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    점수 분포
                  </span>
                </th>
                <th className="w-12 px-4 py-3">
                  <span className="sr-only">상세</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {stocks.map((stock) => (
                <StockRow
                  key={stock.code}
                  stock={stock}
                  isSelected={selectedStocks.includes(stock.code)}
                  onSelect={() => toggleStock(stock.code)}
                  onShowDetail={() => setModalStock({ code: stock.code, name: stock.name })}
                />
              ))}
              {stocks.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    조건에 맞는 종목이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Analysis Detail Modal */}
      <AnalysisDetailModal
        isOpen={modalStock !== null}
        onClose={() => setModalStock(null)}
        stockCode={modalStock?.code || ''}
        stockName={modalStock?.name || ''}
      />
    </>
  )
}

interface StockRowProps {
  stock: StockWithAnalysis
  isSelected: boolean
  onSelect: () => void
  onShowDetail: () => void
}

function StockRow({ stock, isSelected, onSelect, onShowDetail }: StockRowProps) {
  const { analysis } = stock
  const breakdown = analysis.scoreBreakdown

  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
      {/* Checkbox */}
      <td className="px-4 py-3">
        <button
          onClick={(e) => {
            e.preventDefault()
            onSelect()
          }}
          className={cn(
            'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
            isSelected
              ? 'bg-primary-600 border-primary-600'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
          )}
        >
          {isSelected && <Check className="w-3 h-3 text-white" />}
        </button>
      </td>

      {/* Stock Info */}
      <td className="px-4 py-3">
        <Link to={`/stocks/${stock.code}`} className="block">
          <p className="font-medium text-gray-900 dark:text-gray-100 hover:text-primary-600">{stock.name}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{stock.code}</p>
        </Link>
      </td>

      {/* Sector */}
      <td className="px-4 py-3">
        <span className="text-sm text-gray-600 dark:text-gray-400">{stock.sector || '-'}</span>
      </td>

      {/* Current Price */}
      <td className="px-4 py-3 text-right">
        <span className="font-mono text-sm text-gray-900 dark:text-gray-100">
          {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}
        </span>
      </td>

      {/* Price Change */}
      <td className="px-4 py-3 text-right">
        {stock.priceChangeRate !== undefined ? (
          <span className={cn('font-mono text-sm', getPriceChangeColor(stock.priceChangeRate))}>
            {formatPercent(stock.priceChangeRate)}
          </span>
        ) : (
          <span className="text-gray-400 dark:text-gray-400">-</span>
        )}
      </td>

      {/* Total Score */}
      <td className="px-4 py-3 text-center">
        <span className="font-bold text-gray-900 dark:text-gray-100">{analysis.totalScore.toFixed(1)}</span>
      </td>

      {/* Grade */}
      <td className="px-4 py-3 text-center">
        <span
          className={cn(
            'inline-block px-2 py-0.5 text-xs font-bold rounded',
            getGradeBgColor(analysis.grade),
            getGradeColor(analysis.grade)
          )}
        >
          {analysis.grade}
        </span>
      </td>

      {/* Score Distribution */}
      <td className="px-4 py-3">
        <div className="flex gap-0.5 h-4">
          <div
            className="bg-blue-500 rounded-l"
            style={{ width: `${(breakdown.technical.score / 30) * 100}%` }}
            title={`기술: ${breakdown.technical.score}`}
          />
          <div
            className="bg-green-500"
            style={{ width: `${(breakdown.fundamental.score / 50) * 100}%` }}
            title={`기본: ${breakdown.fundamental.score}`}
          />
          <div
            className="bg-purple-500 rounded-r"
            style={{ width: `${(breakdown.sentiment.score / 20) * 100}%` }}
            title={`감정: ${breakdown.sentiment.score}`}
          />
        </div>
        <div className="flex justify-between mt-1 text-[10px] text-gray-400 dark:text-gray-400">
          <span>기술</span>
          <span>기본</span>
          <span>감정</span>
        </div>
      </td>

      {/* Detail Button */}
      <td className="px-4 py-3">
        <button
          onClick={(e) => {
            e.preventDefault()
            onShowDetail()
          }}
          className="p-1.5 text-gray-400 dark:text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="분석 상세 보기"
        >
          <Info className="w-4 h-4" />
        </button>
      </td>
    </tr>
  )
}
