import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';

import { NovoChamadoPage } from '@/pages/NovoChamadoPage';
import { useRascunhoChamado } from '@/stores/rascunhoChamado';
import { server } from '@/test/msw';
import { renderComProvedores } from '@/test/utils';

afterEach(() => useRascunhoChamado.getState().limpar());

describe('NovoChamadoPage (F2.4)', () => {
  it('percorre as 3 etapas, abre o chamado e mostra o protocolo', async () => {
    server.use(
      http.post('/api/chamados', () =>
        HttpResponse.json(
          {
            id_chamado: 51,
            protocolo: 'TK-0051',
            titulo: 'VPN não conecta',
            descricao: 'Desde a atualização falha.',
            categoria: { id_categoria: 1, nome_categoria: 'TI', icone: '💻' },
            severidade: 'MEDIA',
            status_chamado: 'NOVO',
            status_grupo: 'abertos',
            solicitante: { id_usuario: 1, nome: 'Ana Lima' },
            tecnico_responsavel: null,
            qtd_mensagens: 0,
            data_criacao: '2026-10-17T14:32:00Z',
            data_atualizacao: '2026-10-17T14:32:00Z',
          },
          { status: 201 },
        ),
      ),
    );
    const usuario = userEvent.setup();
    renderComProvedores(<NovoChamadoPage />, { rota: '/chamados/novo' });

    // Etapa 1: escolher categoria.
    await usuario.click(await screen.findByRole('radio', { name: /TI/ }));
    await usuario.click(screen.getByRole('button', { name: /próximo/i }));

    // Etapa 2: prioridade (Média).
    await usuario.click(await screen.findByRole('radio', { name: /Média/ }));
    await usuario.click(screen.getByRole('button', { name: /próximo/i }));

    // Etapa 3: detalhes.
    await usuario.type(screen.getByLabelText(/Título do chamado/i), 'VPN não conecta');
    await usuario.type(screen.getByLabelText(/Descrição detalhada/i), 'Desde a atualização falha.');
    await usuario.click(screen.getByRole('button', { name: /enviar chamado/i }));

    // Confirmação com o protocolo.
    expect(await screen.findByText('TK-0051')).toBeInTheDocument();
    expect(screen.getByText('Chamado aberto!')).toBeInTheDocument();
  });

  it('FE02: bloqueia o envio quando título/descrição estão vazios', async () => {
    const usuario = userEvent.setup();
    renderComProvedores(<NovoChamadoPage />, { rota: '/chamados/novo' });

    await usuario.click(await screen.findByRole('radio', { name: /TI/ }));
    await usuario.click(screen.getByRole('button', { name: /próximo/i }));
    await usuario.click(await screen.findByRole('radio', { name: /Baixa/ }));
    await usuario.click(screen.getByRole('button', { name: /próximo/i }));

    // Etapa 3 sem preencher → mensagens de erro e sem confirmação.
    await usuario.click(await screen.findByRole('button', { name: /enviar chamado/i }));
    await waitFor(() => {
      expect(screen.getByText('Informe o título do chamado.')).toBeInTheDocument();
      expect(screen.getByText('Descreva o problema.')).toBeInTheDocument();
    });
    expect(screen.queryByText('Chamado aberto!')).not.toBeInTheDocument();
  });
});
