// Stock Types
export interface Stock {
  id: number
  code: string
  name: string
  sector: string
  market: 'KOSPI' | 'KOSDAQ'
  currentPrice?: number
  priceChange?: number
  priceChangeRate?: number
}

// Analysis Types
export interface AnalysisResult {
  stockCode: string
  stockName: string
  analysisDate: string
  totalScore: number
  maxScore: number
  grade: Grade
  sentimentSource?: 'manual' | 'auto'  // 감정분석 출처 (수동/자동)
  scoreBreakdown: ScoreBreakdown
  details: AnalysisDetails
}

export type Grade = 'A+' | 'A' | 'B+' | 'B' | 'C+' | 'C' | 'D' | 'F'

export interface ScoreBreakdown {
  technical: ScoreItem
  fundamental: ScoreItem
  sentiment: ScoreItem
}

export interface ScoreItem {
  score: number
  max: number
  weight: string
  source?: 'manual' | 'auto'  // 감정분석 출처 (수동/자동)
}

export interface AnalysisDetails {
  technical: TechnicalDetails
  fundamental: FundamentalDetails
  sentiment: SentimentDetails
}

// Technical Analysis
export interface TechnicalDetails {
  stockCode: string
  hasData: boolean
  totalScore: number
  maxScore: number
  details: {
    maArrangement: DetailItem
    maDivergence: DetailItem
    rsi: DetailItem
    macd: DetailItem
    volume: DetailItem
  }
  indicators: TechnicalIndicators
}

export interface TechnicalIndicators {
  currentPrice: number
  ma5: number | null
  ma20: number | null
  ma60: number | null
  ma120: number | null
  rsi14: number | null
  macd: number | null
  macdSignal: number | null
  macdHist: number | null
  volumeRatio: number | null
}

// Fundamental Analysis
export interface FundamentalDetails {
  stockCode: string
  stockId: number | null
  sector: string | null
  hasData: boolean
  totalScore: number
  maxScore: number
  details: {
    per: DetailItem
    pbr: DetailItem
    psr: DetailItem
    revenueGrowth: DetailItem
    opGrowth: DetailItem
    roe: DetailItem
    opMargin: DetailItem
    debtRatio: DetailItem
    currentRatio: DetailItem
  }
  financials: Financials
}

export interface Financials {
  per: number | null
  pbr: number | null
  psr: number | null
  roe: number | null
  revenueGrowth: number | null
  opGrowth: number | null
  opMargin: number | null
  debtRatio: number | null
  currentRatio: number | null
}

// Sentiment Analysis
export interface SentimentDetails {
  stockCode: string
  stockName: string
  hasData: boolean
  totalScore: number
  maxScore: number
  periodDays: number
  source?: 'manual' | 'auto'  // 감정분석 출처 (수동/자동)
  manualRating?: {
    avgRating: number
    ratedCount: number
  } | null
  newsSummary: NewsSummary
  details: {
    sentiment: DetailItem
    impact: DetailItem
    volume: DetailItem
  }
  newsItems: NewsItem[]
}

export interface NewsSummary {
  total: number
  positive: number
  negative: number
  neutral: number
  highImpact: number
  mediumImpact: number
}

export interface NewsItem {
  id?: number
  title: string
  link?: string
  url?: string
  press?: string
  date?: string
  news_date?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  auto_sentiment?: 'positive' | 'negative' | 'neutral'
  impact?: 'high' | 'medium' | 'low'
  auto_impact?: 'high' | 'medium' | 'low'
  rating?: number  // -10 ~ +10 사용자 평점
  is_rated?: boolean
}

// Common
export interface DetailItem {
  score: number
  max: number
  description: string
}

// Price History
export interface PriceHistory {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Filter Types
export interface StockFilter {
  sector?: string
  minScore?: number
  maxScore?: number
  grades?: Grade[]
  excludeLoss?: boolean
  market?: 'KOSPI' | 'KOSDAQ' | 'all'
}

export interface SortOption {
  field: 'totalScore' | 'name' | 'sector' | 'priceChangeRate'
  direction: 'asc' | 'desc'
}

// Portfolio Types
export interface Portfolio {
  id: number
  name: string
  source?: string
  report_date?: string
  created_at: string
  stock_count?: number
  total_amount?: number
}

export interface PortfolioStock {
  stock_code: string
  stock_name: string
  sector?: string
  weight: number
  quantity?: number
  amount?: number
  total_score: number
  grade: Grade
  tech_total?: number
  fund_total?: number
  sent_total?: number
}

export interface PortfolioDetail extends Portfolio {
  stocks: PortfolioStock[]
  avg_score: number
  sector_distribution?: Record<string, number>
}

export interface PortfolioScore {
  portfolio_id: number
  avg_score: number
  weighted_score: number
  max_score: number
  min_score: number
  stock_count: number
}

// Backtest Types
export interface BacktestDailyData {
  date: string
  price: number
  score: number
  portfolioValue: number
  position: 'holding' | 'cash'
  shares: number
}

export interface BacktestTrade {
  type: 'buy' | 'sell'
  date: string
  price: number
  shares: number
  score: number
  portfolioValue: number
  profit?: number
  profitPct?: number
}

export interface BacktestMetrics {
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  tradeCount: number
  finalValue: number
  tradingDays: number
}

export interface BacktestResponse {
  stockCode: string
  stockName: string
  params: {
    startDate: string
    endDate: string
    initialCapital: number
    buyThreshold: number
    sellThreshold: number
  }
  dailyData: BacktestDailyData[]
  trades: BacktestTrade[]
  metrics: BacktestMetrics
  benchmark: {
    buyHoldReturn: number
  }
}
