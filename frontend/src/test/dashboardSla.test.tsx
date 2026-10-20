import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';

import { DashboardPage } from '@/pages/DashboardPage';
import { useSessao } from '@/stores/sessao';
import { server } from '@/test/msw';

function renderDashboard() {
  useSessao.setState({
    usuario: { id_usuario: 1, nome: 'Ana Lima', email: 'a@x.com', tipo_perfil: 'CLIENTE' },
    accessToken: 't',
    estado: 'autenticado',
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => useSessao.setState({ usuario: null, accessToken: null, estado: 'verificando' }));

describe('DashboardPage — SLA do mês (F7.2)', () => {
  it('mostra o percentual quando há chamados concluídos', async () => {
    server.use(
      http.get('/api/sla/mes', () =>
        HttpResponse.json({ total: 4, no_prazo: 3, percentual: 75 }),
      ),
    );
    renderDashboard();
    expect(await screen.findByText('75%')).toBeInTheDocument();
    expect(screen.getByText(/3 de 4 chamados concluídos no prazo/)).toBeInTheDocument();
  });

  it('mostra o estado vazio sem concluídos no mês', async () => {
    // handler padrão: total 0
    renderDashboard();
    expect(
      await screen.findByText('Ainda não há chamados concluídos neste mês.'),
    ).toBeInTheDocument();
  });
});
