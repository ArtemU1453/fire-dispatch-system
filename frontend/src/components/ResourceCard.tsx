import MyLocationIcon from '@mui/icons-material/MyLocation';
import {
  Box,
  Checkbox,
  Chip,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import { memo, useState } from 'react';

import type { ETAResponse, RecommendationItem } from '../types/api';
import { formatDistance, formatDuration } from '../utils/format';

export interface ResourceCardProps {
  unit: RecommendationItem;
  eta?: ETAResponse;
  selected: boolean;
  onToggle: (resourceId: string) => void;
  onFocus: (resourceId: string) => void;
}

/**
 * One recommended (or reserve) unit: identity, role, distance, ETA, capabilities
 * and the automatic rationale. Memoized — long lists re-render only changed rows.
 */
function ResourceCardBase({
  unit,
  eta,
  selected,
  onToggle,
  onFocus,
}: ResourceCardProps) {
  const [showReasons, setShowReasons] = useState(false);
  const isReserve = unit.role === 'reserve';

  return (
    <Box
      sx={{
        border: '1px solid',
        borderColor: selected ? 'primary.main' : 'divider',
        borderRadius: 1,
        p: 1,
        mb: 1,
        bgcolor: selected ? 'action.selected' : 'background.paper',
      }}
      data-testid="resource-card"
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        <Checkbox
          size="small"
          checked={selected}
          onChange={() => onToggle(unit.resource_id)}
          inputProps={{ 'aria-label': `Выбрать ${unit.name}` }}
        />
        <Box flexGrow={1} minWidth={0}>
          <Typography variant="subtitle2" noWrap title={unit.name}>
            {unit.name}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {unit.code}
            {unit.organization?.name ? ` · ${unit.organization.name}` : ''}
          </Typography>
        </Box>
        <Chip
          size="small"
          label={isReserve ? 'резерв' : 'основной'}
          color={isReserve ? 'warning' : 'primary'}
          variant={isReserve ? 'outlined' : 'filled'}
        />
        <Tooltip title="Показать на карте">
          <IconButton size="small" onClick={() => onFocus(unit.resource_id)}>
            <MyLocationIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mt: 0.5, pl: 4 }}>
        <Metric label="Расст." value={formatDistance(unit.distance_meters)} />
        <Metric
          label="ETA"
          value={eta ? formatDuration(eta.eta_seconds) : '—'}
        />
        <Metric label="Готовн." value={unit.readiness} />
      </Stack>

      {unit.capabilities.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5, pl: 4 }}>
          {unit.capabilities.map((cap) => (
            <Chip key={cap} size="small" variant="outlined" label={cap} />
          ))}
        </Stack>
      )}

      {unit.reasons.length > 0 && (
        <Box sx={{ pl: 4, mt: 0.5 }}>
          <Typography
            variant="caption"
            color="primary"
            sx={{ cursor: 'pointer' }}
            onClick={() => setShowReasons((v) => !v)}
          >
            {showReasons ? 'Скрыть обоснование' : 'Обоснование выбора'}
          </Typography>
          {showReasons && (
            <Box component="ul" sx={{ m: 0, pl: 2 }}>
              {unit.reasons.map((reason, index) => (
                <Typography
                  key={index}
                  component="li"
                  variant="caption"
                  color="text.secondary"
                >
                  {reason}
                </Typography>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

export const ResourceCard = memo(ResourceCardBase);
