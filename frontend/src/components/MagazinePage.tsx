import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Grid, Card, CardContent, CardMedia, Stack, Paper, Avatar, Chip, Button, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import React from 'react'
import ReactMarkdown from 'react-markdown'
import apiClient from '@/api/client'

interface AILayout {
  imagePosition?: string
  imageSize?: string
  columns?: number
  textLayout?: string
  composition?: string
  specialEffect?: string
  accentColor?: string
}

interface PageProps {
  page: {
    page_number: number
    type: string
    title: string
    layout: string | AILayout
    content: any
    dimensions?: any
  }
  index: number
}

export default function MagazinePage({ page, index }: PageProps) {
  // States pour le dialog de sélection de zone
  const [zoneDialogOpen, setZoneDialogOpen] = useState(false)
  const [selectedZone, setSelectedZone] = useState<string>('')
  const [albumToPlay, setAlbumToPlay] = useState<any>(null)

  // Récupérer les zones Roon
  const { data: roonZones } = useQuery({
    queryKey: ['roon-zones'],
    queryFn: async () => {
      const response = await apiClient.get('/roon/zones')
      return response.data?.zones || []
    },
    refetchInterval: 10000,
    refetchOnMount: true,
  })

  // Thème journal unique avec fond blanc
  const colorSchemes: Record<string, { bg: string; text: string; accent: string; secondary: string }> = {
    newspaper: { bg: '#ffffff', text: '#1a1a1a', accent: '#c41e3a', secondary: '#2c3e50' }
  }

  const colorScheme = 'newspaper'
  const colors = colorSchemes.newspaper

  // Fonction pour jouer dans Roon
  const handlePlayInRoon = (album: any) => {
    setAlbumToPlay(album)
    setZoneDialogOpen(true)
  }

  // Fonction pour confirmer et lancer la lecture
  const confirmPlayInRoon = async () => {
    if (!selectedZone || !albumToPlay) return

    try {
      console.log('📤 Envoi à Roon:', { artist_name: albumToPlay.artist_name, album_title: albumToPlay.title, zone: selectedZone })
      
      const response = await fetch('/api/v1/roon/play-album-by-name', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          artist_name: albumToPlay.artist_name || albumToPlay.artist,
          album_title: albumToPlay.title,
          zone_name: selectedZone
        })
      })
      
      const data = await response.json().catch(() => null)
      
      if (response.ok) {
        console.log('✅ Lecture lancée dans Roon:', data)
        alert(`Album lancé : ${albumToPlay.title}`)
      } else {
        console.error('❌ Erreur Roon (Status ' + response.status + '):', data)
        const errorMsg = data?.detail || 'Impossible de lancer la lecture dans Roon'
        alert(`Erreur: ${errorMsg}\n\nDétails: Vérifiez que Roon est en ligne et accessible.`)
      }
    } catch (error) {
      console.error('Erreur API Roon:', error)
      alert(`Erreur de connexion: ${(error as Error).message}`)
    } finally {
      setZoneDialogOpen(false)
      setSelectedZone('')
      setAlbumToPlay(null)
    }
  }

  // Extraire les infos de layout AI
  const aiLayout: AILayout | null = typeof page.layout === 'object' ? page.layout : null
  const imagePosition = aiLayout?.imagePosition || 'left'
  const imageSize = aiLayout?.imageSize || 'medium'
  const textColumns = aiLayout?.columns || page.dimensions?.text_columns || 2
  const textLayout = aiLayout?.textLayout || 'double-column'
  const composition = aiLayout?.composition || 'classic'
  const specialEffect = aiLayout?.specialEffect || 'none'
  const accentColor = aiLayout?.accentColor || colors.accent

  // Calculer taille image selon suggestion IA (jusqu'à 75% de l'écran pour fullscreen)
  const imageSizes = { 
    micro: 100, 
    tiny: 150, 
    small: 200, 
    medium: 300, 
    large: 450, 
    huge: 600, 
    massive: 750,
    fullscreen: typeof window !== 'undefined' ? Math.floor(window.innerHeight * 0.75) : 800
  }
  const imageHeight = imageSizes[imageSize as keyof typeof imageSizes] || 300

  // Déterminer le nombre de colonnes pour le texte
  const getTextColumns = () => {
    if (textLayout === 'triple-column') return 3
    if (textLayout === 'double-column') return 2
    if (textLayout === 'asymmetric') return textColumns
    return 1
  }

  // Page 1: Artist Showcase
  if (page.type === 'artist_showcase') {
    const { artist, albums } = page.content
    
    // Déterminer l'ordre des éléments selon composition
    const isFloating = imagePosition === 'floating'
    const isSplit = imagePosition === 'split'
    const isCenter = imagePosition === 'center'
    const isBottom = imagePosition === 'bottom'
    const isDiagonal = imagePosition === 'diagonal'
    const isCorner = imagePosition === 'corner'
    const isFullWidth = imagePosition === 'fullwidth'
    const isMassive = ['massive', 'fullscreen', 'huge'].includes(imageSize)

    return (
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px',
        position: 'relative'
      }}>
        <Box sx={{ maxWidth: '1400px', margin: '0 auto', width: '100%', position: 'relative' }}>
          {/* Header */}
          <Box sx={{ 
            textAlign: isCenter || isFullWidth ? 'center' : (imagePosition === 'right' || isCorner ? 'right' : 'left'), 
            marginBottom: isMassive ? '60px' : '40px',
            position: isCorner ? 'relative' : 'static',
            zIndex: isCorner ? 10 : 'auto'
          }}>
            <Typography variant="h2" sx={{
              fontFamily: '"Playfair Display", "Georgia", serif',
              fontWeight: 900,
              marginBottom: '16px',
              color: colors.text,
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
              borderBottom: '4px solid #2c3e50',
              paddingBottom: '12px',
              transform: composition === 'dramatic' ? 'skewY(-1deg)' : 
                         isDiagonal ? 'rotate(-1deg)' : 'none',
              fontSize: isMassive ? '3.5rem' : 'inherit'
            }}>
              {page.title}
            </Typography>
            <Typography variant="h5" sx={{ 
              fontFamily: '"Merriweather", "Georgia", serif',
              color: '#2c3e50',
              fontWeight: 400,
              fontStyle: 'italic'
            }}>
              {artist.albums_count} albums
            </Typography>
          </Box>

          <Grid container spacing={4} sx={{ position: 'relative' }}>
            {/* Photo d'artiste - GRANDE image avec taille variable */}
            {artist.image_url && (
              <Grid item xs={12} 
                md={isCenter || isFullWidth ? 12 : (imagePosition === 'top' || imagePosition === 'bottom' ? 12 : isMassive ? 12 : (imageSize === 'huge' ? 7 : imageSize === 'massive' ? 8 : 5))}
                order={imagePosition === 'bottom' ? 3 : 1}
              >
                <Box sx={{
                  position: 'relative',
                  paddingBottom: isMassive ? '75%' : (imagePosition === 'top' ? '50%' : (imageSize === 'fullscreen' ? '90%' : '110%')),  // Varier les hauteurs
                  backgroundColor: 'rgba(0,0,0,0.05)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                  border: '1px solid #d0d0d0',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.01)',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
                  }
                }}>
                  <Box
                    component="img"
                    src={artist.image_url}
                    alt={artist.name}
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover'
                    }}
                  />
                </Box>
              </Grid>
            )}

            {/* Haiku - Position dynamique selon layout IA */}
            <Grid item xs={12} 
              md={isCenter || isFloating || isFullWidth ? 12 : (imagePosition === 'top' || imagePosition === 'bottom' ? 12 : isMassive ? 12 : 4)}
              order={isBottom ? 3 : (imagePosition === 'right' || isCorner ? 1 : 2)}
              sx={isFloating || isCorner ? {
                position: { md: 'absolute' },
                top: isCorner ? '5%' : '20%',
                right: isCorner ? '2%' : '5%',
                left: isCorner && imagePosition.includes('left') ? '2%' : 'auto',
                zIndex: 10,
                maxWidth: '350px'
              } : {}}
            >
              <Paper elevation={0} sx={{
                background: '#f8f8f8',
                border: '1px solid #d0d0d0',
                borderLeft: '4px solid #2c3e50',
                padding: isFloating || isCorner ? '24px' : '32px',
                textAlign: 'center',
                borderRadius: '2px',
                height: isFloating || isCorner ? 'auto' : '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                transform: composition === 'playful' ? 'rotate(-1deg)' : 
                           composition === 'chaos' ? `rotate(${Math.random() * 3 - 1.5}deg)` : 'none',
                backdropFilter: isFloating || isCorner ? 'blur(10px)' : 'none',
                transition: 'all 0.3s ease'
              }}>
                <Typography variant={isFloating ? "body1" : "h5"} sx={{
                  fontFamily: '"Crimson Text", "Georgia", serif',
                  fontStyle: 'italic',
                  lineHeight: 2.2,
                  whiteSpace: 'pre-line',
                  color: '#2c3e50',
                  fontWeight: 400,
                  letterSpacing: '0.03em',
                  fontSize: isFloating || isCorner ? '1.1rem' : '1.3rem',
                  '&::before': { content: '"\\201C"', fontSize: '2em', color: '#1a1a1a', lineHeight: 0, marginRight: '4px' },
                  '&::after': { content: '"\\201D"', fontSize: '2em', color: '#1a1a1a', lineHeight: 0, marginLeft: '4px' }
                }}>
                  {artist.haiku}
                </Typography>
              </Paper>
            </Grid>

            {/* Albums Grid - Position et colonnes dynamiques - Photo d'artiste dessus */}
            <Grid item xs={12} 
              md={isCenter || isFloating || isFullWidth ? 12 : (imagePosition === 'top' || imagePosition === 'bottom' ? 12 : isMassive ? 12 : 8)}
              order={isBottom ? 2 : (imagePosition === 'right' || isCorner ? 2 : artist.image_url ? 3 : 1)}
            >
              <Grid container spacing={isSplit || isMassive ? 1 : 2} sx={{ 
                justifyContent: isCenter || isFullWidth ? 'center' : 'flex-start'
              }}>
                {albums.slice(0, isMassive ? 4 : 6).map((album: any, idx: number) => {
                  // Alterner entre layout horizontal et vertical pour plus de variété
                  const isHorizontalLayout = !isSplit && !isMassive && idx % 2 === 0 && album.description
                  
                  return (
                  <Grid item 
                    xs={isHorizontalLayout ? 12 : (isSplit ? 6 : isMassive ? 6 : 6)} 
                    sm={isHorizontalLayout ? 12 : (isSplit ? 4 : isMassive ? 6 : 4)} 
                    md={isHorizontalLayout ? 12 : (isMassive ? 6 : 12 / Math.min(textColumns, isSplit ? 4 : 3))} 
                    key={idx}
                  >
                    <Card elevation={0} sx={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #2c2c2c',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      height: '100%',
                      borderRadius: '2px',
                      display: isHorizontalLayout ? 'flex' : 'block',
                      flexDirection: isHorizontalLayout ? 'row' : 'column',
                      transform: 'none',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        backgroundColor: '#2c2c2c',
                        borderColor: '#444',
                        boxShadow: '0 8px 16px rgba(0,0,0,0.4)'
                      }
                    }}>
                    {album.image_url ? (
                        isHorizontalLayout ? (
                          <Box
                            component="img"
                            src={album.image_url}
                            alt={album.title}
                            sx={{
                              width: { xs: '40%', md: '35%' },
                              minHeight: '250px',
                              objectFit: 'cover',
                              backgroundColor: 'rgba(0,0,0,0.3)'
                            }}
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        ) : (
                          <CardMedia
                            component="img"
                            height={isMassive ? imageHeight * 0.4 : imageHeight * (isSplit ? 0.5 : 0.7)}
                            image={album.image_url}
                            alt={album.title}
                            sx={{ 
                              backgroundColor: 'rgba(0,0,0,0.3)',
                              filter: composition === 'dramatic' ? 'contrast(1.2)' : 
                                      specialEffect === 'blur' ? 'blur(2px)' :
                                      specialEffect === 'zoom' ? 'scale(1.1)' : 'none',
                              transition: 'all 0.3s ease',
                              objectFit: 'cover'
                            }}
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        )
                      ) : (
                        <Box
                          sx={{
                            width: isHorizontalLayout ? { xs: '40%', md: '35%' } : '100%',
                            height: isHorizontalLayout ? '250px' : (isMassive ? imageHeight * 0.4 : imageHeight * (isSplit ? 0.5 : 0.7)),
                            backgroundColor: '#f5f5f5',
                            border: '2px dashed #d0d0d0',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '20px'
                          }}
                        >
                          <Typography variant="h1" sx={{ fontSize: '64px', opacity: 0.25, marginBottom: '8px' }}>🎵</Typography>
                          <Typography variant="body2" sx={{ color: '#999', fontSize: '11px' }}>
                            Image non disponible
                          </Typography>
                        </Box>
                      )}
                      <CardContent sx={{ 
                        padding: isSplit ? '12px' : (isHorizontalLayout ? '24px' : '16px'),
                        flex: isHorizontalLayout ? 1 : 'none',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center'
                      }}>
                        <Typography variant={isSplit ? "body2" : (isHorizontalLayout ? "h6" : "subtitle1")} sx={{ 
                          fontFamily: '"Merriweather", "Georgia", serif',
                          fontWeight: 700, 
                          marginBottom: isHorizontalLayout ? '16px' : '12px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          color: '#ffffff',
                          minHeight: isSplit ? '32px' : 'auto'
                        }}>
                          {album.title}
                        </Typography>
                        {album.description && (
                          <Box sx={{
                            fontFamily: '"Merriweather", "Georgia", serif',
                            color: '#d0d0d0',
                            fontSize: isHorizontalLayout ? '0.95rem' : '0.85rem',
                            marginBottom: '12px',
                            lineHeight: 1.6,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: isHorizontalLayout ? 5 : 3,
                            WebkitBoxOrient: 'vertical',
                            '& p': { margin: 0 },
                            '& strong': { fontWeight: 700, color: '#ffffff' },
                            '& em': { fontStyle: 'italic', color: '#bbb' }
                          }}>
                            <ReactMarkdown>{album.description}</ReactMarkdown>
                          </Box>
                        )}
                        {album.year && (
                          <Chip
                            label={album.year}
                            size="small"
                            sx={{ 
                              fontFamily: '"Roboto Condensed", sans-serif',
                              fontSize: '11px', 
                              height: '22px',
                              backgroundColor: '#2c2c2c',
                              color: '#ffffff',
                              fontWeight: 700,
                              border: '1px solid #444',
                              textTransform: 'uppercase',
                              alignSelf: 'flex-start'
                            }}
                          />
                        )}
                        <Box sx={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <Button
                            size="small"
                            variant="contained"
                            onClick={() => handlePlayInRoon(album)}
                            sx={{
                              backgroundColor: '#23a7dd',
                              color: '#ffffff',
                              fontFamily: '"Roboto Condensed", sans-serif',
                              fontWeight: 700,
                              fontSize: '9px',
                              padding: '2px 6px',
                              height: '18px',
                              minWidth: '40px',
                              textTransform: 'uppercase',
                              '&:hover': {
                                backgroundColor: '#1a8bc4'
                              }
                            }}
                          >
                            ▶ Roon
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                )})}
              </Grid>

              {/* Contenu de remplissage pour espaces vides */}
              {page.content.filler && page.content.filler.length > 0 && (
                <Grid item xs={12} sx={{ mt: 3 }}>
                  <Grid container spacing={2}>
                    {page.content.filler.map((filler: any, idx: number) => (
                      <Grid item xs={12} sm={6} md={4} key={idx}>
                        <Paper elevation={0} sx={{
                          padding: '16px',
                          backgroundColor: filler.type === 'quote' ? '#f9f9f9' : '#ffffff',
                          border: '1px solid #d0d0d0',
                          borderLeft: filler.type === 'quote' ? '4px solid #2c3e50' : '1px solid #d0d0d0',
                          minHeight: '80px',
                          display: 'flex',
                          alignItems: 'center'
                        }}>
                          <Box sx={{
                            '& p': { margin: 0, fontSize: '13px', lineHeight: 1.5, color: '#2c3e50' },
                            '& strong': { fontWeight: 700, color: '#1a1a1a' },
                            '& em': { fontStyle: 'italic', color: '#555' }
                          }}>
                            <ReactMarkdown>{filler.text}</ReactMarkdown>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
              )}
            </Grid>
          </Grid>
        </Box>
      </Box>
    )
  }

  // Page 2: Album Detail
  if (page.type === 'album_detail') {
    const { album } = page.content
    const isImageLeft = imagePosition === 'left'
    const isImageTop = imagePosition === 'top'
    const isMassive = ['massive', 'fullscreen', 'huge'].includes(imageSize)
    const isFullWidth = imagePosition === 'fullwidth'

    return (
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px'
      }}>
        <Box sx={{ maxWidth: isMassive || isFullWidth ? '1600px' : '1200px', margin: '0 auto', width: '100%' }}>
          <Grid container spacing={4} alignItems="flex-start">
            {/* Image */}
            {album.image_url && !isImageTop && (
              <Grid item xs={12} md={isMassive || isFullWidth ? 12 : (imageSize === 'large' ? 6 : 4)} order={isImageLeft ? 1 : 2}>
                <Box sx={{
                  position: 'relative',
                  paddingBottom: isMassive || isFullWidth ? `${(imageHeight / (typeof window !== 'undefined' ? window.innerWidth : 1200)) * 100}%` : '100%',
                  maxHeight: isMassive ? imageHeight : 'none',
                  backgroundColor: 'rgba(0,0,0,0.05)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                  border: '1px solid #d0d0d0',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  transform: 'none',
                  transition: 'all 0.3s ease'
                }}>
                  <Box
                    component="img"
                    src={album.image_url}
                    alt={album.title}
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      filter: specialEffect === 'blur' ? 'blur(1px)' : 
                              specialEffect === 'overlay' ? 'brightness(0.8)' : 'none'
                    }}
                  />
                </Box>
              </Grid>
            )}

            {/* Content */}
            <Grid item xs={12} md={album.image_url && !isImageTop ? (isMassive || isFullWidth ? 12 : (imageSize === 'large' ? 6 : 8)) : 12} order={isImageLeft ? 2 : 1}>
              <Box>
                <Typography variant="h2" sx={{
                  fontFamily: '"Playfair Display", "Georgia", serif',
                  fontWeight: 900,
                  marginBottom: '16px',
                  color: colors.text,
                  letterSpacing: '0.02em',
                  textTransform: 'uppercase',
                  borderBottom: '4px solid #2c3e50',
                  paddingBottom: '12px'
                }}>
                  {album.title}
                </Typography>
                <Typography variant="h4" sx={{ 
                  fontFamily: '"Merriweather", "Georgia", serif',
                  marginBottom: '24px',
                  color: '#2c3e50',
                  fontWeight: 400,
                  fontStyle: 'italic'
                }}>
                  {album.artist}
                  {album.year && ` • ${album.year}`}
                </Typography>

                {album.genre && (
                  <Chip
                    label={album.genre}
                    sx={{
                      fontFamily: '"Roboto Condensed", sans-serif',
                      marginBottom: '24px',
                      backgroundColor: '#f5f5f5',
                      borderColor: '#d0d0d0',
                      color: '#2c3e50',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      height: '28px',
                      border: '1px solid #d0d0d0',
                      textTransform: 'uppercase'
                    }}
                  />
                )}

                {/* Description en colonnes selon layout IA - Style journal avec markdown */}
                <Box sx={{
                  columnCount: { xs: 1, md: textLayout === 'double-column' ? Math.min(textColumns, 3) : 1 },
                  columnGap: '40px',
                  columnRule: '1px solid #d0d0d0',
                  lineHeight: 1.8,
                  color: '#2c3e50',
                  textAlign: 'justify',
                  fontSize: '1.05rem',
                  fontFamily: '"Merriweather", "Georgia", serif',
                  fontWeight: 400,
                  '& p': {
                    marginBottom: '16px',
                    breakInside: 'avoid',
                    textIndent: '2em',
                    '&:first-of-type::first-letter': {
                      fontSize: '3.5em',
                      fontWeight: 700,
                      float: 'left',
                      lineHeight: '0.85',
                      marginRight: '8px',
                      color: '#1a1a1a'
                    }
                  }
                }}>
                  <Typography variant="body1" sx={{ 
                    color: 'inherit',
                    fontSize: 'inherit',
                    lineHeight: 'inherit',
                    fontFamily: 'inherit'
                  }}>
                    {album.description}
                  </Typography>
                </Box>

                {album.style && (
                  <Box sx={{
                    marginTop: '32px',
                    padding: '20px',
                    background: '#f8f8f8',
                    borderRadius: '2px',
                    border: '1px solid #d0d0d0',
                    borderLeft: '4px solid #2c3e50',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                  }}>
                    <Typography variant="subtitle2" sx={{ 
                      marginBottom: '12px',
                      color: '#2c3e50',
                      fontFamily: '"Roboto Condensed", sans-serif',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.15em',
                      fontSize: '0.85rem'
                    }}>
                      Style Musical
                    </Typography>
                    <Typography variant="body1" sx={{ 
                      color: '#2c3e50',
                      fontFamily: '"Merriweather", "Georgia", serif'
                    }}>
                      {album.style}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Box>
    )
  }

  // Page 3: Albums with Haikus
  if (page.type === 'albums_haikus') {
    const { albums, haikus } = page.content

    return (
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px'
      }}>
        <Box sx={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Typography variant="h2" sx={{
          fontFamily: '"Playfair Display", "Georgia", serif',
          fontWeight: 900,
          marginBottom: '48px',
          color: '#1a1a1a',
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
          borderBottom: '4px solid #2c3e50',
          paddingBottom: '12px',
          textAlign: 'center'
        }}>
          {page.title}
        </Typography>

        <Grid container spacing={4}>
          {albums.map((album: any, idx: number) => {
            const haiku = haikus.find((h: any) => h.album_id === album.id)
            return (
              <Grid item xs={12} sm={6} md={4} key={idx}>
                <Card elevation={4} sx={{
                  background: `linear-gradient(135deg, ${colors.bg} 0%, #f5f5f5 100%)`,
                  border: '2px solid #d0d0d0',
                  borderRadius: '16px',
                  overflow: 'hidden',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: `0 12px 32px ${accentColor}60`
                  }
                }}>
                  {album.image_url && (
                    <CardMedia
                      component="img"
                      height={220}
                      image={album.image_url}
                      alt={album.title}
                      sx={{ 
                        backgroundColor: 'rgba(0,0,0,0.3)',
                        borderBottom: '2px solid #d0d0d0'
                      }}
                    />
                  )}
                  <CardContent sx={{ flex: 1, padding: '24px' }}>
                    <Typography variant="h6" sx={{ 
                      fontFamily: '"Merriweather", "Georgia", serif',
                      fontWeight: 700, 
                      marginBottom: '8px',
                      color: '#1a1a1a'
                    }}>
                      {album.title}
                    </Typography>
                    <Typography variant="body2" sx={{ 
                      marginBottom: '20px',
                      color: '#2c3e50',
                      fontWeight: 600
                    }}>
                      {album.artist}
                    </Typography>

                    {haiku && (
                      <Paper elevation={0} sx={{
                        background: `linear-gradient(135deg, #e8e8e8 0%, #f5f5f5 100%)`,
                        padding: '16px',
                        borderRadius: '12px',
                        fontStyle: 'italic',
                        lineHeight: 1.8,
                        whiteSpace: 'pre-wrap',
                        fontSize: '0.95rem',
                        color: colors.text,
                        border: '1px solid #d0d0d0',
                        marginBottom: '16px'
                      }}>
                        {haiku.haiku}
                      </Paper>
                    )}
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => handlePlayInRoon(album)}
                      sx={{
                        backgroundColor: '#23a7dd',
                        color: '#ffffff',
                        fontFamily: '"Roboto Condensed", sans-serif',
                        fontWeight: 700,
                        fontSize: '9px',
                        padding: '2px 6px',
                        height: '18px',
                        minWidth: '40px',
                        textTransform: 'uppercase',
                        marginLeft: 'auto',
                        display: 'block',
                        '&:hover': {
                          backgroundColor: '#1a8bc4'
                        }
                      }}
                    >
                      ▶ Roon
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
          </Grid>
        </Box>
      </Box>
    )
  }

  // Page 4: Timeline & Stats
  if (page.type === 'timeline_stats') {
    const { total_recent_listens, unique_artists, unique_albums, top_artists, top_albums } = page.content

    return (
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px'
      }}>
        <Box sx={{ maxWidth: '1000px', margin: '0 auto' }}>
        <Typography variant="h2" sx={{
          fontFamily: '"Playfair Display", "Georgia", serif',
          fontWeight: 900,
          marginBottom: '48px',
          color: '#1a1a1a',
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
          borderBottom: '4px solid #2c3e50',
          paddingBottom: '12px',
          textAlign: 'center'
        }}>
          {page.title}
        </Typography>

        <Grid container spacing={3} sx={{ marginBottom: '40px' }}>
          <Grid item xs={12} sm={4}>
            <Card elevation={6} sx={{
              background: `linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%)`,
              border: '3px solid #2c3e50',
              textAlign: 'center',
              padding: '32px',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: `0 12px 32px ${accentColor}60`
              }
            }}>
              <Typography variant="h3" sx={{ color: '#1a1a1a', fontWeight: 900, marginBottom: '8px' }}>
                {total_recent_listens}
              </Typography>
              <Typography variant="subtitle1" sx={{ color: colors.text, fontWeight: 600 }}>
                Écoutes récentes
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card elevation={6} sx={{
              background: `linear-gradient(135deg, ${colors.secondary}40 0%, ${colors.secondary}20 100%)`,
              border: `3px solid ${colors.secondary}`,
              textAlign: 'center',
              padding: '32px',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: `0 12px 32px ${colors.secondary}60`
              }
            }}>
              <Typography variant="h3" sx={{ color: colors.secondary, fontWeight: 900, marginBottom: '8px' }}>
                {unique_artists}
              </Typography>
              <Typography variant="subtitle1" sx={{ color: colors.text, fontWeight: 600 }}>
                Artistes uniques
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card elevation={6} sx={{
              background: `linear-gradient(135deg, #ff006e40 0%, #ff006e20 100%)`,
              border: '3px solid #ff006e',
              textAlign: 'center',
              padding: '32px',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: '0 12px 32px #ff006e60'
              }
            }}>
              <Typography variant="h3" sx={{ color: '#ff006e', fontWeight: 900, marginBottom: '8px' }}>
                {unique_albums}
              </Typography>
              <Typography variant="subtitle1" sx={{ color: colors.text, fontWeight: 600 }}>
                Albums uniques
              </Typography>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper elevation={4} sx={{ 
              padding: '24px', 
              backgroundColor: '#1a1a1a',
              border: '2px solid #2c2c2c',
              borderRadius: '16px'
            }}>
              <Typography variant="h5" sx={{ 
                fontFamily: '"Merriweather", "Georgia", serif',
                marginBottom: '24px', 
                color: '#ffffff', 
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                🎤 Top Artistes
              </Typography>
              {top_artists.map((item: any, idx: number) => (
                <Box key={idx} sx={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 16px',
                  marginBottom: '12px',
                  backgroundColor: '#2c2c2c',
                  borderRadius: '12px',
                  border: '1px solid #3a3a3a',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: '#3a3a3a',
                    transform: 'translateX(8px)'
                  }
                }}>
                  {item.image_url ? (
                    <Box
                      component="img"
                      src={item.image_url}
                      alt={item.artist_name}
                      sx={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        objectFit: 'cover',
                        marginRight: '16px',
                      border: '2px solid #2c3e50'
                      }}
                    />
                  ) : (
                    <Box sx={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      backgroundColor: accentColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '16px',
                      fontWeight: 900,
                      fontSize: '1.1rem',
                      color: colors.bg
                    }}>
                      {idx + 1}
                    </Box>
                  )}
                  <Typography sx={{ flex: 1, fontWeight: 600, color: '#ffffff' }}>
                    {item.artist_name || `Artiste #${item.artist_id}`}
                  </Typography>
                  <Chip
                    label={`${item.count} écoutes`}
                    size="small"
                    sx={{
                      backgroundColor: '#3a3a3a',
                      color: '#d0d0d0',
                      fontWeight: 700,
                      border: '1px solid #555'
                    }}
                  />
                </Box>
              ))}
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={4} sx={{ 
              padding: '24px', 
              backgroundColor: '#1a1a1a',
              border: '2px solid #2c2c2c',
              borderRadius: '16px'
            }}>
              <Typography variant="h5" sx={{ 
                fontFamily: '"Merriweather", "Georgia", serif',
                marginBottom: '24px', 
                color: '#ffffff', 
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                💿 Top Albums
              </Typography>
              {top_albums.map((item: any, idx: number) => (
                <Box key={idx} sx={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 16px',
                  marginBottom: '12px',
                  backgroundColor: '#2c2c2c',
                  borderRadius: '12px',
                  border: '1px solid #3a3a3a',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: '#3a3a3a',
                    transform: 'translateX(8px)'
                  }
                }}>
                  {item.image_url ? (
                    <Box
                      component="img"
                      src={item.image_url}
                      alt={item.album_title}
                      sx={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '4px',
                        objectFit: 'cover',
                        marginRight: '16px',
                      border: '2px solid #2c3e50'
                      }}
                    />
                  ) : (
                    <Box sx={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '4px',
                      backgroundColor: colors.secondary,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '16px',
                      fontWeight: 900,
                      fontSize: '1.1rem',
                      color: colors.bg
                    }}>
                      {idx + 1}
                    </Box>
                  )}
                  <Box sx={{ flex: 1 }}>
                    <Typography sx={{ fontWeight: 600, color: '#ffffff' }}>
                      {item.album_title || `Album #${item.album_id}`}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#999', fontSize: '0.85rem' }}>
                      {item.artist_name}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${item.count} écoutes`}
                    size="small"
                    sx={{
                      backgroundColor: '#3a3a3a',
                      color: '#d0d0d0',
                      fontWeight: 700,
                      border: '1px solid #555'
                    }}
                  />
                </Box>
              ))}
            </Paper>
          </Grid>
          </Grid>
        </Box>
      </Box>
    )
  }

  // Page 5: Playlist Theme
  if (page.type === 'playlist_theme') {
    const { playlist } = page.content

    return (
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px'
      }}>
        <Box sx={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Typography variant="h2" sx={{
            fontFamily: '"Playfair Display", "Georgia", serif',
            fontWeight: 900,
            marginBottom: '24px',
            color: '#1a1a1a',
            letterSpacing: '0.02em',
            textTransform: 'uppercase',
            borderBottom: '4px solid #2c3e50',
            paddingBottom: '12px',
            textAlign: 'center'
          }}>
            {page.title}
          </Typography>

          <Box sx={{
            '& p': { mb: 1.5, lineHeight: 1.8 },
            '& p:last-child': { mb: 0 },
            '& em': { fontStyle: 'italic', color: colors.text },
            '& strong': { fontWeight: 'bold', color: colors.text },
            '& h1, & h2, & h3': { mt: 2, mb: 1, fontWeight: 700 },
            '& h1:first-child, & h2:first-child, & h3:first-child': { mt: 0 },
            '& ul, & ol': { mb: 1.5, pl: 2 },
            '& li': { mb: 0.5 },
            '& blockquote': { borderLeft: '4px solid', borderColor: 'primary.main', pl: 2, fontStyle: 'italic', my: 1 },
            '& code': { backgroundColor: 'rgba(0, 0, 0, 0.05)', p: '2px 6px', borderRadius: '4px', fontFamily: 'monospace' },
            color: colors.text,
            fontWeight: 500,
            lineHeight: 2,
            marginBottom: '48px',
            fontSize: '1.15em',
            textAlign: 'left'
          }}>
            <ReactMarkdown>{playlist.description}</ReactMarkdown>
          </Box>

        <Grid container spacing={3}>
          {playlist.albums.map((album: any, idx: number) => (
            <Grid item xs={12} sm={6} md={12 / Math.min(textColumns, 3)} key={idx}>
              <Card elevation={4} sx={{
                background: `linear-gradient(135deg, ${colors.bg} 0%, #f5f5f5 100%)`,
                border: '2px solid #d0d0d0',
                borderRadius: '16px',
                overflow: 'hidden',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-12px) scale(1.02)',
                  borderColor: colors.secondary,
                  boxShadow: `0 16px 40px ${accentColor}60`
                }
              }}>
                {album.image_url && (
                  <CardMedia
                    component="img"
                    height={220}
                    image={album.image_url}
                    alt={album.title}
                    sx={{ 
                      backgroundColor: 'rgba(0,0,0,0.3)',
                      borderBottom: '2px solid #d0d0d0'
                    }}
                  />
                )}
                <CardContent sx={{ padding: '20px' }}>
                  <Typography variant="h6" sx={{ 
                    fontWeight: 700, 
                    marginBottom: '8px',
                    color: colors.text,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical'
                  }}>
                    {album.title}
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    marginBottom: '8px',
                    color: '#2c3e50',
                    fontWeight: 600
                  }}>
                    {album.artist}
                  </Typography>
                  {album.year && (
                    <Chip
                      label={album.year}
                      size="small"
                      sx={{
                        backgroundColor: '#e8e8e8',
                        color: colors.text,
                        fontWeight: 700,
                        border: '1px solid #2c3e50',
                        marginBottom: '12px'
                      }}
                    />
                  )}
                  <Button
                    size="small"
                    variant="contained"
                    onClick={() => handlePlayInRoon(album)}
                    sx={{
                      backgroundColor: '#23a7dd',
                      color: '#ffffff',
                      fontFamily: '"Roboto Condensed", sans-serif',
                      fontWeight: 700,
                      fontSize: '9px',
                      padding: '2px 6px',
                      height: '18px',
                      minWidth: '40px',
                      textTransform: 'uppercase',
                      marginLeft: 'auto',
                      display: 'block',
                      '&:hover': {
                        backgroundColor: '#1a8bc4'
                      }
                    }}
                  >
                    ▶ Roon
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        </Box>
      </Box>
    )
  }

  // Default empty page
  return (
    <>
      <Box sx={{
        width: '100%',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: '60px 20px',
        textAlign: 'center'
      }}>
        <Typography variant="h4" sx={{ color: accentColor, fontWeight: 700 }}>
          Page vide
        </Typography>
      </Box>

      {/* Dialog de sélection de zone Roon */}
      <Dialog open={zoneDialogOpen} onClose={() => setZoneDialogOpen(false)}>
        <DialogTitle>Sélectionner une zone Roon</DialogTitle>
        <DialogContent sx={{ minWidth: 300 }}>
          <Stack spacing={2} sx={{ pt: 2 }}>
            {roonZones && roonZones.length > 0 ? (
              roonZones.map((zone: any) => (
                <Button
                  key={zone.zone_id}
                  variant={selectedZone === zone.name ? 'contained' : 'outlined'}
                  fullWidth
                  onClick={() => setSelectedZone(zone.name)}
                  sx={{ justifyContent: 'flex-start' }}
                >
                  <Box sx={{ textAlign: 'left', width: '100%' }}>
                    <Typography variant="body2">{zone.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      État: {zone.state}
                    </Typography>
                  </Box>
                </Button>
              ))
            ) : (
              <Typography color="text.secondary">Aucune zone Roon disponible</Typography>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setZoneDialogOpen(false)}>Annuler</Button>
          <Button
            variant="contained"
            color="success"
            disabled={!selectedZone}
            onClick={confirmPlayInRoon}
          >
            Lancer la lecture
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
