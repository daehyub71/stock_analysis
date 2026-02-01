import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, RefreshCw, AlertTriangle, BarChart3, PieChart, Activity, HelpCircle } from 'lucide-react'
import { stockApi, analysisApi } from '@/services/api'
import { LoadingPage, ErrorDisplay } from '@/components/common'
import { TotalScoreCard, ScoreCard } from '@/components/dashboard'
import PriceChart from '@/components/charts/PriceChart'
import AnalysisCommentary from '@/components/analysis/AnalysisCommentary'
import NewsRating from '@/components/analysis/NewsRating'
import { cn, formatNumber, formatPercent, getPriceChangeColor } from '@/lib/utils'

type TabType = '기술분석' | '기본분석' | '감정분석'

export default function StockDetailPage() {
  const [activeTab, setActiveTab] = useState<TabType>('기술분석')
  const { code } = useParams<{ code: string }>()

  // 종목 정보 조회
  const {
    data: stock,
    isLoading: stockLoading,
    error: stockError,
  } = useQuery({
    queryKey: ['stock', code],
    queryFn: () => stockApi.getStock(code!),
    enabled: !!code,
  })

  // 분석 결과 조회
  const {
    data: analysis,
    isLoading: analysisLoading,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useQuery({
    queryKey: ['analysis', code],
    queryFn: () => analysisApi.getAnalysis(code!),
    enabled: !!code,
  })

  const isLoading = stockLoading || analysisLoading
  const error = stockError || analysisError

  if (isLoading) {
    return <LoadingPage />
  }

  if (error || !stock || !analysis) {
    return (
      <ErrorDisplay
        error={error as Error || { message: '데이터를 불러올 수 없습니다.' }}
        onRetry={() => refetchAnalysis()}
      />
    )
  }

  const breakdown = analysis.scoreBreakdown
  const details = analysis.details

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">{stock.name}</h1>
              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                {stock.code}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-sm text-gray-500">{stock.sector || '업종 미분류'}</span>
              <span className="text-gray-300">|</span>
              <span className="text-sm text-gray-500">{stock.market}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetchAnalysis()}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
            새로고침
          </button>
          <a
            href={`https://finance.naver.com/item/main.naver?code=${stock.code}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
          >
            <ExternalLink className="w-4 h-4" />
            네이버 증권
          </a>
        </div>
      </div>

      {/* Price Info */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">현재가</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900">
                {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}
              </span>
              <span className="text-gray-500">원</span>
            </div>
          </div>
          {stock.priceChangeRate !== undefined && (
            <div className="text-right">
              <p className="text-sm text-gray-500 mb-1">등락률</p>
              <div className="flex items-center gap-2">
                {stock.priceChangeRate > 0 ? (
                  <TrendingUp className="w-6 h-6 text-red-500" />
                ) : stock.priceChangeRate < 0 ? (
                  <TrendingDown className="w-6 h-6 text-blue-500" />
                ) : null}
                <span
                  className={cn(
                    'text-2xl font-bold',
                    getPriceChangeColor(stock.priceChangeRate)
                  )}
                >
                  {formatPercent(stock.priceChangeRate)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Score Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <TotalScoreCard
          totalScore={analysis.totalScore}
          maxScore={analysis.maxScore}
          grade={analysis.grade}
          breakdown={{
            technical: breakdown.technical.score,
            fundamental: breakdown.fundamental.score,
            sentiment: breakdown.sentiment.score,
          }}
          sentimentSource={analysis.sentimentSource || breakdown.sentiment.source}
        />

        <div className="lg:col-span-2 grid grid-cols-3 gap-4">
          <ScoreCard
            title="기술분석"
            score={breakdown.technical.score}
            maxScore={30}
            description="MA배열, 이격도, RSI, MACD, 거래량"
          />
          <ScoreCard
            title="기본분석"
            score={breakdown.fundamental.score}
            maxScore={50}
            description="PER, PBR, PSR, 성장률, ROE, 마진"
          />
          <ScoreCard
            title={`감정분석${(analysis.sentimentSource || breakdown.sentiment.source) === 'manual' ? ' (수동)' : ''}`}
            score={breakdown.sentiment.score}
            maxScore={20}
            description={(analysis.sentimentSource || breakdown.sentiment.source) === 'manual' ? '수동 뉴스 평점 기반' : '뉴스 감정, 영향도, 관심도'}
          />
        </div>
      </div>

      {/* AI Analysis Commentary */}
      <AnalysisCommentary stockCode={stock.code} stockName={stock.name} />

      {/* Analysis Details Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {(['기술분석', '기본분석', '감정분석'] as TabType[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-6 py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2',
                  activeTab === tab
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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

        <div className="p-6">
          {/* 기술분석 탭 */}
          {activeTab === '기술분석' && (
            <TechnicalAnalysisTab details={details.technical} stockCode={stock.code} />
          )}

          {/* 기본분석 탭 */}
          {activeTab === '기본분석' && (
            <FundamentalAnalysisTab details={details.fundamental} />
          )}

          {/* 감정분석 탭 */}
          {activeTab === '감정분석' && (
            <SentimentAnalysisTab
              details={details.sentiment}
              stockCode={stock.code}
              stockName={stock.name}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// Detail Card Component
interface DetailCardProps {
  label: string
  score: number
  max: number
  description: string
}

function DetailCard({ label, score, max, description }: DetailCardProps) {
  const percentage = (score / max) * 100

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <div className="flex items-baseline gap-1 mb-2">
        <span className="text-lg font-bold text-gray-900">{score.toFixed(1)}</span>
        <span className="text-xs text-gray-400">/ {max}</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden mb-2">
        <div
          className="h-full bg-primary-500 rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 truncate" title={description}>
        {description}
      </p>
    </div>
  )
}

// Helper function
function getDetailLabel(key: string): string {
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
    sentiment: '감정',
    impact: '영향도',
  }
  return labels[key] || key
}

// ===== 툴팁 컴포넌트 =====
interface TooltipProps {
  content: string
}

function Tooltip({ content }: TooltipProps) {
  return (
    <div className="group relative inline-flex items-center ml-1.5">
      <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
      <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-pre-line z-50 w-64 shadow-lg">
        {content}
        <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-gray-900" />
      </div>
    </div>
  )
}

// 지표 설명
const INDICATOR_DESCRIPTIONS = {
  ma: `이동평균선(MA)은 일정 기간 동안의 주가 평균값을 연결한 선입니다.

• MA5: 5일 단기 추세
• MA20: 20일 중기 추세
• MA60: 60일 중장기 추세
• MA120: 120일 장기 추세

정배열(MA5>MA20>MA60): 상승 추세
역배열(MA5<MA20<MA60): 하락 추세`,
  rsi: `RSI(상대강도지수)는 주가의 과매수/과매도 상태를 나타냅니다.

• 70 이상: 과매수 구간 (조정 가능성)
• 30 이하: 과매도 구간 (반등 가능성)
• 30~70: 중립 구간

14일 기준으로 계산되며, 극단적 수치일수록 추세 전환 가능성이 높습니다.`,
  macd: `MACD는 단기/장기 이동평균의 차이로 추세 전환을 포착합니다.

• MACD선: 12일 EMA - 26일 EMA
• Signal선: MACD의 9일 EMA
• Histogram: MACD - Signal

Histogram이 양수→매수 신호
Histogram이 음수→매도 신호
골든크로스/데드크로스로 매매 시점 판단`,
}

// ===== 기술분석 탭 컴포넌트 =====
interface TechnicalAnalysisTabProps {
  details: {
    details?: Record<string, { score: number; max: number; description: string }>
    indicators?: {
      currentPrice?: number | null
      ma5?: number | null
      ma20?: number | null
      ma60?: number | null
      ma120?: number | null
      rsi14?: number | null
      macd?: number | null
      macdSignal?: number | null
      macdHist?: number | null
      volumeRatio?: number | null
    }
    hasData?: boolean
  }
  stockCode: string
}

function TechnicalAnalysisTab({ details, stockCode }: TechnicalAnalysisTabProps) {
  const indicators = details?.indicators || {}
  const detailItems = details?.details || {}

  // MA 상태 판단
  const getMaStatus = () => {
    if (!indicators.ma5 || !indicators.ma20 || !indicators.ma60) return { status: '데이터 없음', color: 'text-gray-500' }
    const ma5 = indicators.ma5 || 0
    const ma20 = indicators.ma20 || 0
    const ma60 = indicators.ma60 || 0
    if (ma5 > ma20 && ma20 > ma60) return { status: '정배열 (상승추세)', color: 'text-green-600' }
    if (ma5 < ma20 && ma20 < ma60) return { status: '역배열 (하락추세)', color: 'text-red-600' }
    return { status: '혼조세', color: 'text-yellow-600' }
  }

  // RSI 상태 판단
  const getRsiStatus = () => {
    const rsi = indicators.rsi14
    if (!rsi) return { status: '데이터 없음', color: 'text-gray-500' }
    if (rsi >= 70) return { status: '과매수 구간', color: 'text-red-600' }
    if (rsi <= 30) return { status: '과매도 구간', color: 'text-green-600' }
    return { status: '중립 구간', color: 'text-gray-600' }
  }

  // MACD 상태 판단
  const getMacdStatus = () => {
    const hist = indicators.macdHist
    if (hist === undefined || hist === null) return { status: '데이터 없음', color: 'text-gray-500' }
    if (hist > 0) return { status: '매수 신호', color: 'text-green-600' }
    if (hist < 0) return { status: '매도 신호', color: 'text-red-600' }
    return { status: '중립', color: 'text-gray-600' }
  }

  const maStatus = getMaStatus()
  const rsiStatus = getRsiStatus()
  const macdStatus = getMacdStatus()

  return (
    <div className="space-y-6">
      {/* 주가 차트 */}
      <PriceChart
        stockCode={stockCode}
        currentPrice={indicators.currentPrice ?? undefined}
        ma5={indicators.ma5 ?? undefined}
        ma20={indicators.ma20 ?? undefined}
        ma60={indicators.ma60 ?? undefined}
        ma120={indicators.ma120 ?? undefined}
      />

      {/* 점수 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Object.entries(detailItems).map(([key, item]) => (
          <DetailCard
            key={key}
            label={getDetailLabel(key)}
            score={item.score}
            max={item.max}
            description={item.description}
          />
        ))}
      </div>

      {/* 기술지표 상세 */}
      <div className="pt-6 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-4">📊 기술지표 상세</h4>

        {/* 이동평균 */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <h5 className="font-medium text-gray-800">이동평균선 (MA)</h5>
              <Tooltip content={INDICATOR_DESCRIPTIONS.ma} />
            </div>
            <span className={cn('text-sm font-medium', maStatus.color)}>{maStatus.status}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">MA5 (5일)</p>
              <p className="text-lg font-mono font-medium">{indicators.ma5 ? formatNumber(indicators.ma5) : '-'}</p>
            </div>
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">MA20 (20일)</p>
              <p className="text-lg font-mono font-medium">{indicators.ma20 ? formatNumber(indicators.ma20) : '-'}</p>
            </div>
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">MA60 (60일)</p>
              <p className="text-lg font-mono font-medium">{indicators.ma60 ? formatNumber(indicators.ma60) : '-'}</p>
            </div>
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">MA120 (120일)</p>
              <p className="text-lg font-mono font-medium">{indicators.ma120 ? formatNumber(indicators.ma120) : '-'}</p>
            </div>
          </div>
        </div>

        {/* RSI */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <h5 className="font-medium text-gray-800">RSI (14)</h5>
              <Tooltip content={INDICATOR_DESCRIPTIONS.rsi} />
            </div>
            <span className={cn('text-sm font-medium', rsiStatus.color)}>{rsiStatus.status}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full flex">
                  <div className="bg-green-400 w-[30%]" />
                  <div className="bg-gray-300 w-[40%]" />
                  <div className="bg-red-400 w-[30%]" />
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0 (과매도)</span>
                <span>50 (중립)</span>
                <span>100 (과매수)</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold font-mono">{indicators.rsi14?.toFixed(1) || '-'}</p>
            </div>
          </div>
        </div>

        {/* MACD */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <h5 className="font-medium text-gray-800">MACD (12, 26, 9)</h5>
              <Tooltip content={INDICATOR_DESCRIPTIONS.macd} />
            </div>
            <span className={cn('text-sm font-medium', macdStatus.color)}>{macdStatus.status}</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">MACD</p>
              <p className="text-lg font-mono font-medium">{indicators.macd?.toFixed(2) || '-'}</p>
            </div>
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">Signal</p>
              <p className="text-lg font-mono font-medium">{indicators.macdSignal?.toFixed(2) || '-'}</p>
            </div>
            <div className="bg-white p-3 rounded">
              <p className="text-xs text-gray-500">Histogram</p>
              <p className={cn('text-lg font-mono font-medium', (indicators.macdHist || 0) >= 0 ? 'text-green-600' : 'text-red-600')}>
                {indicators.macdHist?.toFixed(2) || '-'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ===== 기본분석 탭 컴포넌트 =====
interface FundamentalAnalysisTabProps {
  details: {
    details?: Record<string, { score: number; max: number; description: string; value?: number }>
    isLossCompany?: boolean
    hasData?: boolean
  }
}

function FundamentalAnalysisTab({ details }: FundamentalAnalysisTabProps) {
  const detailItems = details?.details || {}
  const isLossCompany = details?.isLossCompany || false

  // 값을 안전하게 가져오기
  const getValue = (key: string) => {
    const item = detailItems[key]
    return item?.value !== undefined ? item.value : null
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
      {/* 적자 기업 경고 */}
      {isLossCompany && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <div>
            <p className="font-medium text-red-800">적자 기업</p>
            <p className="text-sm text-red-600">최근 실적에서 손실이 발생하여 일부 지표가 제한됩니다.</p>
          </div>
        </div>
      )}

      {/* 점수 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Object.entries(detailItems).map(([key, item]) => (
          <DetailCard
            key={key}
            label={getDetailLabel(key)}
            score={item.score}
            max={item.max}
            description={item.description}
          />
        ))}
      </div>

      {/* 밸류에이션 지표 */}
      <div className="pt-6 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-4">📈 밸류에이션 지표</h4>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">PER (주가수익비율)</p>
              <p className="text-2xl font-bold font-mono">{per !== null ? per.toFixed(1) : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {per !== null && per > 0 ? (per < 10 ? '저평가' : per > 20 ? '고평가' : '적정') : '-'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">PBR (주가순자산비율)</p>
              <p className="text-2xl font-bold font-mono">{pbr !== null ? pbr.toFixed(2) : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {pbr !== null && pbr > 0 ? (pbr < 1 ? '저평가' : pbr > 2 ? '고평가' : '적정') : '-'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">PSR (주가매출비율)</p>
              <p className="text-2xl font-bold font-mono">{psr !== null ? psr.toFixed(2) : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {psr !== null && psr > 0 ? (psr < 1 ? '저평가' : psr > 3 ? '고평가' : '적정') : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 수익성 지표 */}
      <div className="pt-6 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-4">💰 수익성 지표</h4>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">ROE (자기자본이익률)</p>
              <p className="text-2xl font-bold font-mono">{roe !== null ? `${roe.toFixed(1)}%` : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {roe !== null ? (roe >= 15 ? '우수 (15%↑)' : roe >= 10 ? '양호 (10%↑)' : '저조') : '-'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">영업이익률</p>
              <p className="text-2xl font-bold font-mono">{opMargin !== null ? `${opMargin.toFixed(1)}%` : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {opMargin !== null ? (opMargin >= 15 ? '우수 (15%↑)' : opMargin >= 8 ? '양호 (8%↑)' : '저조') : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 성장성 지표 */}
      <div className="pt-6 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-4">📊 성장성 지표</h4>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">매출성장률 (YoY)</p>
              <p className={cn('text-2xl font-bold font-mono', (revenueGrowth || 0) >= 0 ? 'text-green-600' : 'text-red-600')}>
                {revenueGrowth !== null ? `${revenueGrowth > 0 ? '+' : ''}${revenueGrowth.toFixed(1)}%` : '-'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">영업이익성장률 (YoY)</p>
              <p className={cn('text-2xl font-bold font-mono', (opGrowth || 0) >= 0 ? 'text-green-600' : 'text-red-600')}>
                {opGrowth !== null ? `${opGrowth > 0 ? '+' : ''}${opGrowth.toFixed(1)}%` : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 안정성 지표 */}
      <div className="pt-6 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-4">🛡️ 안정성 지표</h4>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">부채비율</p>
              <p className="text-2xl font-bold font-mono">{debtRatio !== null ? `${debtRatio.toFixed(1)}%` : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {debtRatio !== null ? (debtRatio <= 100 ? '안정 (100%↓)' : debtRatio <= 200 ? '보통' : '위험 (200%↑)') : '-'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">유동비율</p>
              <p className="text-2xl font-bold font-mono">{currentRatio !== null ? `${currentRatio.toFixed(1)}%` : '-'}</p>
              <p className="text-xs text-gray-400 mt-1">
                {currentRatio !== null ? (currentRatio >= 200 ? '안정 (200%↑)' : currentRatio >= 100 ? '보통' : '위험 (100%↓)') : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ===== 감정분석 탭 컴포넌트 =====
interface SentimentAnalysisTabProps {
  details: {
    details?: Record<string, { score: number; max: number; description: string }>
    newsCount?: number
    hasData?: boolean
    dataInsufficient?: boolean
    source?: 'manual' | 'auto'
    totalScore?: number
    maxScore?: number
    manualRating?: {
      avgRating: number
      ratedCount: number
    } | null
  }
  stockCode: string
  stockName: string
}

function SentimentAnalysisTab({ details, stockCode, stockName }: SentimentAnalysisTabProps) {
  const detailItems = details?.details || {}
  const isManual = details?.source === 'manual'
  const manualRating = details?.manualRating

  // 점수 계산
  const totalScore = isManual && manualRating
    ? details?.totalScore || 10
    : (detailItems.sentiment?.score || 0) + (detailItems.impact?.score || 0) + (detailItems.volume?.score || 0)

  // 점수 기반 감정 상태 판단
  const getTotalSentiment = () => {
    const max = 20

    if (totalScore >= max * 0.7) return { status: '매우 긍정적', color: 'text-green-600', bg: 'bg-green-100' }
    if (totalScore >= max * 0.5) return { status: '긍정적', color: 'text-green-500', bg: 'bg-green-50' }
    if (totalScore >= max * 0.3) return { status: '중립', color: 'text-gray-600', bg: 'bg-gray-100' }
    return { status: '부정적', color: 'text-red-600', bg: 'bg-red-50' }
  }

  const sentimentStatus = getTotalSentiment()

  return (
    <div className="space-y-6">
      {/* 현재 감정 점수 요약 */}
      <div className={cn('p-6 rounded-lg', sentimentStatus.bg)}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm text-gray-500">현재 시장 감정</p>
              <span className={cn(
                'px-2 py-0.5 text-xs rounded-full font-medium',
                isManual ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-600'
              )}>
                {isManual ? '수동 평점' : '자동 분석'}
              </span>
            </div>
            <p className={cn('text-2xl font-bold', sentimentStatus.color)}>{sentimentStatus.status}</p>
            {isManual && manualRating && (
              <p className="text-sm text-gray-500 mt-1">
                평균 평점: <span className={cn('font-medium', manualRating.avgRating >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {manualRating.avgRating > 0 ? '+' : ''}{manualRating.avgRating.toFixed(1)}
                </span>
                <span className="text-gray-400 ml-2">({manualRating.ratedCount}건 평가)</span>
              </p>
            )}
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500 mb-1">감정분석 점수</p>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-gray-900">
                {totalScore.toFixed(1)}
              </span>
              <span className="text-sm text-gray-500">/ 20</span>
            </div>
          </div>
        </div>
      </div>

      {/* 수동 평점 사용 안내 */}
      {isManual && (
        <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <Activity className="w-5 h-5 text-blue-500 mt-0.5" />
          <div>
            <p className="font-medium text-blue-800">수동 평점이 적용되었습니다</p>
            <p className="text-sm text-blue-600 mt-1">
              {manualRating?.ratedCount || 0}건의 뉴스 평점을 기반으로 감정분석 점수가 계산되었습니다.
              자동 분석 대신 직접 평가한 점수가 총점에 반영됩니다.
            </p>
          </div>
        </div>
      )}

      {/* 점수 카드 - 수동일 때는 하나의 카드만, 자동일 때는 3개 */}
      {isManual ? (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">수동 뉴스 평점 기반 점수</p>
              <p className="text-xs text-gray-500 mt-1">
                평점 범위 -10~+10 → 점수 범위 0~20점으로 변환
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-blue-600">{totalScore.toFixed(1)}</p>
              <p className="text-xs text-gray-400">/ 20점</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(detailItems).map(([key, item]) => (
            <DetailCard
              key={key}
              label={getDetailLabel(key)}
              score={item.score}
              max={item.max}
              description={item.description}
            />
          ))}
        </div>
      )}

      {/* 수동 뉴스 평점 섹션 */}
      <div className="pt-6 border-t border-gray-100">
        <div className="mb-4">
          <h4 className="text-lg font-semibold text-gray-800">📰 뉴스 평점 관리</h4>
          <p className="text-sm text-gray-500 mt-1">
            뉴스를 직접 확인하고 -10(매우 부정)부터 +10(매우 긍정)까지 평점을 부여하세요.
            {!isManual && ' 평점을 입력하면 자동분석 대신 수동 점수가 총점에 반영됩니다.'}
          </p>
        </div>
        <NewsRating stockCode={stockCode} stockName={stockName} />
      </div>
    </div>
  )
}
