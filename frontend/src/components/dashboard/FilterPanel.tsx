import { useState } from 'react'
import { Filter, X, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Grade } from '@/types'
import { useStockStore } from '@/stores/useStockStore'

interface FilterPanelProps {
  sectors: string[]
}

const GRADES: Grade[] = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']

export default function FilterPanel({ sectors }: FilterPanelProps) {
  const { filter, setFilter, resetFilter } = useStockStore()
  const [isExpanded, setIsExpanded] = useState(false)

  const hasActiveFilters = Object.values(filter).some(
    (v) => v !== undefined && v !== false && v !== 'all' && (!Array.isArray(v) || v.length > 0)
  )

  const handleGradeToggle = (grade: Grade) => {
    const currentGrades = filter.grades || []
    const newGrades = currentGrades.includes(grade)
      ? currentGrades.filter((g) => g !== grade)
      : [...currentGrades, grade]
    setFilter({ grades: newGrades.length > 0 ? newGrades : undefined })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
        >
          <Filter className="w-5 h-5" />
          <span className="font-medium">필터</span>
          {hasActiveFilters && (
            <span className="px-1.5 py-0.5 text-xs bg-primary-100 dark:bg-primary-900/40 text-primary-700 rounded">
              적용됨
            </span>
          )}
          <ChevronDown
            className={cn('w-4 h-4 transition-transform', isExpanded && 'rotate-180')}
          />
        </button>
        {hasActiveFilters && (
          <button
            onClick={resetFilter}
            className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <X className="w-4 h-4" />
            초기화
          </button>
        )}
      </div>

      {/* Filters */}
      {isExpanded && (
        <div className="space-y-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          {/* Market Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">시장</label>
            <div className="flex gap-2">
              {(['all', 'KOSPI', 'KOSDAQ'] as const).map((market) => (
                <button
                  key={market}
                  onClick={() => setFilter({ market })}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-lg transition-colors',
                    filter.market === market
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  )}
                >
                  {market === 'all' ? '전체' : market}
                </button>
              ))}
            </div>
          </div>

          {/* Sector Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">업종</label>
            <select
              value={filter.sector || ''}
              onChange={(e) => setFilter({ sector: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm
                       dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">전체 업종</option>
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector}
                </option>
              ))}
            </select>
          </div>

          {/* Grade Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">등급</label>
            <div className="flex flex-wrap gap-2">
              {GRADES.map((grade) => (
                <button
                  key={grade}
                  onClick={() => handleGradeToggle(grade)}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-lg transition-colors',
                    filter.grades?.includes(grade)
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  )}
                >
                  {grade}
                </button>
              ))}
            </div>
          </div>

          {/* Score Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">점수 범위</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={0}
                max={100}
                placeholder="최소"
                value={filter.minScore ?? ''}
                onChange={(e) =>
                  setFilter({ minScore: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm
                         dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <span className="text-gray-400">~</span>
              <input
                type="number"
                min={0}
                max={100}
                placeholder="최대"
                value={filter.maxScore ?? ''}
                onChange={(e) =>
                  setFilter({ maxScore: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm
                         dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Exclude Loss */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="excludeLoss"
              checked={filter.excludeLoss || false}
              onChange={(e) => setFilter({ excludeLoss: e.target.checked })}
              className="w-4 h-4 text-primary-600 border-gray-300 dark:border-gray-600 rounded
                       dark:bg-gray-700 focus:ring-primary-500"
            />
            <label htmlFor="excludeLoss" className="text-sm text-gray-700 dark:text-gray-300">
              적자 기업 제외
            </label>
          </div>
        </div>
      )}
    </div>
  )
}
