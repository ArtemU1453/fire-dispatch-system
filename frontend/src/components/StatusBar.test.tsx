import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as endpoints from '../api/endpoints';
import { renderWithProviders } from '../test/testUtils';
import { StatusBar } from './StatusBar';

vi.mock('../api/endpoints');

describe('StatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(endpoints.getHealth).mockResolvedValue({
      status: 'ok',
      app: 'AI Dispatcher',
      version: '0.1.0',
      environment: 'test',
      database: 'ok',
    });
    vi.mocked(endpoints.getRoutingHealth).mockResolvedValue({
      provider: 'haversine',
      healthy: true,
    });
  });

  it('renders every engine status', async () => {
    renderWithProviders(<StatusBar />);
    for (const name of [
      'Backend',
      'GIS',
      'Search Engine',
      'Rule Engine',
      'Dispatch Engine',
      'Routing',
    ]) {
      expect(screen.getByTestId(`status-${name}`)).toBeInTheDocument();
    }
    await waitFor(() => expect(endpoints.getHealth).toHaveBeenCalled());
  });
});
