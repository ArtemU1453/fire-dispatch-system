import RecommendIcon from '@mui/icons-material/Recommend';
import {
  Autocomplete,
  Box,
  Button,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import { useIncidentTypes } from '../hooks/useIncidentTypes';
import { useRecommendMutation } from '../hooks/useRecommendation';
import { useIncidentStore } from '../store/incident';
import { useNotificationStore } from '../store/notifications';
import { useSessionStore } from '../store/session';
import type { DispatchRequest, IncidentComplexity } from '../types/api';
import { AddressInput } from './AddressInput';

const COMPLEXITIES: { value: IncidentComplexity; label: string }[] = [
  { value: 'simple', label: 'Простое' },
  { value: 'moderate', label: 'Среднее' },
  { value: 'complex', label: 'Сложное' },
  { value: 'critical', label: 'Критическое' },
];

const DANGER_LEVELS = ['low', 'elevated', 'high', 'critical'];

function newUuid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/** The dispatcher's call card — the left panel. Backend performs all logic. */
export function IncidentCard() {
  const draft = useIncidentStore((s) => s.draft);
  const searchRadius = useIncidentStore((s) => s.searchRadius);
  const setDraftField = useIncidentStore((s) => s.setDraftField);
  const setIncidentType = useIncidentStore((s) => s.setIncidentType);
  const notify = useNotificationStore((s) => s.notify);
  const can = useSessionStore((s) => s.can);
  const { data: incidentTypes = [] } = useIncidentTypes();
  const recommend = useRecommendMutation();

  const requestRecommendation = () => {
    if (!draft.incidentTypeId) {
      notify('error', 'Укажите тип происшествия.');
      return;
    }
    if (draft.latitude == null || draft.longitude == null) {
      notify('error', 'Укажите адрес или координаты происшествия.');
      return;
    }
    const request: DispatchRequest = {
      incident_id: newUuid(),
      incident_type_id: draft.incidentTypeId,
      complexity: (draft.complexity || null) as IncidentComplexity | null,
      latitude: draft.latitude,
      longitude: draft.longitude,
      address: draft.address || null,
      danger_level: draft.dangerLevel || null,
      object_type: draft.objectType || null,
      flags: [],
      constraints: { radius_meters: searchRadius },
    };
    recommend.mutate({ request });
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Карточка происшествия
      </Typography>
      <Stack spacing={1.5}>
        <TextField
          label="Номер вызова"
          value={draft.callNumber}
          onChange={(e) => setDraftField('callNumber', e.target.value)}
        />

        <Autocomplete
          freeSolo
          options={incidentTypes}
          getOptionLabel={(o) => (typeof o === 'string' ? o : o.name)}
          value={draft.incidentTypeLabel || null}
          onChange={(_, value) => {
            if (value && typeof value !== 'string') {
              setIncidentType(value.id, value.name);
            } else if (typeof value === 'string') {
              setIncidentType(value, value);
            } else {
              setIncidentType('', '');
            }
          }}
          onInputChange={(_, value, reason) => {
            if (reason === 'input') setIncidentType(value, value);
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Тип происшествия"
              placeholder="Пожар / UUID типа"
              helperText="Выберите из списка или введите идентификатор типа"
            />
          )}
        />

        <TextField
          select
          label="Категория (сложность)"
          value={draft.complexity}
          onChange={(e) => setDraftField('complexity', e.target.value)}
        >
          <MenuItem value="">—</MenuItem>
          {COMPLEXITIES.map((c) => (
            <MenuItem key={c.value} value={c.value}>
              {c.label}
            </MenuItem>
          ))}
        </TextField>

        <AddressInput />

        <TextField
          label="Координаты"
          value={
            draft.latitude != null && draft.longitude != null
              ? `${draft.latitude.toFixed(5)}, ${draft.longitude.toFixed(5)}`
              : ''
          }
          InputProps={{ readOnly: true }}
          placeholder="будут заполнены при геокодировании"
        />

        <Stack direction="row" spacing={1}>
          <TextField
            select
            label="Уровень опасности"
            value={draft.dangerLevel}
            onChange={(e) => setDraftField('dangerLevel', e.target.value)}
          >
            <MenuItem value="">—</MenuItem>
            {DANGER_LEVELS.map((d) => (
              <MenuItem key={d} value={d}>
                {d}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Тип объекта"
            value={draft.objectType}
            onChange={(e) => setDraftField('objectType', e.target.value)}
          />
        </Stack>

        <TextField
          label="Дополнительная информация"
          value={draft.extraInfo}
          onChange={(e) => setDraftField('extraInfo', e.target.value)}
          multiline
          minRows={2}
        />

        <Divider />

        <Button
          variant="contained"
          color="secondary"
          startIcon={<RecommendIcon />}
          onClick={requestRecommendation}
          disabled={recommend.isPending || !can('recommendation.request')}
          data-testid="recommend-button"
        >
          {recommend.isPending ? 'Формирование…' : 'Получить рекомендации'}
        </Button>
      </Stack>
    </Box>
  );
}
