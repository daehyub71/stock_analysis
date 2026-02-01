import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  RefreshCw,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Minus,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { analysisApi } from '@/services/api'
import { cn } from '@/lib/utils'
import type { NewsItem } from '@/types'

interface NewsRatingProps {
  stockCode: string
  stockName?: string
  className?: string
}

export default function NewsRating({ stockCode, stockName, className }: NewsRatingProps) {
  const queryClient = useQueryClient()
  const [expandedNews, setExpandedNews] = useState<Set<number>>(new Set())

  // 뉴스 목록 조회
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['newsRating', stockCode],
    queryFn: () => analysisApi.getNewsList(stockCode),
    enabled: !!stockCode,
    staleTime: 1000 * 60 * 5,
  })

  // 뉴스 수집 mutation
  const collectMutation = useMutation({
    mutationFn: () => analysisApi.collectNews(stockCode, 30, 50),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['newsRating', stockCode] })
    },
  })

  // 평점 업데이트 mutation
  const rateMutation = useMutation({
    mutationFn: ({ newsId, rating }: { newsId: number; rating: number }) =>
      analysisApi.updateNewsRating(stockCode, newsId, rating),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['newsRating', stockCode] })
    },
  })

  const handleCollect = () => {
    collectMutation.mutate()
  }

  const handleRate = (newsId: number, rating: number) => {
    rateMutation.mutate({ newsId, rating })
  }

  const toggleExpand = (newsId: number) => {
    const newExpanded = new Set(expandedNews)
    if (newExpanded.has(newsId)) {
      newExpanded.delete(newsId)
    } else {
      newExpanded.add(newsId)
    }
    setExpandedNews(newExpanded)
  }

  const getRatingColor = (rating: number | undefined) => {
    if (rating === undefined || rating === null) return 'text-gray-400'
    if (rating > 0) return 'text-green-600'
    if (rating < 0) return 'text-red-600'
    return 'text-gray-500'
  }

  const getRatingBg = (rating: number | undefined) => {
    if (rating === undefined || rating === null) return 'bg-gray-100'
    if (rating > 5) return 'bg-green-100'
    if (rating > 0) return 'bg-green-50'
    if (rating < -5) return 'bg-red-100'
    if (rating < 0) return 'bg-red-50'
    return 'bg-gray-50'
  }

  const getAutoSentimentIcon = (sentiment: string | undefined) => {
    switch (sentiment) {
      case 'positive':
        return <ThumbsUp className="w-3 h-3 text-green-500" />
      case 'negative':
        return <ThumbsDown className="w-3 h-3 text-red-500" />
      default:
        return <Minus className="w-3 h-3 text-gray-400" />
    }
  }

  if (isLoading) {
    return (
      <div className={cn('bg-white rounded-xl p-6 shadow-sm', className)}>
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
          <span className="text-gray-600">뉴스 데이터 로딩 중...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('bg-white rounded-xl p-6 shadow-sm', className)}>
        <div className="flex items-center gap-3 text-red-500">
          <AlertCircle className="w-5 h-5" />
          <span>뉴스 데이터를 불러올 수 없습니다.</span>
        </div>
      </div>
    )
  }

  const news = data?.news || []
  const sentimentScore = data?.sentimentScore || { score: 10, avg_rating: 0, rated_count: 0 }
  const ratedCount = news.filter((n: NewsItem) => n.is_rated).length
  const unratedCount = news.length - ratedCount

  return (
    <div className={cn('bg-white rounded-xl shadow-sm overflow-hidden', className)}>
      {/* 헤더 */}
      <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-500">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">뉴스 평점</h3>
            <p className="text-sm text-blue-100">
              {stockName} - 최근 30일 뉴스
            </p>
          </div>
          <button
            onClick={handleCollect}
            disabled={collectMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn('w-4 h-4', collectMutation.isPending && 'animate-spin')} />
            <span>{collectMutation.isPending ? '수집 중...' : '뉴스 수집'}</span>
          </button>
        </div>
      </div>

      {/* 점수 요약 */}
      <div className="px-6 py-4 bg-gray-50 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div>
              <div className="text-sm text-gray-500">감정 점수</div>
              <div className="text-2xl font-bold text-blue-600">
                {sentimentScore.score.toFixed(1)}<span className="text-sm text-gray-400">/20</span>
              </div>
            </div>
            <div className="h-10 border-l border-gray-200" />
            <div>
              <div className="text-sm text-gray-500">평균 평점</div>
              <div className={cn('text-xl font-semibold', getRatingColor(sentimentScore.avg_rating))}>
                {sentimentScore.avg_rating > 0 ? '+' : ''}{sentimentScore.avg_rating.toFixed(1)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span className="text-gray-600">평점 완료: {ratedCount}건</span>
            </div>
            <div className="flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-orange-500" />
              <span className="text-gray-600">미완료: {unratedCount}건</span>
            </div>
          </div>
        </div>
      </div>

      {/* 뉴스 리스트 */}
      <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
        {news.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            <p>수집된 뉴스가 없습니다.</p>
            <p className="text-sm mt-1">위의 '뉴스 수집' 버튼을 클릭하여 뉴스를 수집해주세요.</p>
          </div>
        ) : (
          news.map((item: NewsItem) => (
            <div
              key={item.id}
              className={cn(
                'px-6 py-4 transition-colors',
                getRatingBg(item.rating),
                item.is_rated ? 'opacity-80' : ''
              )}
            >
              {/* 뉴스 제목 및 정보 */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {getAutoSentimentIcon(item.auto_sentiment)}
                    <span className="text-xs text-gray-400 uppercase">{item.auto_impact}</span>
                    {item.press && (
                      <span className="text-xs text-gray-500">{item.press}</span>
                    )}
                    {item.news_date && (
                      <span className="text-xs text-gray-400">{item.news_date}</span>
                    )}
                  </div>
                  <a
                    href={item.link || item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-800 hover:text-blue-600 font-medium flex items-start gap-1"
                  >
                    <span className="line-clamp-2">{item.title}</span>
                    <ExternalLink className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  </a>
                </div>

                {/* 현재 평점 표시 */}
                {item.is_rated && (
                  <div className={cn(
                    'px-3 py-1 rounded-full text-sm font-medium',
                    getRatingColor(item.rating),
                    getRatingBg(item.rating)
                  )}>
                    {item.rating && item.rating > 0 ? '+' : ''}{item.rating}
                  </div>
                )}
              </div>

              {/* 평점 버튼 */}
              <div className="mt-3">
                <button
                  onClick={() => toggleExpand(item.id!)}
                  className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  {expandedNews.has(item.id!) ? (
                    <>
                      <ChevronUp className="w-4 h-4" />
                      평점 숨기기
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4" />
                      평점 입력
                    </>
                  )}
                </button>

                {expandedNews.has(item.id!) && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex flex-wrap gap-2">
                      {/* 부정적 */}
                      {[-10, -7, -5, -3].map((rating) => (
                        <button
                          key={rating}
                          onClick={() => handleRate(item.id!, rating)}
                          disabled={rateMutation.isPending}
                          className={cn(
                            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                            item.rating === rating
                              ? 'bg-red-500 text-white'
                              : 'bg-red-50 text-red-600 hover:bg-red-100'
                          )}
                        >
                          {rating}
                        </button>
                      ))}

                      {/* 무관 */}
                      <button
                        onClick={() => handleRate(item.id!, 0)}
                        disabled={rateMutation.isPending}
                        className={cn(
                          'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                          item.rating === 0
                            ? 'bg-gray-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        )}
                      >
                        0 (무관)
                      </button>

                      {/* 긍정적 */}
                      {[3, 5, 7, 10].map((rating) => (
                        <button
                          key={rating}
                          onClick={() => handleRate(item.id!, rating)}
                          disabled={rateMutation.isPending}
                          className={cn(
                            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                            item.rating === rating
                              ? 'bg-green-500 text-white'
                              : 'bg-green-50 text-green-600 hover:bg-green-100'
                          )}
                        >
                          +{rating}
                        </button>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-gray-400">
                      -10: 매우 부정 | 0: 무관 | +10: 매우 긍정
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
