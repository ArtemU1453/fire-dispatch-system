import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as endpoints from '../api/endpoints';
import { ApiError } from '../api/client';
import { IncidentCard } from '../components/IncidentCard';
import { RecommendationPanel } from '../components/RecommendationPanel';
import { useIncidentStore } from '../store/incident';
import { useNotificationStore } from '../store/notifications';
import { useSessionStore } from '../store/session';
import { eta, recommendation, resourceItem } from './fixtures';
import { renderWithProviders } from './testUtils';

vi.mock('../api/endpoints');

function primeStores() {
  useIncidentStore.getState().reset();
  useNotificationStore.getState().clear();
  useSessionStore.getState().login({
    username: 'operator',
    role: 'dispatcher',
    shift: 'смена №1',
  });
  useIncidentStore.getState().setIncidentType('type-1', 'Пожар');
  useIncidentStore.getState().setCoordinates(55.75, 37.62, 'ул. Тверская, 1');
}

describe('dispatcher recommendation flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    primeStores();
    vi.mocked(endpoints.listRules).mockResolvedValue([]);
    vi.mocked(endpoints.getResource).mockResolvedValue(resourceItem);
    vi.mocked(endpoints.estimateEta).mockResolvedValue(eta);
    vi.mocked(endpoints.getRecommendation).mockResolvedValue(recommendation);
  });

  it('requests a recommendation and renders the units', async () => {
    vi.mocked(endpoints.recommend).mockResolvedValue(recommendation);
    renderWithProviders(
      <>
        <IncidentCard />
        <RecommendationPanel />
      </>,
    );

    await userEvent.click(screen.getByTestId('recommend-button'));

    expect(await screen.findByText('Автоцистерна 1')).toBeInTheDocument();
    expect(screen.getByText(/Состав сформирован/)).toBeInTheDocument();
    // The primary unit is pre-selected → confirm button reflects one unit.
    await waitFor(() =>
      expect(useIncidentStore.getState().selectedUnitIds).toContain('res-1'),
    );
    expect(endpoints.recommend).toHaveBeenCalledTimes(1);
  });

  it('shows a notification when the backend fails', async () => {
    vi.mocked(endpoints.recommend).mockRejectedValue(
      new ApiError('Сервис временно недоступен.', 'unavailable', 503),
    );
    renderWithProviders(<IncidentCard />);

    await userEvent.click(screen.getByTestId('recommend-button'));

    await waitFor(() => {
      const errors = useNotificationStore
        .getState()
        .items.filter((n) => n.severity === 'error');
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it('blocks recommendation when coordinates are missing', async () => {
    useIncidentStore.getState().setDraftField('latitude', null);
    useIncidentStore.getState().setDraftField('longitude', null);
    renderWithProviders(<IncidentCard />);

    await userEvent.click(screen.getByTestId('recommend-button'));

    await waitFor(() => {
      const errors = useNotificationStore.getState().items;
      expect(errors.some((n) => n.message.includes('координаты'))).toBe(true);
    });
    expect(endpoints.recommend).not.toHaveBeenCalled();
  });
});
