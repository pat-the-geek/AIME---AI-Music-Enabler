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
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Tabs,
  Tab
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
  AreaChart,
  Area
} from 'recharts'
import apiClient from '../api/client'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function AnalyticsAdvanced() {
  // Calculer les dates par défaut (90 derniers jours)
  const getDefaultDates = () => {
    const today = new Date()
    const endDate = today.toISOString().split('T')[0]
    const startDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    return { startDate, endDate }
  }

  const getComparisonDates = () => {
    const today = new Date()
    const endDate = today.toISOString().split('T')[0]
    const midDate = new Date(today.getTime() - 45 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    const startDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    return { startDate, midDate, endDate }
  }

  const { startDate: defaultStart, endDate: defaultEnd } = getDefaultDates()

  const [tabValue, setTabValue] = useState(0)
  const [haikuDays, setHaikuDays] = useState(7)
  const [startDate, setStartDate] = useState(defaultStart)
  const [endDate, setEndDate] = useState(defaultEnd)
  const { startDate: compStartDate, midDate: compMidDate, endDate: compEndDate } = getComparisonDates()

  const [period1Start, setPeriod1Start] = useState(compStartDate)
  const [period1End, setPeriod1End] = useState(compMidDate)
  const [period2Start, setPeriod2Start] = useState(compMidDate)
  const [period2End, setPeriod2End] = useState(compEndDate)

  // Patterns d'écoute
  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['listening-patterns'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/history/patterns')
        console.log('✅ Patterns data:', response.data)
        return response.data
      } catch (error) {
        console.error('❌ Error fetching patterns:', error)
        return null
      }
    }
  })

  // Stats avancées
  const { data: advancedStats } = useQuery({
    queryKey: ['advanced-stats', startDate, endDate],
    queryFn: async () => {
      try {
        console.log('📊 Fetching advanced stats:', { startDate, endDate })
        const response = await apiClient.get('/analytics/advanced-stats', {
          params: { start_date: startDate, end_date: endDate }
        })
        console.log('✅ Advanced stats data:', response.data)
        return response.data
      } catch (error) {
        console.error('❌ Error fetching advanced stats:', error)
        return null
      }
    },
    enabled: !!startDate && !!endDate
  })

  // Stats découverte
  const { data: discoveryStats } = useQuery({
    queryKey: ['discovery-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/discovery-stats', {
        params: { days: 30 }
      })
      return response.data
    }
  })

  // Heatmap
  const { data: heatmap } = useQuery({
    queryKey: ['listening-heatmap'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/listening-heatmap', {
        params: { days: 90 }
      })
      return response.data
    }
  })

  // Mood timeline
  const { data: moodTimeline } = useQuery({
    queryKey: ['mood-timeline'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/mood-timeline', {
        params: { days: 30 }
      })
      return response.data
    }
  })

  // Haïku
  const { data: haiku, isLoading: haikuLoading, refetch: refetchHaiku } = useQuery({
    queryKey: ['haiku', haikuDays],
    queryFn: async () => {
      const response = await apiClient.get(`/history/haiku?days=${haikuDays}`)
      return response.data
    },
    enabled: false
  })

  // Comparison
  const { data: comparisonData } = useQuery({
    queryKey: ['comparison', period1Start, period1End, period2Start, period2End],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/comparison', {
        params: {
          period1_start: period1Start,
          period1_end: period1End,
          period2_start: period2Start,
          period2_end: period2End
        }
      })
      return response.data
    },
    enabled: !!period1Start && !!period1End && !!period2Start && !!period2End
  })

  // Préparer les données pour les graphiques
  const hourlyData = patterns?.hourly_patterns
    ? Object.entries(patterns.hourly_patterns).map(([hour, count]) => ({
        hour: `${hour}h`,
        écoutes: count
      }))
    : []

  const monthlyData = advancedStats?.monthly_trend
    ? Object.entries(advancedStats.monthly_trend).map(([month, count]) => ({
        month,
        écoutes: count
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
        📊 Advanced Analytics Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Analyse complète et comparative de vos habitudes d'écoute
      </Typography>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 3, mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Overview" />
          <Tab label="Advanced Stats" />
          <Tab label="Discovery" />
          <Tab label="Timeline" />
          <Tab label="Comparaison" />
          <Tab label="IA Insights" />
        </Tabs>
      </Box>

      {/* TAB 0: OVERVIEW */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {/* Statistiques générales */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Écoutes
                </Typography>
                <Typography variant="h4">{advancedStats?.period?.total_tracks || patterns?.total_tracks || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Moyenne/Jour
                </Typography>
                <Typography variant="h4">{advancedStats?.period?.avg_per_day || patterns?.daily_average || 0}</Typography>
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
                Patterns par heure
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="écoutes" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Top Artistes */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                🎤 Top Artistes
              </Typography>
              <List dense>
                {(advancedStats?.top_artists || patterns?.top_artists || []).slice(0, 5).map((artist: any, i: number) => (
                  <ListItem key={i}>
                    <ListItemText
                      primary={artist.name}
                      secondary={`${artist.count} écoutes`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* TAB 1: ADVANCED STATS */}
      <TabPanel value={tabValue} index={1}>
        <Stack spacing={3}>
          {/* Date filters */}
          <Stack direction="row" spacing={2}>
            <TextField
              label="Date début"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="Date fin"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Stack>

          <Grid container spacing={3}>
            {/* Stats cards */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Écoutes
                  </Typography>
                  <Typography variant="h4">{advancedStats?.period?.total_tracks}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Moyenne: {advancedStats?.period?.avg_per_day}/jour
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Durée Totale
                  </Typography>
                  <Typography variant="h4">{advancedStats?.total_hours}h</Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Monthly trend */}
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📈 Tendance Mensuelle
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="écoutes" fill="#8884d8" stroke="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Top Artists */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  🎤 Top Artistes
                </Typography>
                <List dense>
                  {advancedStats?.top_artists?.slice(0, 5).map((artist: any, i: number) => (
                    <ListItem key={i}>
                      <ListItemText
                        primary={artist.name}
                        secondary={`${artist.count} écoutes`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Grid>

            {/* Top Genres */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  🎵 Genres
                </Typography>
                <Stack spacing={1}>
                  {advancedStats?.top_genres?.map((genre: any, i: number) => (
                    <Stack key={i} direction="row" justifyContent="space-between">
                      <Typography variant="body2">{genre.genre}</Typography>
                      <Chip label={genre.count} size="small" />
                    </Stack>
                  ))}
                </Stack>
              </Paper>
            </Grid>

            {/* Mood Distribution */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  😊 Mood Distribution
                </Typography>
                <Stack spacing={1}>
                  {Object.entries(advancedStats?.mood_distribution || {}).map(([mood, count]) => (
                    <Stack key={mood} direction="row" justifyContent="space-between">
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {mood}
                      </Typography>
                      <Chip label={count as any} size="small" />
                    </Stack>
                  ))}
                </Stack>
              </Paper>
            </Grid>
          </Grid>
        </Stack>
      </TabPanel>

      {/* TAB 2: DISCOVERY */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Alert severity="info">
              Derniers 30 jours: {discoveryStats?.total_new_artists} nouveaux artistes découverts
            </Alert>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                🆕 Nouveaux Artistes
              </Typography>
              <List>
                {discoveryStats?.new_artists?.slice(0, 10).map((artist: any, i: number) => (
                  <ListItem key={i}>
                    <ListItemText
                      primary={artist.name}
                      secondary={`Découvert: ${new Date(artist.first_listened).toLocaleDateString('fr-FR')}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                🔄 Artistes Réécoutés
              </Typography>
              <List>
                {discoveryStats?.most_replayed?.slice(0, 10).map((artist: any, i: number) => (
                  <ListItem key={i}>
                    <ListItemText
                      primary={artist.name}
                      secondary={`${artist.count} écoutes`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* TAB 3: TIMELINE */}
      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          {/* Heatmap */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                🔥 Heatmap Écoutes (90 jours)
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={heatmap?.data || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="hour" type="category" />
                  <Tooltip />
                  <Bar dataKey="Monday" stackId="a" fill="#8884d8" />
                  <Bar dataKey="Tuesday" stackId="a" fill="#82ca9d" />
                  <Bar dataKey="Wednesday" stackId="a" fill="#ffc658" />
                  <Bar dataKey="Thursday" stackId="a" fill="#ff7c7c" />
                  <Bar dataKey="Friday" stackId="a" fill="#0099ff" />
                  <Bar dataKey="Saturday" stackId="a" fill="#ffb300" />
                  <Bar dataKey="Sunday" stackId="a" fill="#ff99cc" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Mood Timeline */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                😊 Timeline des Moods
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={moodTimeline?.data || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="energetic" stackId="1" fill="#ff7c7c" />
                  <Area type="monotone" dataKey="calm" stackId="1" fill="#82ca9d" />
                  <Area type="monotone" dataKey="melancholic" stackId="1" fill="#8884d8" />
                  <Area type="monotone" dataKey="joyful" stackId="1" fill="#ffc658" />
                </AreaChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* TAB 4: COMPARISON */}
      <TabPanel value={tabValue} index={4}>
        <Stack spacing={3}>
          <Alert severity="info">
            Comparez deux périodes pour voir comment vos habitudes d'écoute ont évolué
          </Alert>

          {/* Period 1 */}
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Typography variant="h6" gutterBottom>📅 Période 1</Typography>
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <TextField
                label="Début"
                type="date"
                value={period1Start}
                onChange={(e) => setPeriod1Start(e.target.value)}
                size="small"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Fin"
                type="date"
                value={period1End}
                onChange={(e) => setPeriod1End(e.target.value)}
                size="small"
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
          </Paper>

          {/* Period 2 */}
          <Paper sx={{ p: 3, bgcolor: '#f0f0f0' }}>
            <Typography variant="h6" gutterBottom>📅 Période 2</Typography>
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <TextField
                label="Début"
                type="date"
                value={period2Start}
                onChange={(e) => setPeriod2Start(e.target.value)}
                size="small"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Fin"
                type="date"
                value={period2End}
                onChange={(e) => setPeriod2End(e.target.value)}
                size="small"
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
          </Paper>

          {comparisonData && (
            <Grid container spacing={3}>
              {/* Comparison Stats */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>Période 1</Typography>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      <strong>Écoutes:</strong> {comparisonData.period1?.total_tracks}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Heures:</strong> {comparisonData.period1?.total_hours}h
                    </Typography>
                    <Typography variant="body2">
                      <strong>Artistes uniques:</strong> {comparisonData.period1?.unique_artists}
                    </Typography>
                  </Stack>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>Période 2</Typography>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      <strong>Écoutes:</strong> {comparisonData.period2?.total_tracks}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Heures:</strong> {comparisonData.period2?.total_hours}h
                    </Typography>
                    <Typography variant="body2">
                      <strong>Artistes uniques:</strong> {comparisonData.period2?.unique_artists}
                    </Typography>
                  </Stack>
                </Paper>
              </Grid>

              {/* Changes */}
              <Grid item xs={12}>
                <Paper sx={{ p: 3, bgcolor: '#fffde7' }}>
                  <Typography variant="h6" gutterBottom>📊 Évolution</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Changement d'écoutes
                        </Typography>
                        <Typography variant="h6" color={comparisonData.changes?.tracks_change >= 0 ? 'success.main' : 'error.main'}>
                          {comparisonData.changes?.tracks_change >= 0 ? '+' : ''}{comparisonData.changes?.tracks_change}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Changement d'heures
                        </Typography>
                        <Typography variant="h6" color={comparisonData.changes?.hours_change >= 0 ? 'success.main' : 'error.main'}>
                          {comparisonData.changes?.hours_change >= 0 ? '+' : ''}{comparisonData.changes?.hours_change}h
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Nouveaux artistes
                        </Typography>
                        <Typography variant="h6" color={comparisonData.changes?.artists_change >= 0 ? 'success.main' : 'error.main'}>
                          {comparisonData.changes?.artists_change >= 0 ? '+' : ''}{comparisonData.changes?.artists_change}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            </Grid>
          )}
        </Stack>
      </TabPanel>

      {/* TAB 5: IA INSIGHTS */}
      <TabPanel value={tabValue} index={5}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
              <Typography variant="h6" gutterBottom>
                🎋 Haïku Musical Généré par IA
              </Typography>

              <Stack direction="row" spacing={2} sx={{ my: 2 }}>
                <Button
                  variant={haikuDays === 7 ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setHaikuDays(7)}
                >
                  7 jours
                </Button>
                <Button
                  variant={haikuDays === 30 ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setHaikuDays(30)}
                >
                  30 jours
                </Button>
                <Button
                  variant={haikuDays === 90 ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setHaikuDays(90)}
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
                  <Alert severity="success" sx={{ mb: 2 }}>
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
                      fontStyle: 'italic',
                      textAlign: 'center'
                    }}
                  >
                    <Typography
                      variant="h5"
                      sx={{
                        whiteSpace: 'pre-line',
                        lineHeight: 2
                      }}
                    >
                      {haiku.haiku}
                    </Typography>
                  </Paper>
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      🎤 Artistes majeurs:
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {haiku.top_artists?.map((artist: string, index: number) => (
                        <Chip key={index} label={artist} size="small" color="primary" />
                      ))}
                    </Stack>
                  </Box>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  )
}
