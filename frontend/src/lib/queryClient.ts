import { QueryClient } from '@tanstack/react-query';

/** Shared React Query client — server state lives here, not in component state. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});
