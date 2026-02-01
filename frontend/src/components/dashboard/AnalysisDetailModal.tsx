import { useState, useEffect } from 'react'
import { X, ExternalLink, BarChart3, PieChart, Activity, Loader2 } from 'lucide-react'
import { cn, formatNumber, getGradeColor, getGradeBgColor } from '@/lib/utils'
import { analysisApi } from '@/services/api'
import type { AnalysisResult } from '@/types'
import PriceChart from '@/components/charts/PriceChart'

interface AnalysisDetailModalProps {
  isOpen: boolean
  onClose: () => void
  stockCode: string
  stockName: string
}

type TabType = '기술분석' | '기본분석' | '감정분석'

export default function AnalysisDetailModal({ isOpen, onClose, stockCode, stockName }: AnalysisDetailModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('기본분석')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && stockCode) {
      setLoading(true)
      setError(null)
      analysisApi.getAnalysis(stockCode)
        .then(data => {
          setAnalysis(data)
          setLoading(false)
        })
        .catch(err => {
          setError(err.message || '데이터를 불러올 수 없습니다.')
          setLoading(false)
        })
    }
  }, [isOpen, stockCode])

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-gray-900">{stockName}</h2>
            <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">{stockCode}</span>
            {analysis && (
              <span className={cn(
                'px-2 py-0.5 text-sm font-bold rounded',
                getGradeBgColor(analysis.grade),
                getGradeColor(analysis.grade)
              )}>
                {analysis.grade} ({analysis.totalScore.toFixed(1)}점)
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <a
              href={`https://finance.naver.com/item/main.naver?code=${stockCode}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              <ExternalLink className="w-5 h-5" />
            </a>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Loading / Error */}
        {loading && (
          <div className="flex-1 flex items-center justify-center p-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          </div>
        )}

        {error && (
          <div className="flex-1 flex items-center justify-center p-12">
            <p className="text-red-500">{error}</p>
          </div>
        )}

        {/* Content */}
        {!loading && !error && analysis && (
          <>
            {/* Score Summary */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="grid grid-cols-3 gap-4">
                <ScoreSummaryItem
                  label="기술분석"
                  score={analysis.scoreBreakdown.technical.score}
                  max={30}
                  color="blue"
                />
                <ScoreSummaryItem
                  label="기본분석"
                  score={analysis.scoreBreakdown.fundamental.score}
                  max={50}
                  color="green"
                />
                <ScoreSummaryItem
                  label="감정분석"
                  score={analysis.scoreBreakdown.sentiment.score}
                  max={20}
                  color="purple"
                />
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="flex px-6">
                {(['기술분석', '기본분석', '감정분석'] as TabType[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={cn(
                      'px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2',
                      activeTab === tab
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    )}
                  >
                    {tab === '기술분석' && <BarChart3 className="w-4 h-4" />}
                    {tab === '기본분석' && <PieChart className="w-4 h-4" />}
                    {tab === '감정분석' && <Activity className="w-4 h-4" />}
                    {tab}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === '기술분석' && <TechnicalTab details={analysis.details?.technical} stockCode={stockCode} />}
              {activeTab === '기본분석' && <FundamentalTab details={analysis.details?.fundamental} />}
              {activeTab === '감정분석' && <SentimentTab details={analysis.details?.sentiment} />}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// Score Summary Item
interface ScoreSummaryItemProps {
  label: string
  score: number
  max: number
  color: 'blue' | 'green' | 'purple' | 'red'
  isPenalty?: boolean
}

function ScoreSummaryItem({ label, score, max, color, isPenalty }: ScoreSummaryItemProps) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500',
  }

  const percentage = isPenalty
    ? (Math.abs(score) / Math.abs(max)) * 100
    : (score / max) * 100

  return (
    <div className="bg-white p-3 rounded-lg">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className={cn('text-lg font-bold', isPenalty ? 'text-red-600' : 'text-gray-900')}>
          {isPenalty && score < 0 ? '' : ''}{score.toFixed(1)}
        </span>
        <span className="text-xs text-gray-400">/ {max}</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full mt-2 overflow-hidden">
        <div
          className={cn('h-full rounded-full', colorClasses[color])}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

// Metric Card
interface MetricCardProps {
  label: string
  value: string | number | null
  subLabel?: string
  highlight?: 'positive' | 'negative' | 'neutral'
}

function MetricCard({ label, value, subLabel, highlight }: MetricCardProps) {
  return (
    <div className="bg-gray-50 p-3 rounded-lg">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={cn(
        'text-xl font-bold font-mono',
        highlight === 'positive' && 'text-green-600',
        highlight === 'negative' && 'text-red-600',
        highlight === 'neutral' && 'text-gray-900',
        !highlight && 'text-gray-900'
      )}>
        {value !== null && value !== undefined ? value : '-'}
      </p>
      {subLabel && <p className="text-xs text-gray-400 mt-1">{subLabel}</p>}
    </div>
  )
}

// Technical Tab
interface TechnicalTabProps {
  details: any
  stockCode: string
}

function TechnicalTab({ details, stockCode }: TechnicalTabProps) {
  const items = details?.details || {}
  const indicators = details?.indicators || {}

  return (
    <div className="space-y-6">
      {/* Price Chart with MAs */}
      <PriceChart
        stockCode={stockCode}
        currentPrice={indicators.currentPrice}
        ma5={indicators.ma5}
        ma20={indicators.ma20}
        ma60={indicators.ma60}
        ma120={indicators.ma120}
      />

      {/* Score Details */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">📊 점수 상세</h4>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(items).map(([key, item]: [string, any]) => (
            <div key={key} className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">{getLabel(key)}</p>
              <p className="text-lg font-bold">{item.score?.toFixed(1) || 0} <span className="text-xs text-gray-400">/ {item.max || 0}</span></p>
              <p className="text-xs text-gray-400 mt-1 truncate">{item.description || ''}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Indicators */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">📈 기술지표</h4>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard label="MA5" value={indicators.ma5 ? formatNumber(indicators.ma5) : null} />
          <MetricCard label="MA20" value={indicators.ma20 ? formatNumber(indicators.ma20) : null} />
          <MetricCard label="MA60" value={indicators.ma60 ? formatNumber(indicators.ma60) : null} />
          <MetricCard label="MA120" value={indicators.ma120 ? formatNumber(indicators.ma120) : null} />
          <MetricCard label="RSI (14)" value={indicators.rsi14?.toFixed(1)}
            highlight={indicators.rsi14 >= 70 ? 'negative' : indicators.rsi14 <= 30 ? 'positive' : 'neutral'} />
          <MetricCard label="MACD" value={indicators.macd?.toFixed(2)} />
          <MetricCard label="Signal" value={indicators.macdSignal?.toFixed(2)} />
          <MetricCard label="Histogram" value={indicators.macdHist?.toFixed(2)}
            highlight={indicators.macdHist > 0 ? 'positive' : indicators.macdHist < 0 ? 'negative' : 'neutral'} />
        </div>
      </div>
    </div>
  )
}

// Fundamental Tab
function FundamentalTab({ details }: { details: any }) {
  const items = details?.details || {}
  const financials = details?.financials || {}

  // Get actual values from details
  const getValue = (key: string) => {
    const item = items[key]
    return item?.value !== undefined ? item.value : financials[key]
  }

  const per = getValue('per')
  const pbr = getValue('pbr')
  const psr = getValue('psr')
  const roe = getValue('roe')
  const opMargin = getValue('opMargin')
  const revenueGrowth = getValue('revenueGrowth')
  const opGrowth = getValue('opGrowth')
  const debtRatio = getValue('debtRatio')
  const currentRatio = getValue('currentRatio')

  return (
    <div className="space-y-6">
      {/* Score Details */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">📊 점수 상세</h4>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(items).slice(0, 5).map(([key, item]: [string, any]) => (
            <div key={key} className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">{getLabel(key)}</p>
              <p className="text-lg font-bold">{item.score?.toFixed(1) || 0} <span className="text-xs text-gray-400">/ {item.max || 0}</span></p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-4 gap-3 mt-3">
          {Object.entries(items).slice(5).map(([key, item]: [string, any]) => (
            <div key={key} className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">{getLabel(key)}</p>
              <p className="text-lg font-bold">{item.score?.toFixed(1) || 0} <span className="text-xs text-gray-400">/ {item.max || 0}</span></p>
            </div>
          ))}
        </div>
      </div>

      {/* Valuation */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">📈 밸류에이션 지표</h4>
        <div className="grid grid-cols-3 gap-3">
          <MetricCard
            label="PER (주가수익비율)"
            value={per !== null && per !== undefined ? per.toFixed(1) : null}
            subLabel={per ? (per < 10 ? '저평가' : per > 20 ? '고평가' : '적정') : undefined}
            highlight={per ? (per < 10 ? 'positive' : per > 20 ? 'negative' : 'neutral') : undefined}
          />
          <MetricCard
            label="PBR (주가순자산비율)"
            value={pbr !== null && pbr !== undefined ? pbr.toFixed(2) : null}
            subLabel={pbr ? (pbr < 1 ? '저평가' : pbr > 2 ? '고평가' : '적정') : undefined}
            highlight={pbr ? (pbr < 1 ? 'positive' : pbr > 2 ? 'negative' : 'neutral') : undefined}
          />
          <MetricCard
            label="PSR (주가매출비율)"
            value={psr !== null && psr !== undefined ? psr.toFixed(2) : null}
            subLabel={psr ? (psr < 1 ? '저평가' : psr > 3 ? '고평가' : '적정') : undefined}
          />
        </div>
      </div>

      {/* Profitability & Growth */}
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">💰 수익성</h4>
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="ROE"
              value={roe !== null && roe !== undefined ? `${roe.toFixed(1)}%` : null}
              highlight={roe ? (roe >= 15 ? 'positive' : roe < 5 ? 'negative' : 'neutral') : undefined}
            />
            <MetricCard
              label="영업이익률"
              value={opMargin !== null && opMargin !== undefined ? `${opMargin.toFixed(1)}%` : null}
              highlight={opMargin ? (opMargin >= 15 ? 'positive' : opMargin < 5 ? 'negative' : 'neutral') : undefined}
            />
          </div>
        </div>
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">📊 성장성</h4>
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="매출성장률"
              value={revenueGrowth !== null && revenueGrowth !== undefined ? `${revenueGrowth > 0 ? '+' : ''}${revenueGrowth.toFixed(1)}%` : null}
              highlight={revenueGrowth ? (revenueGrowth > 10 ? 'positive' : revenueGrowth < 0 ? 'negative' : 'neutral') : undefined}
            />
            <MetricCard
              label="영업이익성장률"
              value={opGrowth !== null && opGrowth !== undefined ? `${opGrowth > 0 ? '+' : ''}${opGrowth.toFixed(1)}%` : null}
              highlight={opGrowth ? (opGrowth > 10 ? 'positive' : opGrowth < 0 ? 'negative' : 'neutral') : undefined}
            />
          </div>
        </div>
      </div>

      {/* Stability */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">🛡️ 안정성</h4>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            label="부채비율"
            value={debtRatio !== null && debtRatio !== undefined ? `${debtRatio.toFixed(1)}%` : null}
            subLabel={debtRatio ? (debtRatio <= 100 ? '안정' : debtRatio > 200 ? '위험' : '보통') : undefined}
            highlight={debtRatio ? (debtRatio <= 100 ? 'positive' : debtRatio > 200 ? 'negative' : 'neutral') : undefined}
          />
          <MetricCard
            label="유동비율"
            value={currentRatio !== null && currentRatio !== undefined ? `${currentRatio.toFixed(1)}%` : null}
            subLabel={currentRatio ? (currentRatio >= 200 ? '안정' : currentRatio < 100 ? '위험' : '보통') : undefined}
            highlight={currentRatio ? (currentRatio >= 200 ? 'positive' : currentRatio < 100 ? 'negative' : 'neutral') : undefined}
          />
        </div>
      </div>
    </div>
  )
}

// Sentiment Tab
function SentimentTab({ details }: { details: any }) {
  const items = details?.details || {}
  const newsCount = details?.newsCount || details?.newsSummary?.total || 0

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(items).map(([key, item]: [string, any]) => (
          <div key={key} className="bg-gray-50 p-4 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">{getLabel(key)}</p>
            <p className="text-2xl font-bold">{item.score?.toFixed(1) || 0} <span className="text-xs text-gray-400">/ {item.max || 0}</span></p>
            <p className="text-xs text-gray-400 mt-1">{item.description || ''}</p>
          </div>
        ))}
      </div>
      <div className="bg-blue-50 p-4 rounded-lg">
        <p className="text-sm text-blue-800">분석 뉴스: <strong>{newsCount}건</strong></p>
      </div>
    </div>
  )
}

// Helper
function getLabel(key: string): string {
  const labels: Record<string, string> = {
    maArrangement: 'MA 배열',
    maDivergence: 'MA 이격도',
    rsi: 'RSI',
    macd: 'MACD',
    volume: '거래량',
    per: 'PER',
    pbr: 'PBR',
    psr: 'PSR',
    revenueGrowth: '매출성장률',
    opGrowth: '영업이익성장률',
    roe: 'ROE',
    opMargin: '영업이익률',
    debtRatio: '부채비율',
    currentRatio: '유동비율',
    sentiment: '뉴스 감정',
    impact: '영향도',
  }
  return labels[key] || key
}
