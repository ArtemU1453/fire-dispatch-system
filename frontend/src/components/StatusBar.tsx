import { Box, Chip, Stack, Tooltip, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { useHealth } from '../hooks/useHealth';
import { formatTime } from '../utils/format';

/** Bottom status bar — health of each backend engine and the current time. */
export function StatusBar() {
  const { statuses } = useHealth();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const color = (healthy: boolean | null) =>
    healthy == null ? 'default' : healthy ? 'success' : 'error';

  return (
    <Stack
      direction="row"
      spacing={1}
      alignItems="center"
      sx={{ px: 1, height: '100%', overflowX: 'auto' }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
        Состояние сервисов:
      </Typography>
      {statuses.map((s) => (
        <Tooltip key={s.name} title={s.detail ?? ''}>
          <Chip
            size="small"
            variant="outlined"
            color={color(s.healthy)}
            label={s.name}
            data-testid={`status-${s.name}`}
            icon={
              <Box
                component="span"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  ml: 1,
                  bgcolor:
                    s.healthy == null
                      ? 'grey.500'
                      : s.healthy
                        ? 'success.main'
                        : 'error.main',
                }}
              />
            }
          />
        </Tooltip>
      ))}
      <Box flexGrow={1} />
      <Typography variant="caption" data-testid="statusbar-clock">
        {formatTime(now)}
      </Typography>
    </Stack>
  );
}
