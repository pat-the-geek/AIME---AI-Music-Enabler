import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack
} from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import apiClient from '../api/client'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658']

export default function Analytics() {
  const [haikuDays, setHaikuDays] = useState(7)

  // Récupérer patterns d'écoute
  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['listening-patterns'],
    queryFn: async () => {
      const response = await apiClient.get('/history/patterns')
      return response.data
    }
  })

  // Récupérer haïku
  const { data: haiku, isLoading: haikuLoading, refetch: refetchHaiku } = useQuery({
    queryKey: ['haiku', haikuDays],
    queryFn: async () => {
      const response = await apiClient.get(`/history/haiku?days=${haikuDays}`)
      return response.data
    },
    enabled: false
  })

  // Préparer données pour graphiques
  const hourlyData = patterns?.hourly_patterns
    ? Object.entries(patterns.hourly_patterns).map(([hour, count]) => ({
        hour: `${hour}h`,
        écoutes: count
      }))
    : []

  const weekdayData = patterns?.weekday_patterns
    ? Object.entries(patterns.weekday_patterns).map(([day, count]) => ({
        name: day,
        value: count as number
      }))
    : []

  if (patternsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        📊 Analytics & Patterns
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Analyse approfondie de vos habitudes d'écoute
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Statistiques générales */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Écoutes
              </Typography>
              <Typography variant="h4">{patterns?.total_tracks || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Moyenne/Jour
              </Typography>
              <Typography variant="h4">{patterns?.daily_average || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Sessions
              </Typography>
              <Typography variant="h4">
                {patterns?.listening_sessions?.total_sessions || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Jours Actifs
              </Typography>
              <Typography variant="h4">{patterns?.unique_days || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Patterns horaires */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Patterns d'écoute par heure
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Heure de pointe: {patterns?.peak_hour}h
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="écoutes" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Patterns par jour */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Par jour de la semaine
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Jour favori: {patterns?.peak_weekday}
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={weekdayData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => entry.name}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {weekdayData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Sessions d'écoute */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📻 Sessions d'écoute
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Moyenne: {patterns?.listening_sessions?.avg_tracks_per_session?.toFixed(1) || 0}{' '}
              tracks/session
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Sessions les plus longues
            </Typography>
            <List>
              {patterns?.listening_sessions?.longest_sessions?.map((session: any, index: number) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={`${session.track_count} tracks`}
                    secondary={`${session.duration_minutes} minutes • ${new Date(
                      session.start_time
                    ).toLocaleString('fr-FR')}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Corrélations artistes */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              🔗 Corrélations d'artistes
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Artistes souvent écoutés ensemble
            </Typography>
            <Divider sx={{ my: 2 }} />
            <List>
              {patterns?.artist_correlations?.map((corr: any, index: number) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip label={corr.artist1} size="small" />
                        <Typography variant="body2">↔</Typography>
                        <Chip label={corr.artist2} size="small" />
                      </Stack>
                    }
                    secondary={`${corr.count} fois ensemble`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Haïku généré par IA */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
            <Typography variant="h6" gutterBottom>
              🎋 Haïku Musical
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Généré par IA basé sur vos écoutes
            </Typography>

            <Stack direction="row" spacing={2} sx={{ my: 2 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setHaikuDays(7)
                  refetchHaiku()
                }}
              >
                7 jours
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setHaikuDays(30)
                  refetchHaiku()
                }}
              >
                30 jours
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setHaikuDays(90)
                  refetchHaiku()
                }}
              >
                90 jours
              </Button>
              <Button variant="contained" onClick={() => refetchHaiku()}>
                Générer
              </Button>
            </Stack>

            {haikuLoading && <CircularProgress size={24} />}

            {haiku && (
              <Box sx={{ mt: 3 }}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Basé sur {haiku.total_tracks} écoutes sur {haiku.period_days} jours
                  </Typography>
                </Alert>
                <Paper
                  elevation={3}
                  sx={{
                    p: 4,
                    bgcolor: 'grey.900',
                    color: 'white',
                    fontFamily: 'serif',
                    fontStyle: 'italic'
                  }}
                >
                  <Typography
                    variant="h5"
                    sx={{
                      whiteSpace: 'pre-line',
                      textAlign: 'center',
                      lineHeight: 2
                    }}
                  >
                    {haiku.haiku}
                  </Typography>
                </Paper>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Top Artistes:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {haiku.top_artists?.map((artist: string, index: number) => (
                      <Chip key={index} label={artist} size="small" />
                    ))}
                  </Stack>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

