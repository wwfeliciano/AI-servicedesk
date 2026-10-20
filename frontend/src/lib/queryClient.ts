import { QueryClient } from '@tanstack/react-query';

/** Estado do servidor (seção 8.1): cache do TanStack Query. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
