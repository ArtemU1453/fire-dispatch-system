import { Box, Paper } from '@mui/material';
import type { ReactNode } from 'react';

export interface DispatcherLayoutProps {
  top: ReactNode;
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
  bottom: ReactNode;
}

/**
 * The dispatcher workstation grid, tuned for 1920×1080:
 * top toolbar, a middle row (left call card · central map · right recommendations)
 * and a bottom status bar.
 */
export function DispatcherLayout({
  top,
  left,
  center,
  right,
  bottom,
}: DispatcherLayoutProps) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateRows: 'auto 1fr 36px',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ gridRow: 1 }}>{top}</Box>

      <Box
        sx={{
          gridRow: 2,
          display: 'grid',
          gridTemplateColumns: '380px 1fr 420px',
          minHeight: 0,
        }}
      >
        <Paper
          square
          sx={{ overflow: 'auto', p: 1.5, borderRight: '1px solid', borderColor: 'divider' }}
        >
          {left}
        </Paper>
        <Box sx={{ position: 'relative', minWidth: 0 }}>{center}</Box>
        <Paper
          square
          sx={{ overflow: 'auto', p: 1.5, borderLeft: '1px solid', borderColor: 'divider' }}
        >
          {right}
        </Paper>
      </Box>

      <Paper square sx={{ gridRow: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        {bottom}
      </Paper>
    </Box>
  );
}
