import { Box, Typography } from '@mui/material';

import type { ETAResponse, RecommendationItem } from '../types/api';
import { ResourceCard } from './ResourceCard';

export interface ResourceListProps {
  title: string;
  units: RecommendationItem[];
  etas: Map<string, ETAResponse>;
  selectedIds: string[];
  onToggle: (resourceId: string) => void;
  onFocus: (resourceId: string) => void;
  emptyText?: string;
}

/**
 * A titled list of recommended units. Recommendation lists are short; the long
 * (searchable) resource list is virtualized separately in the SearchPanel.
 */
export function ResourceList({
  title,
  units,
  etas,
  selectedIds,
  onToggle,
  onFocus,
  emptyText = 'Нет подразделений',
}: ResourceListProps) {
  return (
    <Box sx={{ mb: 1 }}>
      <Typography variant="overline" color="text.secondary">
        {title} ({units.length})
      </Typography>
      {units.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {emptyText}
        </Typography>
      ) : (
        units.map((unit) => (
          <ResourceCard
            key={unit.id}
            unit={unit}
            eta={etas.get(unit.resource_id)}
            selected={selectedIds.includes(unit.resource_id)}
            onToggle={onToggle}
            onFocus={onFocus}
          />
        ))
      )}
    </Box>
  );
}
