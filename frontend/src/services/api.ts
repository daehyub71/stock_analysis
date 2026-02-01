import axios from 'axios'
import type {
  Stock,
  AnalysisResult,
  PriceHistory,
  PaginatedResponse,
  StockFilter,
  SortOption,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Stock APIs
export const stockApi = {
  // 종목 리스트 조회
  getStocks: async (params: {
    filter?: StockFilter
    sort?: SortOption
    page?: number
    pageSize?: number
    search?: string
  }): Promise<PaginatedResponse<Stock & { analysis: AnalysisResult }>> => {
    const response = await api.get('/stocks', { params })
    return response.data
  },

  // 종목 상세 조회
  getStock: async (code: string): Promise<Stock> => {
    const response = await api.get(`/stocks/${code}`)
    return response.data
  },

  // 종목 주가 히스토리
  getPriceHistory: async (
    code: string,
    days = 365
  ): Promise<PriceHistory[]> => {
    const response = await api.get(`/stocks/${code}/history`, {
      params: { days },
    })
    return response.data
  },

  // 업종 목록
  getSectors: async (): Promise<string[]> => {
    const response = await api.get('/stocks/sectors')
    return response.data
  },
}

// Analysis APIs
export const analysisApi = {
  // 분석 결과 조회
  getAnalysis: async (code: string): Promise<AnalysisResult> => {
    const response = await api.get(`/analysis/${code}`)
    return response.data
  },

  // 분석 순위 조회
  getRanking: async (params: {
    date?: string
    limit?: number
    minScore?: number
  }): Promise<AnalysisResult[]> => {
    const response = await api.get('/analysis/ranking', { params })
    return response.data
  },

  // 분석 히스토리 조회
  getHistory: async (
    code: string,
    days = 30
  ): Promise<{ date: string; score: number }[]> => {
    const response = await api.get(`/analysis/${code}/history`, {
      params: { days },
    })
    return response.data
  },

  // 분석 실행 (관리자용)
  runAnalysis: async (code: string): Promise<AnalysisResult> => {
    const response = await api.post(`/analysis/${code}/run`)
    return response.data
  },

  // 일괄 분석 (관리자용)
  runBatchAnalysis: async (): Promise<{ count: number }> => {
    const response = await api.post('/analysis/batch')
    return response.data
  },

  // LLM 코멘터리 조회
  getCommentary: async (code: string): Promise<{
    stockCode: string
    stockName: string
    totalScore: number
    grade: string
    commentary: {
      summary: string
      highlights: string[]
      risks: string[]
      technical_comment: string
      fundamental_comment: string
      sentiment_comment: string
      action_suggestion: string
    }
  }> => {
    const response = await api.get(`/analysis/${code}/commentary`)
    return response.data
  },

  // 뉴스 목록 조회
  getNewsList: async (code: string, ratedOnly = false): Promise<{
    stockCode: string
    stockName: string
    newsCount: number
    sentimentScore: {
      score: number
      avg_rating: number
      rated_count: number
    }
    news: NewsItem[]
  }> => {
    const response = await api.get(`/analysis/${code}/news`, {
      params: { rated_only: ratedOnly }
    })
    return response.data
  },

  // 뉴스 수집
  collectNews: async (code: string, days = 30, limit = 50): Promise<{
    stockCode: string
    stockName: string
    collectedCount: number
    savedCount: number
    totalNews: number
    news: NewsItem[]
  }> => {
    const response = await api.post(`/analysis/${code}/news/collect`, null, {
      params: { days, limit }
    })
    return response.data
  },

  // 뉴스 평점 업데이트
  updateNewsRating: async (code: string, newsId: number, rating: number): Promise<{
    newsId: number
    rating: number
    sentimentScore: {
      score: number
      avg_rating: number
      rated_count: number
    }
  }> => {
    const response = await api.put(`/analysis/${code}/news/${newsId}/rate`, null, {
      params: { rating }
    })
    return response.data
  },

  // 감정 점수 조회
  getSentimentScore: async (code: string): Promise<{
    stockCode: string
    stockName: string
    sentimentScore: number
    maxScore: number
    avgRating: number
    ratedCount: number
    unratedCount: number
    totalNews: number
  }> => {
    const response = await api.get(`/analysis/${code}/sentiment-score`)
    return response.data
  },
}

// Compare APIs
export const compareApi = {
  // 종목 비교
  compareStocks: async (codes: string[]): Promise<AnalysisResult[]> => {
    const response = await api.get('/stocks/compare', {
      params: { codes: codes.join(',') },
    })
    return response.data
  },
}

export default api
