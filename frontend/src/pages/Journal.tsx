import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Avatar,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Chip,
} from '@mui/material'
import { Favorite, FavoriteBorder, ExpandMore } from '@mui/icons-material'
import apiClient from '@/api/client'
import type { ListeningHistory, PaginatedResponse } from '@/types/models'

export default function Journal() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery<PaginatedResponse<ListeningHistory>>({
    queryKey: ['history', page],
    queryFn: async () => {
      const response = await apiClient.get(`/history/tracks?page=${page}&page_size=50`)
      return response.data
    },
  })

  const handleToggleLove = async (trackId: number) => {
    await apiClient.post(`/history/tracks/${trackId}/love`)
    // Refetch data
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
        Journal d'Écoute
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {data?.total || 0} écoutes au total
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {data?.items.map((entry) => (
          <Card key={entry.id}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item>
                  <Avatar
                    src={entry.artist_image}
                    alt={entry.artist}
                    sx={{ width: 60, height: 60 }}
                  />
                </Grid>
                
                <Grid item>
                  <Avatar
                    src={entry.album_image}
                    alt={entry.album}
                    sx={{ width: 60, height: 60 }}
                    variant="rounded"
                  />
                </Grid>

                <Grid item xs>
                  <Typography variant="h6">{entry.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {entry.artist}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {entry.album}
                  </Typography>
                  <Box sx={{ mt: 0.5 }}>
                    <Chip
                      label={entry.date}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={entry.source}
                      size="small"
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  </Box>
                </Grid>

                <Grid item>
                  <IconButton onClick={() => handleToggleLove(entry.id)}>
                    {entry.loved ? (
                      <Favorite color="error" />
                    ) : (
                      <FavoriteBorder />
                    )}
                  </IconButton>
                </Grid>
              </Grid>

              {entry.ai_info && (
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>🤖 Info IA</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">{entry.ai_info}</Typography>
                  </AccordionDetails>
                </Accordion>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  )
}
