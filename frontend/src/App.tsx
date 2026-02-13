import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Box } from '@mui/material'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/layout/Navbar'
import FloatingRoonController from './components/FloatingRoonController'
import Collection from './pages/Collection'
import Journal from './pages/Journal'
import Timeline from './pages/Timeline'
import Collections from './pages/Collections'
import Analytics from './pages/Analytics'
import AnalyticsAdvanced from './pages/AnalyticsAdvanced'
import Magazine from './pages/Magazine'
import Settings from './pages/Settings'
import ArtistArticle from './pages/ArtistArticle'
import RoonPlayerWindow from './pages/RoonPlayerWindow'
import { RoonProvider } from './contexts/RoonContext'

function App() {
  const location = useLocation()
  const isPopupWindow = location.pathname === '/roon-player'

  return (
    <ErrorBoundary>
      <RoonProvider>
        {isPopupWindow ? (
          // Fenêtre popup sans layout
          <Routes>
            <Route path="/roon-player" element={<RoonPlayerWindow />} />
          </Routes>
        ) : (
          // Application principale avec layout
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <FloatingRoonController />
            <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
              <Routes>
                <Route path="/" element={<Navigate to="/magazine" replace />} />
                <Route path="/magazine" element={<Magazine />} />
                <Route path="/collection" element={<Collection />} />
                <Route path="/journal" element={<Journal />} />
                <Route path="/timeline" element={<Timeline />} />
                <Route path="/collections" element={<Collections />} />
                <Route path="/analytics" element={<AnalyticsAdvanced />} />
                <Route path="/analytics-simple" element={<Analytics />} />
                <Route path="/artist-article" element={<ArtistArticle />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Box>
          </Box>
        )}
      </RoonProvider>
    </ErrorBoundary>
  )
}

export default App
