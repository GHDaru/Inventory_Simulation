import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation, NavLink } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  useMediaQuery,
  useTheme,
  CircularProgress,
  Chip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import TuneIcon from '@mui/icons-material/Tune';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InventoryIcon from '@mui/icons-material/Inventory';
import { listRuns } from '../api/api';

const DRAWER_WIDTH = 260;
const POLL_INTERVAL_MS = 4000;

function RunStatusChip({ status }) {
  const colorMap = { done: 'success', running: 'warning', failed: 'error', created: 'default' };
  return (
    <Chip
      label={status}
      size="small"
      color={colorMap[status] || 'default'}
      sx={{ height: 18, fontSize: '0.65rem', ml: 0.5 }}
    />
  );
}

export default function AppShellLayout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [runsOpen, setRunsOpen] = useState(true);
  const [runs, setRuns] = useState([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const fetchRuns = useCallback(async () => {
    setLoadingRuns(true);
    try {
      const data = await listRuns();
      setRuns(data);
    } catch {
      // silently ignore; runs list is non-critical
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  // Fetch runs on mount
  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  // Poll for run status updates every 4 seconds
  useEffect(() => {
    const hasActive = runs.some(r => r.status === 'running' || r.status === 'created');
    if (!hasActive) return;
    const id = setInterval(fetchRuns, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [runs, fetchRuns]);

  // Refresh runs list whenever the location changes (e.g. after creating a run)
  useEffect(() => {
    fetchRuns();
  }, [location.pathname, fetchRuns]);

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Brand */}
      <Toolbar sx={{ gap: 1 }}>
        <InventoryIcon color="primary" />
        <Typography variant="subtitle1" fontWeight={700} color="primary" noWrap>
          Inventory Sim
        </Typography>
      </Toolbar>
      <Divider />

      <List dense>
        {/* Upload */}
        <ListItem disablePadding>
          <ListItemButton
            component={NavLink}
            to="/upload"
            selected={location.pathname === '/upload'}
            onClick={() => isMobile && setMobileOpen(false)}
          >
            <ListItemIcon><UploadFileIcon /></ListItemIcon>
            <ListItemText primary="Upload" />
          </ListItemButton>
        </ListItem>

        {/* Config */}
        <ListItem disablePadding>
          <ListItemButton
            component={NavLink}
            to="/config"
            selected={location.pathname === '/config'}
            onClick={() => isMobile && setMobileOpen(false)}
          >
            <ListItemIcon><TuneIcon /></ListItemIcon>
            <ListItemText primary="Configuração de Simulação" />
          </ListItemButton>
        </ListItem>

        {/* Results section header */}
        <ListItem disablePadding>
          <ListItemButton onClick={() => setRunsOpen(o => !o)}>
            <ListItemIcon>
              <AssessmentIcon />
            </ListItemIcon>
            <ListItemText primary="Avaliação de Resultados" />
            {loadingRuns
              ? <CircularProgress size={14} sx={{ mr: 1 }} />
              : runsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </ListItemButton>
        </ListItem>

        {/* Run list (nested) */}
        <Collapse in={runsOpen} timeout="auto" unmountOnExit>
          <List dense disablePadding>
            {runs.length === 0 && !loadingRuns && (
              <ListItem sx={{ pl: 4 }}>
                <ListItemText
                  secondary="Nenhuma rodada ainda"
                  secondaryTypographyProps={{ fontSize: '0.78rem' }}
                />
              </ListItem>
            )}
            {runs.map(run => (
              <ListItem key={run.id} disablePadding>
                <ListItemButton
                  sx={{ pl: 4 }}
                  selected={location.pathname === `/results/${run.id}`}
                  onClick={() => {
                    navigate(`/results/${run.id}`);
                    if (isMobile) setMobileOpen(false);
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 130 }}>
                          {run.name}
                        </Typography>
                        <RunStatusChip status={run.status} />
                      </Box>
                    }
                    secondary={new Date(run.created_at).toLocaleString()}
                    secondaryTypographyProps={{ fontSize: '0.7rem', noWrap: true }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Collapse>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Top app bar (mobile only) */}
      <AppBar
        position="fixed"
        sx={{ display: { md: 'none' }, zIndex: theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(o => !o)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <InventoryIcon sx={{ mr: 1 }} />
          <Typography variant="h6" noWrap>Inventory Sim</Typography>
        </Toolbar>
      </AppBar>

      {/* Permanent drawer (desktop) */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
        }}
        open
      >
        {drawerContent}
      </Drawer>

      {/* Temporary drawer (mobile) */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: { xs: 8, md: 0 },
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
