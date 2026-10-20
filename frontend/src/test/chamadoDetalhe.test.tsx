import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';

import { ChamadoDetalhePage } from '@/pages/ChamadoDetalhePage';
import { useSessao } from '@/stores/sessao';
import { server } from '@/test/msw';

function chamado(status: string) {
  return {
    id_chamado: 41,
    protocolo: 'TK-0041',
    titulo: 'VPN não conecta',
    descricao: 'Desde a atualização falha.',
    categoria: { id_categoria: 1, nome_categoria: 'TI', icone: '💻' },
    severidade: 'ALTA',
    status_chamado: status,
    status_grupo: status === 'FECHADO' ? 'encerrados' : 'resolvidos',
    solicitante: { id_usuario: 7, nome: 'Ana Lima' },
    tecnico_responsavel: { id_usuario: 3, nome: 'Rafael' },
    qtd_mensagens: 0,
    data_criacao: '2026-10-17T12:00:00Z',
    data_atualizacao: '2026-10-17T13:00:00Z',
  };
}

function renderDetalhe() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={['/chamados/41']}>
        <Routes>
          <Route path="/chamados/:id" element={<ChamadoDetalhePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => useSessao.setState({ usuario: null, accessToken: null, estado: 'verificando' }));

describe('ChamadoDetalhePage (F4.3)', () => {
  it('mostra o cartão da solução ao solicitante quando CONCLUIDO e permite aprovar', async () => {
    // Usuário logado = solicitante (id 7).
    useSessao.setState({
      usuario: { id_usuario: 7, nome: 'Ana Lima', email: 'ana@x.com', tipo_perfil: 'CLIENTE' },
      accessToken: 't',
      estado: 'autenticado',
    });
    let aprovou = false;
    server.use(
      http.get('/api/chamados/:id', () => HttpResponse.json(chamado('CONCLUIDO'))),
      http.get('/api/chamados/:id/solucoes', () =>
        HttpResponse.json([
          {
            id_solucao: 9,
            descricao_solucao: 'Reinstalei o cliente VPN.',
            status_aprovacao: 'PENDENTE_APROVACAO',
            id_analista: 3,
            data_solucao: '2026-10-17T13:00:00Z',
          },
        ]),
      ),
      http.post('/api/solucoes/:id/resposta', () => {
        aprovou = true;
        return HttpResponse.json(chamado('FECHADO'));
      }),
    );

    renderDetalhe();
    expect(await screen.findByText('Solução proposta')).toBeInTheDocument();
    expect(screen.getByText('Reinstalei o cliente VPN.')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /aprovar e encerrar/i }));
    await waitFor(() => expect(aprovou).toBe(true));
  });

  it('mostra ações de técnico (Registrar solução) quando ATRIBUIDO', async () => {
    useSessao.setState({
      usuario: { id_usuario: 3, nome: 'Rafael', email: 'r@x.com', tipo_perfil: 'ANALISTA' },
      accessToken: 't',
      estado: 'autenticado',
    });
    server.use(http.get('/api/chamados/:id', () => HttpResponse.json(chamado('ATRIBUIDO'))));
    renderDetalhe();
    expect(await screen.findByRole('button', { name: /registrar solução/i })).toBeInTheDocument();
    // Cliente não veria o cartão de solução aqui (status ATRIBUIDO).
    expect(screen.queryByText('Solução proposta')).not.toBeInTheDocument();
  });
});
