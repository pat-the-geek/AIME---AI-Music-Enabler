import { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, Grid } from '@mui/material'
import apiClient from '../api/client'

export default function AnalyticsTest() {
  const [patterns, setPatterns] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching patterns...')
        const response = await apiClient.get('/history/patterns')
        const data = response.data
        console.log('Data received:', data)
        setPatterns(data)
      } catch (err) {
        console.error('Error:', err)
        setError(err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  if (loading) return <Typography>Chargement...</Typography>
  if (error) return <Typography color="error">Erreur: {JSON.stringify(error)}</Typography>

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Test Analytics</Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Total Écoutes</Typography>
              <Typography variant="h4">{patterns?.total_tracks}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Moyenne/Jour</Typography>
              <Typography variant="h4">{patterns?.daily_average}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Jours Actifs</Typography>
              <Typography variant="h4">{patterns?.unique_days}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Peak Hour</Typography>
              <Typography variant="h4">{patterns?.peak_hour}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, p: 2, bgcolor: '#f0f0f0' }}>
        <Typography variant="caption">DEBUG: {JSON.stringify(patterns)}</Typography>
      </Box>
    </Box>
  )
}
