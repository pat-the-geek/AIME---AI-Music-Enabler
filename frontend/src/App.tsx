import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/layout/Navbar'
import Collection from './pages/Collection'
import Journal from './pages/Journal'
import Timeline from './pages/Timeline'
import Playlists from './pages/Playlists'
import Analytics from './pages/Analytics'
import AnalyticsAdvanced from './pages/AnalyticsAdvanced'
import Settings from './pages/Settings'

function App() {
  return (
    <ErrorBoundary>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/collection" replace />} />
            <Route path="/collection" element={<Collection />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/playlists" element={<Playlists />} />
            <Route path="/analytics" element={<AnalyticsAdvanced />} />
            <Route path="/analytics-simple" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Box>
      </Box>
    </ErrorBoundary>
  )
}

export default App
