import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Bell, Database, RefreshCw, Check, FileSpreadsheet, FileText, Mail, Sun, Moon, Monitor, Send } from 'lucide-react'
import { toast } from 'sonner'
import { stockApi, alertsApi } from '@/services/api'
import { useThemeStore } from '@/stores/useThemeStore'
import { requestNotificationPermission } from '@/lib/notifications'
import { cn } from '@/lib/utils'

interface Settings {
  alertsEnabled: boolean
  scoreChangeAlert: number
  gradeChangeAlert: boolean
  autoRefresh: boolean
  refreshInterval: number
  emailAlertEnabled: boolean
  alertEmail: string
}

const DEFAULT_SETTINGS: Settings = {
  alertsEnabled: true,
  scoreChangeAlert: 5,
  gradeChangeAlert: true,
  autoRefresh: false,
  refreshInterval: 30,
  emailAlertEnabled: false,
  alertEmail: '',
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
  const [emailSending, setEmailSending] = useState(false)
  const { mode, setMode } = useThemeStore()

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

  const handleAlertToggle = async (enabled: boolean) => {
    updateSetting('alertsEnabled', enabled)
    if (enabled) {
      const granted = await requestNotificationPermission()
      if (granted) {
        toast.success('브라우저 알림이 활성화되었습니다.')
      } else {
        toast.info('브라우저 알림 권한이 거부되었습니다. 브라우저 설정에서 변경할 수 있습니다.')
      }
    }
  }

  const handleTestEmail = async () => {
    if (!settings.alertEmail) {
      toast.error('이메일 주소를 입력해주세요.')
      return
    }
    setEmailSending(true)
    try {
      const result = await alertsApi.sendAlertEmail(settings.alertEmail, settings.scoreChangeAlert)
      if (result.sent) {
        toast.success(result.message)
      } else {
        toast.info(result.message)
      }
    } catch {
      toast.error('이메일 발송에 실패했습니다. SMTP 설정을 확인해주세요.')
    } finally {
      setEmailSending(false)
    }
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
      toast.error('내보내기에 실패했습니다.')
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
      toast.error('내보내기에 실패했습니다.')
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">설정</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">앱 설정 및 데이터 관리</p>
        </div>
        {saved && (
          <div className="flex items-center gap-2 text-green-600">
            <Check className="w-4 h-4" />
            <span className="text-sm">저장됨</span>
          </div>
        )}
      </div>

      {/* Data Export */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/40 text-blue-600 rounded-lg">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">데이터 내보내기</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">분석 결과를 파일로 다운로드합니다</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={exportToCSV}
            disabled={exportLoading || !stocksData?.items?.length}
            className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-lg hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileSpreadsheet className="w-6 h-6 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">CSV 내보내기</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Excel에서 열 수 있음</p>
            </div>
          </button>

          <button
            onClick={exportToJSON}
            disabled={exportLoading || !stocksData?.items?.length}
            className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-lg hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-6 h-6 text-orange-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">JSON 내보내기</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">상세 데이터 포함</p>
            </div>
          </button>
        </div>

        {stocksData?.items && (
          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
            {stocksData.items.length}개 종목 데이터 내보내기 가능
          </p>
        )}
      </div>

      {/* Theme Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 rounded-lg">
            <Sun className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">테마 설정</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">화면 테마를 선택합니다</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {([
            { value: 'light' as const, label: '라이트', icon: Sun },
            { value: 'dark' as const, label: '다크', icon: Moon },
            { value: 'system' as const, label: '시스템', icon: Monitor },
          ]).map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors',
                mode === value
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              )}
            >
              <Icon className={cn('w-6 h-6', mode === value ? 'text-primary-600' : 'text-gray-500 dark:text-gray-400')} />
              <span className={cn('text-sm font-medium', mode === value ? 'text-primary-600' : 'text-gray-700 dark:text-gray-300')}>{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Alert Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-amber-100 dark:bg-amber-900/40 text-amber-600 rounded-lg">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">알림 설정</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">점수 변화 및 등급 변화 알림</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">브라우저 알림</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">분석 결과 변화 시 브라우저 알림 수신</p>
            </div>
            <button
              onClick={() => handleAlertToggle(!settings.alertsEnabled)}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.alertsEnabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
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
              <p className="font-medium text-gray-900 dark:text-gray-100">점수 변화 임계값</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">이 이상 변화 시 알림</p>
            </div>
            <select
              value={settings.scoreChangeAlert}
              onChange={(e) => updateSetting('scoreChangeAlert', Number(e.target.value))}
              disabled={!settings.alertsEnabled}
              className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-gray-100 disabled:opacity-50"
            >
              <option value={3}>±3점</option>
              <option value={5}>±5점</option>
              <option value={10}>±10점</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">등급 변화 알림</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">등급 승급/하락 시 알림</p>
            </div>
            <button
              onClick={() => updateSetting('gradeChangeAlert', !settings.gradeChangeAlert)}
              disabled={!settings.alertsEnabled}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.gradeChangeAlert && settings.alertsEnabled
                  ? 'bg-primary-600'
                  : 'bg-gray-200 dark:bg-gray-600',
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

      {/* Email Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-rose-100 dark:bg-rose-900/40 text-rose-600 rounded-lg">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">이메일 알림</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">점수 변화 시 이메일로 알림을 받습니다</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">이메일 알림 활성화</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">점수 변화 시 이메일 발송</p>
            </div>
            <button
              onClick={() => updateSetting('emailAlertEnabled', !settings.emailAlertEnabled)}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.emailAlertEnabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  settings.emailAlertEnabled ? 'translate-x-6' : 'translate-x-0.5'
                )}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">수신 이메일</label>
            <input
              type="email"
              value={settings.alertEmail}
              onChange={(e) => updateSetting('alertEmail', e.target.value)}
              disabled={!settings.emailAlertEnabled}
              placeholder="your@email.com"
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-gray-100 placeholder:text-gray-400 disabled:opacity-50"
            />
          </div>

          <button
            onClick={handleTestEmail}
            disabled={!settings.emailAlertEnabled || !settings.alertEmail || emailSending}
            className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
            <span>{emailSending ? '발송 중...' : '테스트 이메일 발송'}</span>
          </button>
        </div>
      </div>

      {/* Auto Refresh */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-green-100 dark:bg-green-900/40 text-green-600 rounded-lg">
            <RefreshCw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">자동 새로고침</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">데이터 자동 갱신 설정</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">자동 새로고침</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">주기적으로 데이터 갱신</p>
            </div>
            <button
              onClick={() => updateSetting('autoRefresh', !settings.autoRefresh)}
              className={cn(
                'relative w-12 h-6 rounded-full transition-colors',
                settings.autoRefresh ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
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
              <p className="font-medium text-gray-900 dark:text-gray-100">갱신 간격</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">데이터 갱신 주기</p>
            </div>
            <select
              value={settings.refreshInterval}
              onChange={(e) => updateSetting('refreshInterval', Number(e.target.value))}
              disabled={!settings.autoRefresh}
              className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-gray-100 disabled:opacity-50"
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
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/40 text-purple-600 rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">데이터 정보</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">저장된 데이터 현황</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">분석 대상 종목</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {stocksData?.items?.length || 0}개
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">시세 데이터</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">5년치</p>
          </div>
        </div>

        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
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
