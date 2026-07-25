import LogoutIcon from '@mui/icons-material/Logout';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SearchIcon from '@mui/icons-material/Search';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import {
  AppBar,
  Badge,
  Box,
  Chip,
  IconButton,
  InputAdornment,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';

import { useHealth } from '../hooks/useHealth';
import { useNotificationStore } from '../store/notifications';
import { useSessionStore } from '../store/session';
import { formatTime } from '../utils/format';

export interface TopToolbarProps {
  onSearch: (query: string) => void;
  onOpenNotifications: () => void;
}

/** Top panel — clock, user, shift, connection, notifications and global search. */
export function TopToolbar({ onSearch, onOpenNotifications }: TopToolbarProps) {
  const user = useSessionStore((s) => s.user);
  const logout = useSessionStore((s) => s.logout);
  const unread = useNotificationStore(
    (s) => s.items.filter((n) => !n.read).length,
  );
  const { connected } = useHealth();
  const [now, setNow] = useState(new Date());
  const [query, setQuery] = useState('');

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar variant="dense" sx={{ gap: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          АСУ «Выезд»
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Рабочее место диспетчера
        </Typography>

        <TextField
          size="small"
          placeholder="Поиск подразделений…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSearch(query);
          }}
          sx={{ maxWidth: 320 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />

        <Box flexGrow={1} />

        <Tooltip title={connected ? 'Связь с сервером' : 'Нет связи'}>
          <Chip
            size="small"
            color={connected ? 'success' : 'error'}
            variant="outlined"
            icon={connected ? <WifiIcon /> : <WifiOffIcon />}
            label={connected ? 'online' : 'offline'}
          />
        </Tooltip>

        <Typography variant="body2" data-testid="toolbar-clock">
          {formatTime(now)}
        </Typography>

        {user && (
          <Chip
            size="small"
            label={`${user.username} · ${user.shift}`}
            variant="outlined"
          />
        )}

        <Tooltip title="Уведомления">
          <IconButton onClick={onOpenNotifications} size="small">
            <Badge badgeContent={unread} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        <Tooltip title="Выйти">
          <IconButton onClick={logout} size="small">
            <LogoutIcon />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
