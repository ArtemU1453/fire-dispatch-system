import CloseIcon from '@mui/icons-material/Close';
import {
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect } from 'react';

import { useNotificationStore } from '../store/notifications';

export interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
}

const COLOR: Record<string, string> = {
  error: 'error.main',
  warning: 'warning.main',
  info: 'info.main',
  success: 'success.main',
};

/** Slide-over list of recent notifications (errors, warnings, info, success). */
export function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const items = useNotificationStore((s) => s.items);
  const dismiss = useNotificationStore((s) => s.dismiss);
  const clear = useNotificationStore((s) => s.clear);
  const markAllRead = useNotificationStore((s) => s.markAllRead);

  useEffect(() => {
    if (open) markAllRead();
  }, [open, markAllRead]);

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 340, p: 1 }}>
        <Stack direction="row" alignItems="center">
          <Typography variant="h6" flexGrow={1}>
            Уведомления
          </Typography>
          <Typography
            variant="caption"
            color="primary"
            sx={{ cursor: 'pointer', mr: 1 }}
            onClick={clear}
          >
            Очистить
          </Typography>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
        <Divider sx={{ my: 1 }} />
        {items.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ p: 1 }}>
            Нет уведомлений
          </Typography>
        ) : (
          <List dense>
            {items.map((n) => (
              <ListItem
                key={n.id}
                secondaryAction={
                  <IconButton edge="end" size="small" onClick={() => dismiss(n.id)}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                }
                sx={{ borderLeft: '3px solid', borderColor: COLOR[n.severity] }}
              >
                <ListItemText
                  primary={n.message}
                  secondary={new Date(n.at).toLocaleTimeString('ru-RU')}
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Drawer>
  );
}
