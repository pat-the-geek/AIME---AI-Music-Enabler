import { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  Menu as MenuIcon,
  LibraryMusic,
  History,
  Timeline,
  QueueMusic,
  Analytics,
  Settings,
  NewspaperOutlined,
  ArticleOutlined,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'

const menuItems = [
  { text: 'Magazine', path: '/magazine', icon: <NewspaperOutlined /> },
  { text: 'Articles', path: '/artist-article', icon: <ArticleOutlined /> },
  { text: 'Collection', path: '/collection', icon: <LibraryMusic /> },
  { text: 'Journal', path: '/journal', icon: <History /> },
  { text: 'Timeline', path: '/timeline', icon: <Timeline /> },
  { text: 'Discover', path: '/collections', icon: <QueueMusic /> },
  { text: 'Analytics', path: '/analytics', icon: <Analytics /> },
  { text: 'Settings', path: '/settings', icon: <Settings /> },
]

export default function Navbar() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const handleNavigation = (path: string) => {
    navigate(path)
    setDrawerOpen(false)
  }

  return (
    <>
      <AppBar position="fixed" sx={{ backgroundColor: '#000000' }}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AIME - AI Music Enabler
          </Typography>

          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {menuItems.map((item) => (
                <Button
                  key={item.path}
                  color="inherit"
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    borderBottom: location.pathname === item.path ? 2 : 0,
                    borderRadius: 0,
                  }}
                >
                  {item.text}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 250 }} role="presentation">
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => handleNavigation(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
    </>
  )
}
