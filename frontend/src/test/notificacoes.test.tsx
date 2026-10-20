import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { NotificacoesPage } from '@/pages/NotificacoesPage';
import { server } from '@/test/msw';
import { renderComProvedores } from '@/test/utils';

const UMA = {
  items: [
    {
      id_notificacao: 1,
      id_chamado: 41,
      tipo: 'CHAMADO_CRIADO',
      titulo: 'Chamado aberto',
      mensagem: 'Seu chamado TK-0041 foi aberto.',
      lida: false,
      data_criacao: '2026-10-17T12:00:00Z',
    },
  ],
  total: 1,
  nao_lidas: 1,
  page: 1,
  page_size: 20,
};

describe('NotificacoesPage (F3.3)', () => {
  it('lista as notificações e destaca as não lidas', async () => {
    server.use(http.get('/api/notificacoes', () => HttpResponse.json(UMA)));
    renderComProvedores(<NotificacoesPage />, { rota: '/notificacoes' });

    expect(await screen.findByText('Chamado aberto')).toBeInTheDocument();
    expect(screen.getByText('1 não lida')).toBeInTheDocument();
  });

  it('marca todas como lidas', async () => {
    let chamou = false;
    server.use(
      http.get('/api/notificacoes', () => HttpResponse.json(UMA)),
      http.post('/api/notificacoes/lidas', () => {
        chamou = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderComProvedores(<NotificacoesPage />, { rota: '/notificacoes' });

    const botao = await screen.findByRole('button', { name: /marcar todas como lidas/i });
    await userEvent.click(botao);
    await waitFor(() => expect(chamou).toBe(true));
  });

  it('mostra o estado vazio', async () => {
    // handler padrão (lista vazia)
    renderComProvedores(<NotificacoesPage />, { rota: '/notificacoes' });
    expect(await screen.findByText('Você não tem notificações.')).toBeInTheDocument();
  });
});
