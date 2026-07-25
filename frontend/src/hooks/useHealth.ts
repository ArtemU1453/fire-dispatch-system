import { useQuery } from '@tanstack/react-query';

import { getHealth, getRoutingHealth } from '../api/endpoints';

export interface EngineStatus {
  name: string;
  healthy: boolean | null;
  detail?: string;
}

/**
 * Aggregate engine statuses for the status bar.
 *
 * The backend exposes an overall `/health` and the routing provider's
 * `/routing/health`. GIS, Search, Rule and Dispatch are in-process backend
 * modules with no dedicated probe, so they mirror the backend process health.
 */
export function useHealth() {
  const backend = useQuery({
    queryKey: ['health', 'backend'],
    queryFn: getHealth,
    refetchInterval: 15_000,
  });
  const routing = useQuery({
    queryKey: ['health', 'routing'],
    queryFn: getRoutingHealth,
    refetchInterval: 15_000,
  });

  const backendUp = backend.isSuccess ? backend.data.status === 'ok' : null;
  const inProcess = (name: string): EngineStatus => ({
    name,
    healthy: backend.isError ? false : backendUp,
    detail: backend.isError ? 'нет связи' : undefined,
  });

  const statuses: EngineStatus[] = [
    {
      name: 'Backend',
      healthy: backend.isError ? false : backendUp,
      detail: backend.data?.version,
    },
    inProcess('GIS'),
    inProcess('Search Engine'),
    inProcess('Rule Engine'),
    inProcess('Dispatch Engine'),
    {
      name: 'Routing',
      healthy: routing.isError ? false : routing.data?.healthy ?? null,
      detail: routing.data?.provider,
    },
  ];

  return {
    statuses,
    isLoading: backend.isLoading || routing.isLoading,
    connected: !backend.isError,
  };
}
