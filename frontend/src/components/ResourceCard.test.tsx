import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { eta, primaryUnit } from '../test/fixtures';
import { renderWithProviders } from '../test/testUtils';
import { ResourceCard } from './ResourceCard';

describe('ResourceCard', () => {
  it('shows the unit, distance, ETA and capabilities', () => {
    renderWithProviders(
      <ResourceCard
        unit={primaryUnit}
        eta={eta}
        selected={false}
        onToggle={() => {}}
        onFocus={() => {}}
      />,
    );
    expect(screen.getByText('Автоцистерна 1')).toBeInTheDocument();
    expect(screen.getByText('1.2 км')).toBeInTheDocument();
    expect(screen.getByText('5 мин')).toBeInTheDocument();
    expect(screen.getByText('fire_suppression')).toBeInTheDocument();
    expect(screen.getByText('основной')).toBeInTheDocument();
  });

  it('toggles selection', async () => {
    const onToggle = vi.fn();
    renderWithProviders(
      <ResourceCard
        unit={primaryUnit}
        selected={false}
        onToggle={onToggle}
        onFocus={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole('checkbox'));
    expect(onToggle).toHaveBeenCalledWith('res-1');
  });

  it('reveals the rationale on demand', async () => {
    renderWithProviders(
      <ResourceCard
        unit={primaryUnit}
        selected={false}
        onToggle={() => {}}
        onFocus={() => {}}
      />,
    );
    expect(screen.queryByText(/подразделение доступно/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByText('Обоснование выбора'));
    expect(screen.getByText(/подразделение доступно/)).toBeInTheDocument();
  });
});
