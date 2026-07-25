import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useIncidentStore } from '../store/incident';
import { renderWithProviders } from '../test/testUtils';
import { AddressInput } from './AddressInput';
import * as endpoints from '../api/endpoints';

vi.mock('../api/endpoints');

describe('AddressInput', () => {
  beforeEach(() => {
    useIncidentStore.getState().reset();
    vi.mocked(endpoints.geocode).mockResolvedValue({
      query: 'Тверская',
      provider: 'nominatim',
      from_cache: false,
      success: true,
      count: 1,
      results: [
        {
          formatted_address: 'ул. Тверская, 1, Москва',
          latitude: 55.7573,
          longitude: 37.6136,
          accuracy: 'house',
          source: 'nominatim',
        },
      ],
    });
  });

  it('geocodes and sets coordinates on selection', async () => {
    renderWithProviders(<AddressInput />);
    await userEvent.type(screen.getByLabelText('Адрес'), 'Тверская');
    await userEvent.click(screen.getByTestId('geocode-button'));

    const result = await screen.findByText('ул. Тверская, 1, Москва');
    await userEvent.click(result);

    await waitFor(() => {
      const draft = useIncidentStore.getState().draft;
      expect(draft.latitude).toBeCloseTo(55.7573);
      expect(draft.longitude).toBeCloseTo(37.6136);
    });
    expect(endpoints.geocode).toHaveBeenCalledWith('Тверская', 5);
  });
});
