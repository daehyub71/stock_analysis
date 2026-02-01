import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Trash2, Edit2, Check, X, Briefcase, TrendingUp, TrendingDown, PieChart } from 'lucide-react'
import { stockApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, formatNumber, formatPercent, getGradeColor, getGradeBgColor, getPriceChangeColor } from '@/lib/utils'
import type { Stock, AnalysisResult } from '@/types'

interface Portfolio {
  id: string
  name: string
  description: string
  stocks: string[]
  createdAt: string
}

interface StockWithAnalysis extends Stock {
  analysis: AnalysisResult
}

// 로컬 스토리지 키
const PORTFOLIOS_KEY = 'stock_analysis_portfolios'

// 포트폴리오 저장/로드 함수
const loadPortfolios = (): Portfolio[] => {
  const data = localStorage.getItem(PORTFOLIOS_KEY)
  return data ? JSON.parse(data) : []
}

const savePortfolios = (portfolios: Portfolio[]) => {
  localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios))
}

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>(loadPortfolios)
  const [selectedPortfolio, setSelectedPortfolio] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAddStockModal, setShowAddStockModal] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

  // 전체 종목 리스트 조회
  const { data: stocksData, isLoading: stocksLoading } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  const allStocks = stocksData?.items || []
  const currentPortfolio = portfolios.find((p) => p.id === selectedPortfolio)

  // 현재 포트폴리오의 종목들
  const portfolioStocks = currentPortfolio
    ? allStocks.filter((s) => currentPortfolio.stocks.includes(s.code))
    : []

  // 포트폴리오 통계 계산
  const calculateStats = (stocks: StockWithAnalysis[]) => {
    if (stocks.length === 0) return null

    const scores = stocks.map((s) => s.analysis?.totalScore || 0)
    const priceChanges = stocks.map((s) => s.priceChangeRate || 0)
    const upCount = priceChanges.filter((c) => c > 0).length
    const downCount = priceChanges.filter((c) => c < 0).length

    return {
      avgScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      maxScore: Math.max(...scores),
      minScore: Math.min(...scores),
      avgPriceChange: priceChanges.reduce((a, b) => a + b, 0) / priceChanges.length,
      upCount,
      downCount,
    }
  }

  const stats = calculateStats(portfolioStocks as StockWithAnalysis[])

  // 포트폴리오 생성
  const createPortfolio = (name: string, description: string) => {
    const newPortfolio: Portfolio = {
      id: Date.now().toString(),
      name,
      description,
      stocks: [],
      createdAt: new Date().toISOString(),
    }
    const updated = [...portfolios, newPortfolio]
    setPortfolios(updated)
    savePortfolios(updated)
    setSelectedPortfolio(newPortfolio.id)
    setShowCreateModal(false)
  }

  // 포트폴리오 삭제
  const deletePortfolio = (id: string) => {
    const updated = portfolios.filter((p) => p.id !== id)
    setPortfolios(updated)
    savePortfolios(updated)
    if (selectedPortfolio === id) {
      setSelectedPortfolio(updated.length > 0 ? updated[0].id : null)
    }
  }

  // 포트폴리오 이름 수정
  const updatePortfolioName = (id: string, name: string) => {
    const updated = portfolios.map((p) => (p.id === id ? { ...p, name } : p))
    setPortfolios(updated)
    savePortfolios(updated)
    setEditingId(null)
  }

  // 종목 추가
  const addStock = (code: string) => {
    if (!currentPortfolio || currentPortfolio.stocks.includes(code)) return

    const updated = portfolios.map((p) =>
      p.id === currentPortfolio.id ? { ...p, stocks: [...p.stocks, code] } : p
    )
    setPortfolios(updated)
    savePortfolios(updated)
    setShowAddStockModal(false)
  }

  // 종목 제거
  const removeStock = (code: string) => {
    if (!currentPortfolio) return

    const updated = portfolios.map((p) =>
      p.id === currentPortfolio.id
        ? { ...p, stocks: p.stocks.filter((c) => c !== code) }
        : p
    )
    setPortfolios(updated)
    savePortfolios(updated)
  }

  if (stocksLoading) {
    return <LoadingPage />
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">포트폴리오</h1>
          <p className="text-gray-500 mt-1">나만의 관심 종목 그룹을 관리하세요</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          새 포트폴리오
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Portfolio List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <h3 className="font-medium text-gray-900 mb-4">내 포트폴리오</h3>

          {portfolios.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p>포트폴리오가 없습니다</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-2 text-primary-600 hover:text-primary-700"
              >
                새로 만들기
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {portfolios.map((portfolio) => (
                <div
                  key={portfolio.id}
                  className={cn(
                    'p-3 rounded-lg cursor-pointer transition-colors',
                    selectedPortfolio === portfolio.id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  )}
                  onClick={() => setSelectedPortfolio(portfolio.id)}
                >
                  <div className="flex items-center justify-between">
                    {editingId === portfolio.id ? (
                      <div className="flex items-center gap-2 flex-1">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="flex-1 px-2 py-1 text-sm border border-gray-200 rounded"
                          autoFocus
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            updatePortfolioName(portfolio.id, editName)
                          }}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingId(null)
                          }}
                          className="p-1 text-gray-400 hover:bg-gray-100 rounded"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div>
                          <p className="font-medium text-gray-900">{portfolio.name}</p>
                          <p className="text-xs text-gray-500">{portfolio.stocks.length}개 종목</p>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingId(portfolio.id)
                              setEditName(portfolio.name)
                            }}
                            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (confirm('정말 삭제하시겠습니까?')) {
                                deletePortfolio(portfolio.id)
                              }
                            }}
                            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Portfolio Detail */}
        <div className="lg:col-span-3 space-y-6">
          {currentPortfolio ? (
            <>
              {/* Stats Cards */}
              {stats && portfolioStocks.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                    <p className="text-sm text-gray-500 mb-1">평균 점수</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.avgScore.toFixed(1)}</p>
                  </div>
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                    <p className="text-sm text-gray-500 mb-1">평균 등락률</p>
                    <p
                      className={cn(
                        'text-2xl font-bold',
                        getPriceChangeColor(stats.avgPriceChange)
                      )}
                    >
                      {formatPercent(stats.avgPriceChange)}
                    </p>
                  </div>
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                      <TrendingUp className="w-4 h-4 text-red-500" />
                      상승
                    </div>
                    <p className="text-2xl font-bold text-red-600">{stats.upCount}개</p>
                  </div>
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                      <TrendingDown className="w-4 h-4 text-blue-500" />
                      하락
                    </div>
                    <p className="text-2xl font-bold text-blue-600">{stats.downCount}개</p>
                  </div>
                </div>
              )}

              {/* Stock List */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h3 className="font-medium text-gray-900">
                    {currentPortfolio.name} ({portfolioStocks.length}개)
                  </h3>
                  <button
                    onClick={() => setShowAddStockModal(true)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    종목 추가
                  </button>
                </div>

                {portfolioStocks.length === 0 ? (
                  <div className="p-12 text-center text-gray-500">
                    <PieChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p>아직 종목이 없습니다</p>
                    <button
                      onClick={() => setShowAddStockModal(true)}
                      className="mt-2 text-primary-600 hover:text-primary-700"
                    >
                      종목 추가하기
                    </button>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {portfolioStocks.map((stock) => (
                      <div key={stock.code} className="p-4 flex items-center justify-between hover:bg-gray-50">
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="font-medium text-gray-900">{stock.name}</p>
                            <p className="text-sm text-gray-500">{stock.code}</p>
                          </div>
                          {stock.analysis && (
                            <span
                              className={cn(
                                'px-2 py-0.5 text-xs font-bold rounded',
                                getGradeBgColor(stock.analysis.grade),
                                getGradeColor(stock.analysis.grade)
                              )}
                            >
                              {stock.analysis.grade}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="font-mono text-gray-900">
                              {stock.currentPrice ? formatNumber(stock.currentPrice) : '-'}원
                            </p>
                            <p
                              className={cn(
                                'text-sm font-mono',
                                getPriceChangeColor(stock.priceChangeRate || 0)
                              )}
                            >
                              {stock.priceChangeRate !== undefined
                                ? formatPercent(stock.priceChangeRate)
                                : '-'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-500">점수</p>
                            <p className="font-bold text-gray-900">
                              {stock.analysis?.totalScore?.toFixed(1) || '-'}
                            </p>
                          </div>
                          <button
                            onClick={() => removeStock(stock.code)}
                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">포트폴리오를 선택하세요</h3>
              <p className="text-gray-500">왼쪽에서 포트폴리오를 선택하거나 새로 만드세요</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <CreatePortfolioModal
          onClose={() => setShowCreateModal(false)}
          onCreate={createPortfolio}
        />
      )}

      {/* Add Stock Modal */}
      {showAddStockModal && currentPortfolio && (
        <AddStockModal
          stocks={allStocks.filter((s) => !currentPortfolio.stocks.includes(s.code))}
          onClose={() => setShowAddStockModal(false)}
          onAdd={addStock}
        />
      )}
    </div>
  )
}

// Create Portfolio Modal
function CreatePortfolioModal({
  onClose,
  onCreate,
}: {
  onClose: () => void
  onCreate: (name: string, description: string) => void
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">새 포트폴리오 만들기</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 성장주 포트폴리오"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">설명 (선택)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="포트폴리오에 대한 설명..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            취소
          </button>
          <button
            onClick={() => name && onCreate(name, description)}
            disabled={!name}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            만들기
          </button>
        </div>
      </div>
    </div>
  )
}

// Add Stock Modal
function AddStockModal({
  stocks,
  onClose,
  onAdd,
}: {
  stocks: StockWithAnalysis[]
  onClose: () => void
  onAdd: (code: string) => void
}) {
  const [search, setSearch] = useState('')

  const filtered = stocks.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.code.includes(search)
  )

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-3">종목 추가</h3>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="종목명 또는 코드 검색..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            autoFocus
          />
        </div>

        <div className="max-h-80 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="p-4 text-center text-gray-500">검색 결과가 없습니다</p>
          ) : (
            filtered.slice(0, 20).map((stock) => (
              <button
                key={stock.code}
                onClick={() => onAdd(stock.code)}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 border-b border-gray-50"
              >
                <div className="text-left">
                  <p className="font-medium text-gray-900">{stock.name}</p>
                  <p className="text-sm text-gray-500">{stock.code}</p>
                </div>
                {stock.analysis && (
                  <span
                    className={cn(
                      'px-2 py-0.5 text-xs font-bold rounded',
                      getGradeBgColor(stock.analysis.grade),
                      getGradeColor(stock.analysis.grade)
                    )}
                  >
                    {stock.analysis.grade}
                  </span>
                )}
              </button>
            ))
          )}
        </div>

        <div className="p-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="w-full py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
