import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AdminIntegracoesPage } from '@/pages/AdminIntegracoesPage';
import { server } from '@/test/msw';

function evento(id: number, status: string, tentativas = 0) {
  return {
    id_evento: id,
    tipo: 'CHAMADO_CRIADO',
    canal: 'EMAIL',
    destino: 'ana@empresa.com.br',
    status,
    tentativas,
    ultimo_erro: status === 'FALHOU' ? 'n8n fora' : null,
    proxima_tentativa_em: '2026-10-18T00:00:00Z',
    criado_em: '2026-10-18T00:00:00Z',
    enviado_em: null,
  };
}

function renderPagina() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <AdminIntegracoesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AdminIntegracoesPage (F6.4b)', () => {
  it('mostra o status da sessão e a fila do outbox', async () => {
    server.use(
      http.get('/api/admin/integracoes', () =>
        HttpResponse.json({ status: 'WORKING', detalhe: 'ok', atualizado_em: '2026-10-18T00:00:00Z' }),
      ),
      http.get('/api/admin/outbox', () =>
        HttpResponse.json({
          items: [evento(2, 'FALHOU', 3), evento(1, 'ENVIADO')],
          total: 2,
          page: 1,
          page_size: 20,
          contadores: { PENDENTE: 0, PROCESSANDO: 0, ENVIADO: 1, FALHOU: 1 },
        }),
      ),
    );
    renderPagina();

    expect(await screen.findByText('WORKING')).toBeInTheDocument();
    expect(
      await screen.findAllByText(/CHAMADO_CRIADO → ana@empresa.com.br/),
    ).toHaveLength(2);
    // Só o FALHOU tem botão Reenviar.
    expect(screen.getAllByRole('button', { name: /reenviar/i })).toHaveLength(1);
  });

  it('reenfileira um evento FALHOU', async () => {
    let reenviou = false;
    server.use(
      http.get('/api/admin/integracoes', () => HttpResponse.json({ status: 'WORKING' })),
      http.get('/api/admin/outbox', () =>
        HttpResponse.json({
          items: [evento(9, 'FALHOU', 8)],
          total: 1,
          page: 1,
          page_size: 20,
          contadores: { PENDENTE: 0, PROCESSANDO: 0, ENVIADO: 0, FALHOU: 1 },
        }),
      ),
      http.post('/api/admin/outbox/:id/reenviar', () => {
        reenviou = true;
        return HttpResponse.json(evento(9, 'PENDENTE'));
      }),
    );
    renderPagina();

    await userEvent.click(await screen.findByRole('button', { name: /reenviar/i }));
    await waitFor(() => expect(reenviou).toBe(true));
  });
});
