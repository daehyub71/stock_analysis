import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Edit2, Check, X, Briefcase, TrendingUp, TrendingDown, PieChart, Target, BarChart3 } from 'lucide-react'
import { toast } from 'sonner'
import { portfolioApi, stockApi } from '@/services/api'
import { LoadingPage } from '@/components/common'
import { cn, getGradeColor, getGradeBgColor } from '@/lib/utils'
import type { Portfolio, Grade } from '@/types'

export default function PortfolioPage() {
  const queryClient = useQueryClient()
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAddStockModal, setShowAddStockModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')

  // 포트폴리오 목록 조회
  const { data: portfolios = [], isLoading: portfoliosLoading } = useQuery({
    queryKey: ['portfolios'],
    queryFn: portfolioApi.getPortfolios,
  })

  // 선택된 포트폴리오 상세 조회
  const { data: portfolioDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['portfolio', selectedPortfolio],
    queryFn: () => portfolioApi.getPortfolio(selectedPortfolio!),
    enabled: !!selectedPortfolio,
  })

  // 포트폴리오 점수 조회
  const { data: portfolioScore } = useQuery({
    queryKey: ['portfolioScore', selectedPortfolio],
    queryFn: () => portfolioApi.getScore(selectedPortfolio!),
    enabled: !!selectedPortfolio,
  })

  // 전체 종목 리스트 (종목 추가 모달용)
  const { data: stocksData } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
    enabled: showAddStockModal,
  })

  // === Mutations ===

  const createMutation = useMutation({
    mutationFn: portfolioApi.createPortfolio,
    onSuccess: (data: Portfolio) => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setSelectedPortfolio(data.id)
      setShowCreateModal(false)
      toast.success('포트폴리오가 생성되었습니다')
    },
    onError: () => toast.error('포트폴리오 생성에 실패했습니다'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string } }) =>
      portfolioApi.updatePortfolio(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setEditingId(null)
      toast.success('이름이 수정되었습니다')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: portfolioApi.deletePortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setSelectedPortfolio(null)
      toast.success('포트폴리오가 삭제되었습니다')
    },
    onError: () => toast.error('포트폴리오 삭제에 실패했습니다'),
  })

  const addStockMutation = useMutation({
    mutationFn: ({ portfolioId, stockCode }: { portfolioId: number; stockCode: string }) =>
      portfolioApi.addStock(portfolioId, stockCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio', selectedPortfolio] })
      queryClient.invalidateQueries({ queryKey: ['portfolioScore', selectedPortfolio] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setShowAddStockModal(false)
      toast.success('종목이 추가되었습니다')
    },
    onError: () => toast.error('종목 추가에 실패했습니다'),
  })

  const removeStockMutation = useMutation({
    mutationFn: ({ portfolioId, stockCode }: { portfolioId: number; stockCode: string }) =>
      portfolioApi.removeStock(portfolioId, stockCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio', selectedPortfolio] })
      queryClient.invalidateQueries({ queryKey: ['portfolioScore', selectedPortfolio] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      toast.success('종목이 제거되었습니다')
    },
    onError: () => toast.error('종목 제거에 실패했습니다'),
  })

  const updateWeightMutation = useMutation({
    mutationFn: ({ portfolioId, stockCode, weight }: { portfolioId: number; stockCode: string; weight: number }) =>
      portfolioApi.updateWeight(portfolioId, stockCode, weight),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio', selectedPortfolio] })
      queryClient.invalidateQueries({ queryKey: ['portfolioScore', selectedPortfolio] })
    },
    onError: () => toast.error('비중 수정에 실패했습니다'),
  })

  // === Handlers ===

  const handleDeletePortfolio = (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleWeightChange = (stockCode: string, value: string) => {
    const weight = parseFloat(value)
    if (isNaN(weight) || weight < 0 || weight > 100 || !selectedPortfolio) return
    updateWeightMutation.mutate({ portfolioId: selectedPortfolio, stockCode, weight })
  }

  const stocks = portfolioDetail?.stocks || []
  const totalWeight = stocks.reduce((sum, s) => sum + (s.weight || 0), 0)

  if (portfoliosLoading) {
    return <LoadingPage />
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">포트폴리오</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">나만의 관심 종목 그룹을 관리하세요</p>
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">내 포트폴리오</h3>

          {portfolios.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <Briefcase className="w-12 h-12 text-gray-300 dark:text-gray-500 mx-auto mb-3" />
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
                      ? 'bg-primary-50 dark:bg-primary-900/30 border border-primary-200 dark:border-primary-800'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700 border border-transparent'
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
                          className="flex-1 px-2 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded dark:bg-gray-700 dark:text-gray-100"
                          autoFocus
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            updateMutation.mutate({ id: portfolio.id, data: { name: editName } })
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
                          className="p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">{portfolio.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{portfolio.stock_count || 0}개 종목</p>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingId(portfolio.id)
                              setEditName(portfolio.name)
                            }}
                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeletePortfolio(portfolio.id)
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
          {selectedPortfolio && portfolioDetail ? (
            <>
              {/* Score & Stats Cards */}
              {stocks.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
                      <Target className="w-4 h-4 text-blue-500" />
                      평균 점수
                    </div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {portfolioScore?.avg_score?.toFixed(1) || portfolioDetail.avg_score?.toFixed(1) || '-'}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
                      <BarChart3 className="w-4 h-4 text-purple-500" />
                      가중 평균
                    </div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {portfolioScore?.weighted_score?.toFixed(1) || '-'}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
                      <TrendingUp className="w-4 h-4 text-red-500" />
                      최고 점수
                    </div>
                    <p className="text-2xl font-bold text-red-600">
                      {portfolioScore?.max_score?.toFixed(1) || '-'}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
                      <TrendingDown className="w-4 h-4 text-blue-500" />
                      최저 점수
                    </div>
                    <p className="text-2xl font-bold text-blue-600">
                      {portfolioScore?.min_score?.toFixed(1) || '-'}
                    </p>
                  </div>
                </div>
              )}

              {/* Weight Bar */}
              {stocks.length > 0 && totalWeight > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">비중 합계</span>
                    <span className={cn(
                      'text-sm font-bold',
                      Math.abs(totalWeight - 100) < 0.1 ? 'text-green-600' : 'text-amber-600'
                    )}>
                      {totalWeight.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className={cn(
                        'h-2.5 rounded-full transition-all',
                        Math.abs(totalWeight - 100) < 0.1 ? 'bg-green-500' : totalWeight > 100 ? 'bg-red-500' : 'bg-blue-500'
                      )}
                      style={{ width: `${Math.min(totalWeight, 100)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Sector Distribution */}
              {portfolioDetail.sector_distribution && Object.keys(portfolioDetail.sector_distribution).length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <PieChart className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">업종 분포</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(portfolioDetail.sector_distribution).map(([sector, count]) => (
                      <span
                        key={sector}
                        className="px-2.5 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full"
                      >
                        {sector} ({count})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Stock List */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {portfolioDetail.name} ({stocks.length}개)
                  </h3>
                  <button
                    onClick={() => setShowAddStockModal(true)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    종목 추가
                  </button>
                </div>

                {stocks.length === 0 ? (
                  <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                    <PieChart className="w-12 h-12 text-gray-300 dark:text-gray-500 mx-auto mb-3" />
                    <p>아직 종목이 없습니다</p>
                    <button
                      onClick={() => setShowAddStockModal(true)}
                      className="mt-2 text-primary-600 hover:text-primary-700"
                    >
                      종목 추가하기
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Table Header */}
                    <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-700/50 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                      <div className="col-span-3">종목</div>
                      <div className="col-span-2 text-center">등급</div>
                      <div className="col-span-2 text-center">점수</div>
                      <div className="col-span-2 text-center">비중(%)</div>
                      <div className="col-span-2 text-center">업종</div>
                      <div className="col-span-1"></div>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-gray-700">
                      {stocks.map((stock) => (
                        <div key={stock.stock_code} className="grid grid-cols-1 md:grid-cols-12 gap-2 p-4 items-center hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <div className="col-span-3">
                            <p className="font-medium text-gray-900 dark:text-gray-100">{stock.stock_name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{stock.stock_code}</p>
                          </div>
                          <div className="col-span-2 text-center">
                            <span
                              className={cn(
                                'px-2 py-0.5 text-xs font-bold rounded',
                                getGradeBgColor(stock.grade),
                                getGradeColor(stock.grade)
                              )}
                            >
                              {stock.grade}
                            </span>
                          </div>
                          <div className="col-span-2 text-center">
                            <p className="font-bold text-gray-900 dark:text-gray-100">
                              {stock.total_score?.toFixed(1) || '-'}
                            </p>
                          </div>
                          <div className="col-span-2 text-center">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="0.1"
                              defaultValue={stock.weight || ''}
                              onBlur={(e) => handleWeightChange(stock.stock_code, e.target.value)}
                              placeholder="0.0"
                              className="w-20 px-2 py-1 text-sm text-center border border-gray-200 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />
                          </div>
                          <div className="col-span-2 text-center">
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {stock.sector || '-'}
                            </span>
                          </div>
                          <div className="col-span-1 text-center">
                            <button
                              onClick={() => selectedPortfolio && removeStockMutation.mutate({
                                portfolioId: selectedPortfolio,
                                stockCode: stock.stock_code,
                              })}
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </>
          ) : selectedPortfolio && detailLoading ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">불러오는 중...</p>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
              <Briefcase className="w-16 h-16 text-gray-300 dark:text-gray-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">포트폴리오를 선택하세요</h3>
              <p className="text-gray-500 dark:text-gray-400">왼쪽에서 포트폴리오를 선택하거나 새로 만드세요</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <CreatePortfolioModal
          onClose={() => setShowCreateModal(false)}
          onCreate={(name) => createMutation.mutate({ name })}
        />
      )}

      {/* Add Stock Modal */}
      {showAddStockModal && selectedPortfolio && (
        <AddStockModal
          stocks={(stocksData?.items || []).filter(
            (s) => !stocks.some((ps) => ps.stock_code === s.code)
          )}
          onClose={() => setShowAddStockModal(false)}
          onAdd={(code) => addStockMutation.mutate({ portfolioId: selectedPortfolio, stockCode: code })}
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
  onCreate: (name: string) => void
}) {
  const [name, setName] = useState('')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">새 포트폴리오 만들기</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">이름</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 성장주 포트폴리오"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            취소
          </button>
          <button
            onClick={() => name && onCreate(name)}
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
  stocks: Array<{ code: string; name: string; analysis?: { grade?: string } }>
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
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3">종목 추가</h3>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="종목명 또는 코드 검색..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100"
            autoFocus
          />
        </div>

        <div className="max-h-80 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="p-4 text-center text-gray-500 dark:text-gray-400">검색 결과가 없습니다</p>
          ) : (
            filtered.slice(0, 20).map((stock) => (
              <button
                key={stock.code}
                onClick={() => onAdd(stock.code)}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-50 dark:border-gray-700"
              >
                <div className="text-left">
                  <p className="font-medium text-gray-900 dark:text-gray-100">{stock.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{stock.code}</p>
                </div>
                {stock.analysis?.grade && (
                  <span
                    className={cn(
                      'px-2 py-0.5 text-xs font-bold rounded',
                      getGradeBgColor(stock.analysis.grade as Grade),
                      getGradeColor(stock.analysis.grade as Grade)
                    )}
                  >
                    {stock.analysis.grade}
                  </span>
                )}
              </button>
            ))
          )}
        </div>

        <div className="p-4 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={onClose}
            className="w-full py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
