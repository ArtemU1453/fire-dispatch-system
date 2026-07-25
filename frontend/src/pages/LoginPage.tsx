import {
  Box,
  Button,
  Card,
  CardContent,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { authenticate } from '../services/auth';
import { useSessionStore, type Role } from '../store/session';

const ROLES: { value: Role; label: string }[] = [
  { value: 'dispatcher', label: 'Диспетчер' },
  { value: 'supervisor', label: 'Старший смены' },
  { value: 'viewer', label: 'Наблюдатель' },
];

/**
 * Authorization screen. Auth is client-side at this stage (no backend auth API);
 * the role selection prepares the UI for future RBAC.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const login = useSessionStore((s) => s.login);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [shift, setShift] = useState('Дежурная смена №1');
  const [role, setRole] = useState<Role>('dispatcher');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      const user = await authenticate({ username, password, shift, role });
      login(user);
      navigate('/', { replace: true });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Card sx={{ width: 380 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            АСУ «Выезд»
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Вход в рабочее место диспетчера
          </Typography>
          <Stack
            spacing={2}
            sx={{ mt: 2 }}
            component="form"
            onSubmit={(e) => {
              e.preventDefault();
              void submit();
            }}
          >
            <TextField
              label="Пользователь"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
            <TextField
              label="Пароль"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <TextField
              label="Смена"
              value={shift}
              onChange={(e) => setShift(e.target.value)}
            />
            <TextField
              select
              label="Роль"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              {ROLES.map((r) => (
                <MenuItem key={r.value} value={r.value}>
                  {r.label}
                </MenuItem>
              ))}
            </TextField>
            {error && (
              <Typography variant="body2" color="error">
                {error}
              </Typography>
            )}
            <Button
              type="submit"
              variant="contained"
              disabled={busy}
              data-testid="login-submit"
            >
              Войти
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
