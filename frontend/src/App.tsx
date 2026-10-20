import { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'sonner';

import { restaurarSessao } from '@/api/auth';
import { router } from '@/app/router';
import { queryClient } from '@/lib/queryClient';
import { useAplicarTema } from '@/lib/useTema';

export function App() {
  useAplicarTema();

  // Restaura a sessão pelo cookie de refresh ao abrir o app (uma vez).
  useEffect(() => {
    void restaurarSessao();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}
