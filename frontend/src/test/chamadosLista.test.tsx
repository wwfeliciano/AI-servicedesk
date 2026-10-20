import { http, HttpResponse } from 'msw';
import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ChamadosPage } from '@/pages/ChamadosPage';
import { server } from '@/test/msw';
import { renderComProvedores } from '@/test/utils';

function chamado(id: number, titulo: string, severidade = 'BAIXA', status = 'NOVO') {
  return {
    id_chamado: id,
    protocolo: `TK-${String(id).padStart(4, '0')}`,
    titulo,
    descricao: 'Descrição.',
    categoria: { id_categoria: 1, nome_categoria: 'TI', icone: '💻' },
    severidade,
    status_chamado: status,
    status_grupo: 'abertos',
    solicitante: { id_usuario: 1, nome: 'Ana Lima' },
    tecnico_responsavel: null,
    qtd_mensagens: 0,
    data_criacao: '2026-10-17T12:00:00Z',
    data_atualizacao: '2026-10-17T12:00:00Z',
  };
}

describe('ChamadosPage (F2.4)', () => {
  it('lista os chamados e mostra os contadores das abas', async () => {
    server.use(
      http.get('/api/chamados', () =>
        HttpResponse.json({
          items: [chamado(41, 'VPN não conecta', 'CRITICO'), chamado(40, 'Acesso ao Protheus')],
          total: 2,
          page: 1,
          page_size: 10,
          contadores: { todos: 2, abertos: 2, em_andamento: 0, resolvidos: 0, encerrados: 0 },
        }),
      ),
    );
    renderComProvedores(<ChamadosPage />, { rota: '/chamados' });

    expect(await screen.findByText('VPN não conecta')).toBeInTheDocument();
    expect(screen.getByText('Acesso ao Protheus')).toBeInTheDocument();
    expect(screen.getByText('2 chamados no total')).toBeInTheDocument();
    // Protocolo em fonte monoespaçada.
    expect(screen.getByText('TK-0041')).toBeInTheDocument();
  });

  it('mostra estado vazio quando não há chamados', async () => {
    // Usa o handler padrão (lista vazia).
    renderComProvedores(<ChamadosPage />, { rota: '/chamados' });
    expect(
      await screen.findByText('Nenhum chamado encontrado com esses filtros.'),
    ).toBeInTheDocument();
  });
});
