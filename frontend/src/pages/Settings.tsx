import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
} from '@mui/material'
import apiClient from '@/api/client'

export default function Settings() {
  const [trackerEnabled, setTrackerEnabled] = useState(false)

  const { data: trackerStatus, isLoading } = useQuery({
    queryKey: ['tracker-status'],
    queryFn: async () => {
      const response = await apiClient.get('/services/tracker/status')
      return response.data
    },
  })

  const startMutation = useMutation({
    mutationFn: () => apiClient.post('/services/tracker/start'),
  })

  const stopMutation = useMutation({
    mutationFn: () => apiClient.post('/services/tracker/stop'),
  })

  const handleToggleTracker = async () => {
    if (trackerStatus?.running) {
      await stopMutation.mutateAsync()
    } else {
      await startMutation.mutateAsync()
    }
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tracker Last.fm
          </Typography>
          
          {trackerStatus?.running ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              Le tracker est en cours d'exécution
            </Alert>
          ) : (
            <Alert severity="info" sx={{ mb: 2 }}>
              Le tracker est arrêté
            </Alert>
          )}

          <Button
            variant="contained"
            onClick={handleToggleTracker}
            disabled={startMutation.isPending || stopMutation.isPending}
          >
            {trackerStatus?.running ? 'Arrêter' : 'Démarrer'} le Tracker
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            À propos
          </Typography>
          <Typography variant="body2" color="text.secondary">
            AIME - AI Music Enabler v4.0.0
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Application React + FastAPI pour le suivi d'écoute musicale
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
