import SearchIcon from '@mui/icons-material/Search';
import {
  Box,
  Button,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  TextField,
} from '@mui/material';
import { useState } from 'react';

import { useGeocode } from '../hooks/useGeocode';
import { useIncidentStore } from '../store/incident';

/**
 * Address entry with geocoding. The dispatcher types an address and searches;
 * picking a candidate sets the incident coordinates (used by the map and the
 * recommendation request). Geocoding runs on the server (GIS module).
 */
export function AddressInput() {
  const address = useIncidentStore((s) => s.draft.address);
  const setDraftField = useIncidentStore((s) => s.setDraftField);
  const setCoordinates = useIncidentStore((s) => s.setCoordinates);
  const geocode = useGeocode();
  const [query, setQuery] = useState(address);

  const submit = () => {
    const trimmed = query.trim();
    if (trimmed) geocode.mutate(trimmed);
  };

  const results = geocode.data?.results ?? [];

  return (
    <Box>
      <Stack direction="row" spacing={1}>
        <TextField
          label="Адрес"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setDraftField('address', e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit();
          }}
          placeholder="ул. Тверская, 1"
        />
        <Button
          variant="contained"
          onClick={submit}
          disabled={geocode.isPending}
          startIcon={<SearchIcon />}
          data-testid="geocode-button"
        >
          Найти
        </Button>
      </Stack>

      {results.length > 0 && (
        <List dense sx={{ maxHeight: 160, overflow: 'auto', mt: 0.5 }}>
          {results.map((result, index) => (
            <ListItemButton
              key={`${result.latitude}-${result.longitude}-${index}`}
              onClick={() => {
                setCoordinates(
                  result.latitude,
                  result.longitude,
                  result.formatted_address,
                );
                setQuery(result.formatted_address);
              }}
            >
              <ListItemText
                primary={result.formatted_address}
                secondary={`${result.latitude.toFixed(5)}, ${result.longitude.toFixed(
                  5,
                )} · ${result.source}`}
              />
            </ListItemButton>
          ))}
        </List>
      )}
    </Box>
  );
}
