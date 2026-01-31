import React, { ReactNode } from 'react'
import { Box, Container, Typography, Button } from '@mui/material'
import ErrorIcon from '@mui/icons-material/Error'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="sm">
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '100vh',
              gap: 2,
            }}
          >
            <ErrorIcon sx={{ fontSize: 80, color: 'error.main' }} />
            <Typography variant="h4" component="h1">
              Oups! Quelque chose s'est mal passé
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ textAlign: 'center' }}>
              {this.state.error?.message || 'Une erreur interne s\'est produite'}
            </Typography>

            {/* Dev mode: show stack trace */}
            {this.state.errorInfo && (
              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 1,
                  maxHeight: 200,
                  overflow: 'auto',
                  width: '100%',
                }}
              >
                <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {this.state.errorInfo.componentStack}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
              <Button variant="contained" onClick={this.handleReset}>
                Réessayer
              </Button>
              <Button variant="outlined" onClick={() => window.location.href = '/'}>
                Retour à l'accueil
              </Button>
            </Box>
          </Box>
        </Container>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
