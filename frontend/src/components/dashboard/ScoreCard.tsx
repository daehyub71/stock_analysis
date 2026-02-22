import { cn, getGradeColor, getGradeBgColor, getScoreColor } from '@/lib/utils'
import type { Grade } from '@/types'

interface ScoreCardProps {
  title: string
  score: number
  maxScore: number
  grade?: Grade
  description?: string
  showBar?: boolean
  className?: string
}

export default function ScoreCard({
  title,
  score,
  maxScore,
  grade,
  description,
  showBar = true,
  className,
}: ScoreCardProps) {
  const percentage = (score / maxScore) * 100

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700', className)}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
        {grade && (
          <span
            className={cn(
              'px-2 py-0.5 text-xs font-bold rounded',
              getGradeBgColor(grade),
              getGradeColor(grade)
            )}
          >
            {grade}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-1 mb-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{score.toFixed(1)}</span>
        <span className="text-sm text-gray-400">/ {maxScore}</span>
      </div>

      {showBar && (
        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-500', getScoreColor(score, maxScore))}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}

      {description && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{description}</p>
      )}
    </div>
  )
}

// 종합 점수 카드
interface TotalScoreCardProps {
  totalScore: number
  maxScore: number
  grade: Grade
  breakdown: {
    technical: number
    fundamental: number
    sentiment: number
  }
  sentimentSource?: 'manual' | 'auto'
}

export function TotalScoreCard({ totalScore, maxScore, grade, breakdown, sentimentSource }: TotalScoreCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">종합 점수</h2>
        <span
          className={cn(
            'px-3 py-1 text-lg font-bold rounded-lg',
            getGradeBgColor(grade),
            getGradeColor(grade)
          )}
        >
          {grade}
        </span>
      </div>

      <div className="flex items-baseline gap-2 mb-6">
        <span className="text-5xl font-bold text-gray-900 dark:text-gray-100">{totalScore.toFixed(1)}</span>
        <span className="text-xl text-gray-400">/ {maxScore}</span>
      </div>

      {/* Score breakdown */}
      <div className="space-y-3">
        <ScoreBreakdownItem label="기술분석" score={breakdown.technical} max={30} color="bg-blue-500" />
        <ScoreBreakdownItem label="기본분석" score={breakdown.fundamental} max={50} color="bg-green-500" />
        <ScoreBreakdownItem
          label="감정분석"
          score={breakdown.sentiment}
          max={20}
          color="bg-purple-500"
          badge={sentimentSource === 'manual' ? '수동' : undefined}
        />
      </div>
    </div>
  )
}

interface ScoreBreakdownItemProps {
  label: string
  score: number
  max: number
  color: string
  isNegative?: boolean
  badge?: string  // 배지 텍스트 (예: "수동")
}

function ScoreBreakdownItem({ label, score, max, color, isNegative, badge }: ScoreBreakdownItemProps) {
  const percentage = Math.abs(score) / max * 100

  return (
    <div className="flex items-center gap-3">
      <div className="w-20 flex items-center gap-1">
        <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
        {badge && (
          <span className="px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-700 rounded">
            {badge}
          </span>
        )}
      </div>
      <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full', color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={cn('w-16 text-sm text-right', isNegative ? 'text-red-500' : 'text-gray-700 dark:text-gray-300')}>
        {score.toFixed(1)} / {max}
      </span>
    </div>
  )
}
