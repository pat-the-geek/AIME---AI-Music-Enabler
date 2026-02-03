import React from 'react'
import { Typography, TypographyProps, Box, BoxProps } from '@mui/material'
import { isEmptyContent, hiddenContentSx } from '@/utils/hideEmptyContent'

/**
 * Composant Typography qui masque automatiquement les contenus "vides"
 */
export const TypographyWithHiddenEmpty: React.FC<
  TypographyProps & { children: React.ReactNode }
> = ({ children, sx, ...props }) => {
  const childText = typeof children === 'string' ? children : undefined
  const shouldHide = isEmptyContent(childText)
  
  return (
    <Typography
      {...props}
      sx={{
        ...sx,
        ...(shouldHide ? hiddenContentSx : {})
      }}
    >
      {children}
    </Typography>
  )
}

/**
 * Composant Box qui masque automatiquement les contenus "vides" si enfant textuel
 */
export const BoxWithHiddenEmpty: React.FC<
  BoxProps & { children?: React.ReactNode }
> = ({ children, sx, ...props }) => {
  const childText = typeof children === 'string' ? children : undefined
  const shouldHide = isEmptyContent(childText)
  
  return (
    <Box
      {...props}
      sx={{
        ...sx,
        ...(shouldHide ? hiddenContentSx : {})
      }}
    >
      {children}
    </Box>
  )
}
