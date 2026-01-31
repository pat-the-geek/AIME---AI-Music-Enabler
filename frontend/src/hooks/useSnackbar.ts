import { useState, useCallback } from 'react'

export type SnackbarSeverity = 'success' | 'error' | 'warning' | 'info'

export interface SnackbarState {
  open: boolean
  message: string
  severity: SnackbarSeverity
  autoHideDuration?: number
}

export function useSnackbar() {
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'info',
    autoHideDuration: 5000,
  })

  const showSuccess = useCallback(
    (message: string, duration?: number) => {
      setSnackbar({
        open: true,
        message,
        severity: 'success',
        autoHideDuration: duration ?? 4000,
      })
    },
    []
  )

  const showError = useCallback(
    (message: string, duration?: number) => {
      setSnackbar({
        open: true,
        message,
        severity: 'error',
        autoHideDuration: duration ?? 6000,
      })
    },
    []
  )

  const showWarning = useCallback(
    (message: string, duration?: number) => {
      setSnackbar({
        open: true,
        message,
        severity: 'warning',
        autoHideDuration: duration ?? 5000,
      })
    },
    []
  )

  const showInfo = useCallback(
    (message: string, duration?: number) => {
      setSnackbar({
        open: true,
        message,
        severity: 'info',
        autoHideDuration: duration ?? 4000,
      })
    },
    []
  )

  const close = useCallback(() => {
    setSnackbar((prev) => ({
      ...prev,
      open: false,
    }))
  }, [])

  return {
    snackbar,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    close,
  }
}
