import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import { useThemeStore } from './stores/useThemeStore'
import Layout from './components/common/Layout'
import { LoadingPage } from './components/common'

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const StockDetailPage = lazy(() => import('./pages/StockDetailPage'))
const ComparePage = lazy(() => import('./pages/ComparePage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'))
const RankingPage = lazy(() => import('./pages/RankingPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const BacktestingPage = lazy(() => import('./pages/BacktestingPage'))

function SuspensePage({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<LoadingPage />}>{children}</Suspense>
}

function App() {
  const isDark = useThemeStore((s) => s.isDark)

  return (
    <>
      <Toaster position="top-right" richColors theme={isDark ? 'dark' : 'light'} />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SuspensePage><Dashboard /></SuspensePage>} />
          <Route path="stocks/:code" element={<SuspensePage><StockDetailPage /></SuspensePage>} />
          <Route path="compare" element={<SuspensePage><ComparePage /></SuspensePage>} />
          <Route path="history" element={<SuspensePage><HistoryPage /></SuspensePage>} />
          <Route path="portfolio" element={<SuspensePage><PortfolioPage /></SuspensePage>} />
          <Route path="ranking" element={<SuspensePage><RankingPage /></SuspensePage>} />
          <Route path="backtest" element={<SuspensePage><BacktestingPage /></SuspensePage>} />
          <Route path="settings" element={<SuspensePage><SettingsPage /></SuspensePage>} />
        </Route>
      </Routes>
    </>
  )
}

export default App
