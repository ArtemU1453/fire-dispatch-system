import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import { useMemo } from 'react';

import { useRecommendationQuery } from '../hooks/useRecommendation';
import { useUnitDetails, useUnitEtas } from '../hooks/useUnitRouting';
import { useIncidentStore } from '../store/incident';
import { useNotificationStore } from '../store/notifications';
import { useSessionStore } from '../store/session';
import {
  confidenceLabel,
  priorityLabel,
  statusLabel,
} from '../utils/format';
import { ResourceList } from './ResourceList';

/** System recommendations — the right panel. Purely presents backend output. */
export function RecommendationPanel() {
  const incidentId = useIncidentStore((s) => s.incidentId);
  const draft = useIncidentStore((s) => s.draft);
  const selectedIds = useIncidentStore((s) => s.selectedUnitIds);
  const confirmed = useIncidentStore((s) => s.confirmed);
  const toggleUnit = useIncidentStore((s) => s.toggleUnit);
  const confirmComposition = useIncidentStore((s) => s.confirmComposition);
  const focusMap = useIncidentStore((s) => s.focusMap);
  const notify = useNotificationStore((s) => s.notify);
  const can = useSessionStore((s) => s.can);

  const { data, isLoading, isError } = useRecommendationQuery(incidentId);

  const allUnits = useMemo(
    () => [...(data?.primary_units ?? []), ...(data?.reserve_units ?? [])],
    [data],
  );
  const { byId: unitDetails } = useUnitDetails(
    allUnits.map((u) => u.resource_id),
  );
  const origin =
    draft.latitude != null && draft.longitude != null
      ? { lat: draft.latitude, lon: draft.longitude }
      : null;
  const etas = useUnitEtas(origin, Array.from(unitDetails.values()));

  const focusUnit = (resourceId: string) => {
    const detail = unitDetails.get(resourceId);
    if (detail?.latitude != null && detail?.longitude != null) {
      focusMap(detail.latitude, detail.longitude);
    }
  };

  if (!incidentId) {
    return (
      <Placeholder text="Сформируйте рекомендацию из карточки происшествия." />
    );
  }
  if (isLoading) return <LinearProgress />;
  if (isError || !data) {
    return <Placeholder text="Не удалось загрузить рекомендацию." />;
  }

  const confirm = () => {
    confirmComposition();
    notify('success', `Состав подтверждён: ${selectedIds.length} подразделений.`);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Рекомендации системы
      </Typography>

      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 1 }}>
        <Chip
          size="small"
          color={data.status === 'recommended' ? 'success' : 'warning'}
          label={statusLabel(data.status)}
        />
        <Chip size="small" label={`Приоритет: ${priorityLabel(data.priority)}`} />
        <Chip
          size="small"
          variant="outlined"
          label={`Уверенность: ${confidenceLabel(data.confidence)}`}
        />
        <Chip
          size="small"
          variant="outlined"
          label={`Кандидатов: ${data.total_candidates}`}
        />
      </Stack>

      {data.required_capabilities.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="overline" color="text.secondary">
            Требуемые возможности
          </Typography>
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
            {data.required_capabilities.map((cap) => (
              <Chip
                key={cap.code}
                size="small"
                color={cap.mandatory ? 'primary' : 'default'}
                variant="outlined"
                label={`${cap.label ?? cap.code}×${cap.min_quantity}`}
              />
            ))}
          </Stack>
        </Box>
      )}

      {data.messages.length > 0 && (
        <Alert
          severity={data.sufficient ? 'success' : 'warning'}
          sx={{ mb: 1, py: 0 }}
        >
          {data.messages.join(' ')}
        </Alert>
      )}

      <Divider sx={{ my: 1 }} />

      <ResourceList
        title="Рекомендуемые подразделения"
        units={data.primary_units}
        etas={etas}
        selectedIds={selectedIds}
        onToggle={toggleUnit}
        onFocus={focusUnit}
        emptyText="Подразделения не подобраны"
      />
      <ResourceList
        title="Резерв"
        units={data.reserve_units}
        etas={etas}
        selectedIds={selectedIds}
        onToggle={toggleUnit}
        onFocus={focusUnit}
        emptyText="Резерв не назначен"
      />

      <Divider sx={{ my: 1 }} />

      {confirmed ? (
        <Alert icon={<CheckCircleIcon />} severity="success">
          Состав подтверждён диспетчером ({selectedIds.length}). Отправка
          подразделений выполняется вне системы.
        </Alert>
      ) : (
        <Button
          fullWidth
          variant="contained"
          color="success"
          startIcon={<CheckCircleIcon />}
          disabled={selectedIds.length === 0 || !can('recommendation.confirm')}
          onClick={confirm}
          data-testid="confirm-button"
        >
          Подтвердить состав ({selectedIds.length})
        </Button>
      )}
    </Box>
  );
}

function Placeholder({ text }: { text: string }) {
  return (
    <Box sx={{ p: 2, textAlign: 'center' }}>
      <Typography variant="h6" gutterBottom>
        Рекомендации системы
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {text}
      </Typography>
    </Box>
  );
}
