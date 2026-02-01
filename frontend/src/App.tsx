import { Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Dashboard from './pages/Dashboard'
import StockDetailPage from './pages/StockDetailPage'
import ComparePage from './pages/ComparePage'
import HistoryPage from './pages/HistoryPage'
import PortfolioPage from './pages/PortfolioPage'
import RankingPage from './pages/RankingPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="stocks/:code" element={<StockDetailPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="ranking" element={<RankingPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
