import MyLocationIcon from '@mui/icons-material/MyLocation';
import SearchIcon from '@mui/icons-material/Search';
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { FixedSizeList, type ListChildComponentProps } from 'react-window';

import { searchResources, type ResourceSearchParams } from '../api/endpoints';
import { useIncidentStore } from '../store/incident';
import type { ResourceSearchItem } from '../types/api';
import { formatDistance } from '../utils/format';

export interface SearchPanelProps {
  open: boolean;
  onClose: () => void;
  initialQuery?: string;
}

/**
 * Resource search around the incident (or by text). Results are **virtualized**
 * (react-window) so long lists stay fast. Selecting a result focuses it on the
 * map. Backend performs the search; this only renders it.
 */
export function SearchPanel({ open, onClose, initialQuery = '' }: SearchPanelProps) {
  const draft = useIncidentStore((s) => s.draft);
  const searchRadius = useIncidentStore((s) => s.searchRadius);
  const focusMap = useIncidentStore((s) => s.focusMap);
  const [query, setQuery] = useState(initialQuery);
  const [params, setParams] = useState<ResourceSearchParams | null>(null);

  useEffect(() => {
    if (open) setQuery(initialQuery);
  }, [open, initialQuery]);

  const { data, isFetching } = useQuery({
    queryKey: ['resource-search', params],
    queryFn: () => searchResources(params as ResourceSearchParams),
    enabled: Boolean(params),
  });

  const submit = () => {
    setParams({
      q: query.trim() || undefined,
      lat: draft.latitude ?? undefined,
      lon: draft.longitude ?? undefined,
      radius_m: draft.latitude != null ? searchRadius : undefined,
      deployable: true,
      limit: 200,
    });
  };

  const items = data?.items ?? [];

  const Row = ({ index, style }: ListChildComponentProps) => {
    const item: ResourceSearchItem = items[index];
    return (
      <Box
        style={style}
        sx={{
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid',
          borderColor: 'divider',
          px: 1,
        }}
      >
        <Box flexGrow={1} minWidth={0}>
          <Typography variant="body2" noWrap>
            {item.name}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {item.code} · {item.availability_status?.name ?? '—'} ·{' '}
            {formatDistance(item.distance_meters)}
          </Typography>
        </Box>
        <IconButton
          size="small"
          disabled={item.latitude == null || item.longitude == null}
          onClick={() =>
            item.latitude != null &&
            item.longitude != null &&
            focusMap(item.latitude, item.longitude)
          }
        >
          <MyLocationIcon fontSize="small" />
        </IconButton>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Поиск подразделений</DialogTitle>
      <DialogContent>
        <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
          <TextField
            autoFocus
            placeholder="Название / код"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submit();
            }}
          />
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={submit}
            data-testid="search-submit"
          >
            Искать
          </Button>
        </Stack>
        {isFetching && <LinearProgress />}
        <Typography variant="caption" color="text.secondary">
          {data ? `Найдено: ${data.total}` : 'Введите запрос и нажмите «Искать».'}
        </Typography>
        {items.length > 0 && (
          <FixedSizeList
            height={360}
            itemCount={items.length}
            itemSize={56}
            width="100%"
          >
            {Row}
          </FixedSizeList>
        )}
      </DialogContent>
    </Dialog>
  );
}
