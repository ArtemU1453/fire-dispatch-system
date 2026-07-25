import { createTheme } from '@mui/material/styles';

/**
 * A dark, control-room theme tuned for a 1920×1080 dispatcher workstation:
 * dense layout, high contrast, calm accent colors.
 */
export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#4f9dff' },
    secondary: { main: '#ffb74d' },
    success: { main: '#4caf50' },
    warning: { main: '#ff9800' },
    error: { main: '#ef5350' },
    background: { default: '#0e1621', paper: '#16212e' },
    divider: 'rgba(255,255,255,0.08)',
  },
  shape: { borderRadius: 8 },
  typography: {
    fontSize: 13,
    fontFamily: 'Roboto, "Segoe UI", system-ui, sans-serif',
    h6: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
  },
  components: {
    MuiCard: { defaultProps: { variant: 'outlined' } },
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiTextField: { defaultProps: { size: 'small', fullWidth: true } },
  },
});
