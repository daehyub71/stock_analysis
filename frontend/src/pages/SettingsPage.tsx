import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Bell, Database, RefreshCw, Check, FileSpreadsheet, FileText } from 'lucide-react'
import { stockApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface Settings {
  theme: 'light' | 'dark' | 'system'
  alertsEnabled: boolean
  scoreChangeAlert: number
  gradeChangeAlert: boolean
  autoRefresh: boolean
  refreshInterval: number
}

const DEFAULT_SETTINGS: Settings = {
  theme: 'light',
  alertsEnabled: true,
  scoreChangeAlert: 5,
  gradeChangeAlert: true,
  autoRefresh: false,
  refreshInterval: 30,
}

const SETTINGS_KEY = 'stock_analysis_settings'

const loadSettings = (): Settings => {
  const data = localStorage.getItem(SETTINGS_KEY)
  return data ? { ...DEFAULT_SETTINGS, ...JSON.parse(data) } : DEFAULT_SETTINGS
}

const saveSettings = (settings: Settings) => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const [exportLoading, setExportLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  // 종목 데이터 조회
  const { data: stocksData } = useQuery({
    queryKey: ['stocks', 'all'],
    queryFn: () => stockApi.getStocks({ pageSize: 100 }),
  })

  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    const updated = { ...settings, [key]: value }
    setSettings(updated)
    saveSettings(updated)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  // CSV 내보내기
  const exportToCSV = async () => {
    if (!stocksData?.items) return

    setExportLoading(true)
    try {
      const headers = [
        '종목코드',
        '종목명',
        '업종',
        '시장',
        '현재가',
        '등락률',
        '총점',
        '등급',
        '기술분석',
        '기본분석',
        '감정분석',
      ]

      const rows = stocksData.items.map((stock) => [
        stock.code,
        stock.name,
        stock.sector || '',
        stock.market,
        stock.currentPrice || '',
        stock.priceChangeRate?.toFixed(2) || '',
        stock.analysis?.totalScore?.toFixed(1) || '',
        stock.analysis?.grade || '',
        stock.analysis?.scoreBreakdown?.technical?.score?.toFixed(1) || '',
        stock.analysis?.scoreBreakdown?.fundamental?.score?.toFixed(1) || '',
        stock.analysis?.scoreBreakdown?.sentiment?.score?.toFixed(1) || '',
      ])

      const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')

      // BOM 추가 (Excel에서 한글 깨짐 방지)
      const bom = '\uFEFF'
      const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8' })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `stock_analysis_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('내보내기 실패')
    } finally {
      setExportLoading(false)
    }
  }

  // JSON 내보내기
  const exportToJSON = async () => {
    if (!stocksData?.items) return

    setExportLoading(true)
    try {
      const data = stocksData.items.map((stock) => ({
        code: stock.code,
        name: stock.name,
        sector: stock.sector,
        market: stock.market,
        currentPrice: stock.currentPrice,
        priceChangeRate: stock.priceChangeRate,
        analysis: stock.analysis,
      }))

      const json = JSON.stringify(data, null, 2)
      const blob = new Blob([json], { type: 'application/json' })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `stock_analysis_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('내보내기 실패')
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">설정</h1>
          <p className="text-gray-500 mt-1">앱 설정 및 데이터 관리</p>
        </div>
        {saved && (
          <div className="flex items-center gap-2 text-green-600">
            <Check className="w-4 h-4" />
            <span className="text-sm">저장됨</span>
          </div>
        )}
      </div>

      {/* Data Export */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900">데이터 내보내기</h3>
            <p className="text-sm text-gray-500">분석 결과를 파일로 다운로드합니다</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={exportToCSV}
            disabled={exportLoading || !stocksData?.items?.length}
            className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileSpreadsheet className="w-6 h-6 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">CSV 내보내기</p>
              <p className="text-xs text-gray-500">Excel에서 열 수 있음</p>
            </div>
          </button>

          <button
            onClick={exportToJSON}
            disabled={exportLoading || !stocksData?.items?.length}
            className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-6 h-6 text-orange-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">JSON 내보내기</p>
              <p className="text-xs text-gray-500">상세 데이터 포함</p>
            </div>
          </button>
        </div>

        {stocksData?.items && (
          <p className="mt-3 text-sm text-gray-500">
            {stocksData.items.length}개 종목 데이터 내보내기 가능
          </p>
        )}
      </div>

      {/* Alert Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-amber-100 text-amber-600 rounded-lg">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900">알림 설정</h3>
            <p className="text-sm text-gray-500">점수 변화 및 등급 변화 알림</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">알림 활성화</p>
              <p className="text-sm text-gray-500">분석 결과 변화 시 알림 수신</p>
            </div>
            <button
              onClick={() => updateSetting('alertsEnabled', !settings.alertsEnabled)}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.alertsEnabled ? 'bg-primary-600' : 'bg-gray-200'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  settings.alertsEnabled ? 'translate-x-6' : 'translate-x-0.5'
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">점수 변화 임계값</p>
              <p className="text-sm text-gray-500">이 이상 변화 시 알림</p>
            </div>
            <select
              value={settings.scoreChangeAlert}
              onChange={(e) => updateSetting('scoreChangeAlert', Number(e.target.value))}
              disabled={!settings.alertsEnabled}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm disabled:opacity-50"
            >
              <option value={3}>±3점</option>
              <option value={5}>±5점</option>
              <option value={10}>±10점</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">등급 변화 알림</p>
              <p className="text-sm text-gray-500">등급 승급/하락 시 알림</p>
            </div>
            <button
              onClick={() => updateSetting('gradeChangeAlert', !settings.gradeChangeAlert)}
              disabled={!settings.alertsEnabled}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.gradeChangeAlert && settings.alertsEnabled
                  ? 'bg-primary-600'
                  : 'bg-gray-200',
                !settings.alertsEnabled && 'opacity-50'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  settings.gradeChangeAlert && settings.alertsEnabled
                    ? 'translate-x-6'
                    : 'translate-x-0.5'
                )}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Auto Refresh */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-green-100 text-green-600 rounded-lg">
            <RefreshCw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900">자동 새로고침</h3>
            <p className="text-sm text-gray-500">데이터 자동 갱신 설정</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">자동 새로고침</p>
              <p className="text-sm text-gray-500">주기적으로 데이터 갱신</p>
            </div>
            <button
              onClick={() => updateSetting('autoRefresh', !settings.autoRefresh)}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.autoRefresh ? 'bg-primary-600' : 'bg-gray-200'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  settings.autoRefresh ? 'translate-x-6' : 'translate-x-0.5'
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">갱신 간격</p>
              <p className="text-sm text-gray-500">데이터 갱신 주기</p>
            </div>
            <select
              value={settings.refreshInterval}
              onChange={(e) => updateSetting('refreshInterval', Number(e.target.value))}
              disabled={!settings.autoRefresh}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm disabled:opacity-50"
            >
              <option value={15}>15초</option>
              <option value={30}>30초</option>
              <option value={60}>1분</option>
              <option value={300}>5분</option>
            </select>
          </div>
        </div>
      </div>

      {/* Data Info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900">데이터 정보</h3>
            <p className="text-sm text-gray-500">저장된 데이터 현황</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500 mb-1">분석 대상 종목</p>
            <p className="text-2xl font-bold text-gray-900">
              {stocksData?.items?.length || 0}개
            </p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500 mb-1">시세 데이터</p>
            <p className="text-2xl font-bold text-gray-900">5년치</p>
          </div>
        </div>

        <p className="mt-4 text-sm text-gray-500">
          마지막 업데이트: {new Date().toLocaleDateString('ko-KR')}
        </p>
      </div>

      {/* Version */}
      <div className="text-center text-sm text-gray-400">
        <p>VIP 종목분석 대시보드 v1.0.0</p>
        <p>© 2024 Stock Analysis Dashboard</p>
      </div>
    </div>
  )
}
