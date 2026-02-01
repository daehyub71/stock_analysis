import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronUp, Sparkles, TrendingUp, AlertTriangle, Loader2 } from 'lucide-react'
import { analysisApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface AnalysisCommentaryProps {
  stockCode: string
  stockName?: string
  className?: string
}

export default function AnalysisCommentary({ stockCode, className }: AnalysisCommentaryProps) {
  const [expanded, setExpanded] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['commentary', stockCode],
    queryFn: () => analysisApi.getCommentary(stockCode),
    enabled: !!stockCode,
    staleTime: 1000 * 60 * 5, // 5분 캐시
  })

  if (isLoading) {
    return (
      <div className={cn('bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6', className)}>
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
          <span className="text-gray-600">AI 분석 코멘트 생성 중...</span>
        </div>
      </div>
    )
  }

  if (error || !data?.commentary) {
    return null
  }

  const { commentary } = data

  return (
    <div className={cn('bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl overflow-hidden', className)}>
      {/* 헤더 */}
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-500">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-white" />
          <h3 className="text-lg font-semibold text-white">AI 종합 분석</h3>
        </div>
      </div>

      {/* 요약 */}
      <div className="p-6">
        <p className="text-gray-700 leading-relaxed">{commentary.summary}</p>

        {/* 투자 제안 */}
        <div className="mt-4 p-4 bg-white/70 rounded-lg border border-indigo-100">
          <p className="text-sm font-medium text-indigo-700">{commentary.action_suggestion}</p>
        </div>

        {/* 강점/리스크 요약 (항상 표시) */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          {/* 강점 */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-700">강점</span>
            </div>
            <ul className="space-y-1">
              {commentary.highlights.slice(0, expanded ? undefined : 2).map((item, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-1.5">
                  <span className="text-green-500 mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
              {!expanded && commentary.highlights.length > 2 && (
                <li className="text-xs text-gray-400">+{commentary.highlights.length - 2}개 더</li>
              )}
            </ul>
          </div>

          {/* 리스크 */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm font-medium text-red-700">리스크</span>
            </div>
            <ul className="space-y-1">
              {commentary.risks.slice(0, expanded ? undefined : 2).map((item, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-1.5">
                  <span className="text-red-500 mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
              {!expanded && commentary.risks.length > 2 && (
                <li className="text-xs text-gray-400">+{commentary.risks.length - 2}개 더</li>
              )}
            </ul>
          </div>
        </div>

        {/* 상세 분석 (펼쳤을 때만) */}
        {expanded && (
          <div className="mt-6 space-y-4 pt-4 border-t border-indigo-100">
            {/* 기술분석 코멘트 */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">📊 기술분석</h4>
              <p className="text-sm text-gray-600 bg-white/50 rounded-lg p-3">
                {commentary.technical_comment}
              </p>
            </div>

            {/* 기본분석 코멘트 */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">📈 기본분석</h4>
              <p className="text-sm text-gray-600 bg-white/50 rounded-lg p-3">
                {commentary.fundamental_comment}
              </p>
            </div>

            {/* 감정분석 코멘트 */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">💬 감정분석</h4>
              <p className="text-sm text-gray-600 bg-white/50 rounded-lg p-3">
                {commentary.sentiment_comment}
              </p>
            </div>
          </div>
        )}

        {/* 더보기/접기 버튼 */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-4 w-full flex items-center justify-center gap-1 py-2 text-sm text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          {expanded ? (
            <>
              <span>접기</span>
              <ChevronUp className="w-4 h-4" />
            </>
          ) : (
            <>
              <span>상세 분석 보기</span>
              <ChevronDown className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}
