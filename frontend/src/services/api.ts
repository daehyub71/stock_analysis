import axios from 'axios'
import type {
  Stock,
  AnalysisResult,
  PriceHistory,
  PaginatedResponse,
  StockFilter,
  SortOption,
  NewsItem,
  BacktestResponse,
  Portfolio,
  PortfolioDetail,
  PortfolioScore,
} from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
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

  // 기업개요 조회
  getCompanyOverview: async (code: string): Promise<{
    stockCode: string
    stockName: string
    overview: string[]
  }> => {
    const response = await api.get(`/stocks/${code}/overview`)
    return response.data
  },

  // 대시보드 통계
  getOverview: async (): Promise<{
    totalStocks: number
    avgScore: number
    upCount: number
    downCount: number
    analyzedCount: number
  }> => {
    const response = await api.get('/stocks/overview')
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

  // 미평점 뉴스 일괄 평점 설정
  rateAllNews: async (code: string, rating: number): Promise<{
    updatedCount: number
    rating: number
    sentimentScore: {
      score: number
      avg_rating: number
      rated_count: number
    }
  }> => {
    const response = await api.put(`/analysis/${code}/news/rate-all`, null, {
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

// Alerts APIs
export const alertsApi = {
  // 점수 변화 조회
  getScoreChanges: async (threshold = 5): Promise<{
    threshold: number
    count: number
    changes: {
      stockCode: string
      stockName: string
      prevScore: number
      currScore: number
      change: number
      grade: string
      date: string
    }[]
  }> => {
    const response = await api.get('/alerts/score-changes', {
      params: { threshold },
    })
    return response.data
  },

  // 알림 이메일 발송
  sendAlertEmail: async (email: string, threshold = 5): Promise<{
    sent: boolean
    message: string
    email?: string
    changesCount?: number
  }> => {
    const response = await api.post('/alerts/send-alert-email', {
      email,
      threshold,
    })
    return response.data
  },
}

// Portfolio APIs
export const portfolioApi = {
  // 포트폴리오 목록 조회
  getPortfolios: async (): Promise<Portfolio[]> => {
    const response = await api.get('/portfolios')
    return response.data
  },

  // 포트폴리오 생성
  createPortfolio: async (data: { name: string; source?: string }): Promise<Portfolio> => {
    const response = await api.post('/portfolios', data)
    return response.data
  },

  // 포트폴리오 상세 조회
  getPortfolio: async (id: number): Promise<PortfolioDetail> => {
    const response = await api.get(`/portfolios/${id}`)
    return response.data
  },

  // 포트폴리오 수정
  updatePortfolio: async (id: number, data: { name?: string; source?: string }): Promise<Portfolio> => {
    const response = await api.put(`/portfolios/${id}`, data)
    return response.data
  },

  // 포트폴리오 삭제
  deletePortfolio: async (id: number): Promise<{ message: string; id: number }> => {
    const response = await api.delete(`/portfolios/${id}`)
    return response.data
  },

  // 종목 추가
  addStock: async (portfolioId: number, stockCode: string): Promise<{
    portfolio_id: number
    stock_code: string
    stock_name: string
    message: string
  }> => {
    const response = await api.post(`/portfolios/${portfolioId}/stocks`, { stock_code: stockCode })
    return response.data
  },

  // 종목 제거
  removeStock: async (portfolioId: number, stockCode: string): Promise<{
    portfolio_id: number
    stock_code: string
    message: string
  }> => {
    const response = await api.delete(`/portfolios/${portfolioId}/stocks/${stockCode}`)
    return response.data
  },

  // 비중 수정
  updateWeight: async (portfolioId: number, stockCode: string, weight: number): Promise<{
    portfolio_id: number
    stock_code: string
    weight: number
    message: string
  }> => {
    const response = await api.put(`/portfolios/${portfolioId}/stocks/${stockCode}/weight`, { weight })
    return response.data
  },

  // 포트폴리오 점수 조회
  getScore: async (portfolioId: number): Promise<PortfolioScore> => {
    const response = await api.get(`/portfolios/${portfolioId}/score`)
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

// Backtest APIs
export const backtestApi = {
  // 백테스트 실행
  runBacktest: async (code: string, params: {
    start_date: string
    end_date: string
    initial_capital?: number
    buy_threshold?: number
    sell_threshold?: number
  }): Promise<BacktestResponse> => {
    const response = await api.post(`/backtest/${code}/run`, params)
    return response.data
  },

  // 백테스트 가능 기간 조회
  getDateRange: async (code: string): Promise<{
    stockCode: string
    stockName: string
    startDate: string
    endDate: string
  }> => {
    const response = await api.get(`/backtest/${code}/date-range`)
    return response.data
  },
}

export default api
