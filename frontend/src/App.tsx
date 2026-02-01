import { Routes, Route, Navigate } from 'react-router-dom'
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
import Settings from './pages/Settings'
import { RoonProvider } from './contexts/RoonContext'

function App() {
  return (
    <ErrorBoundary>
      <RoonProvider>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <FloatingRoonController />
          <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
            <Routes>
              <Route path="/" element={<Navigate to="/collection" replace />} />
              <Route path="/collection" element={<Collection />} />
              <Route path="/journal" element={<Journal />} />
              <Route path="/timeline" element={<Timeline />} />
              <Route path="/collections" element={<Collections />} />
              <Route path="/analytics" element={<AnalyticsAdvanced />} />
              <Route path="/analytics-simple" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Box>
        </Box>
      </RoonProvider>
    </ErrorBoundary>
  )
}

export default App
