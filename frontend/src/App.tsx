import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Navbar from './components/layout/Navbar'
import Collection from './pages/Collection'
import Journal from './pages/Journal'
import Timeline from './pages/Timeline'
import Playlists from './pages/Playlists'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/journal" replace />} />
          <Route path="/collection" element={<Collection />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/playlists" element={<Playlists />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Box>
    </Box>
  )
}

export default App
