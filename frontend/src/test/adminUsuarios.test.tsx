import { http, HttpResponse } from 'msw';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { AdminUsuariosPage } from '@/pages/AdminUsuariosPage';
import { server } from '@/test/msw';
import { renderComProvedores } from '@/test/utils';

const UM_USUARIO = {
  items: [
    {
      id_usuario: 1,
      nome: 'Ana Lima',
      email: 'ana.lima@empresa.com.br',
      tipo_perfil: 'ADMIN',
      cargo: 'Analista',
      ativo: true,
      data_cadastro: '2026-10-17T12:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
};

describe('AdminUsuariosPage (F1.3)', () => {
  it('lista os usuários retornados pela API', async () => {
    server.use(http.get('/api/usuarios', () => HttpResponse.json(UM_USUARIO)));
    renderComProvedores(<AdminUsuariosPage />);

    expect(await screen.findByText('Ana Lima')).toBeInTheDocument();
    expect(screen.getByText('ana.lima@empresa.com.br')).toBeInTheDocument();
    expect(screen.getByText('1 usuário · página 1 de 1')).toBeInTheDocument();
  });

  it('mostra erro no campo e-mail quando a API responde EMAIL_DUPLICADO (409)', async () => {
    server.use(
      http.get('/api/usuarios', () => HttpResponse.json(UM_USUARIO)),
      http.post('/api/usuarios', () =>
        HttpResponse.json(
          {
            codigo: 'EMAIL_DUPLICADO',
            mensagem: 'Este e-mail já está cadastrado.',
            campos: { email: 'Este e-mail já está cadastrado.' },
          },
          { status: 409 },
        ),
      ),
    );
    const usuario = userEvent.setup();
    renderComProvedores(<AdminUsuariosPage />);

    await usuario.click(await screen.findByRole('button', { name: /novo usuário/i }));
    const dialogo = await screen.findByRole('dialog', { name: 'Novo usuário' });

    await usuario.type(within(dialogo).getByLabelText('Nome'), 'Repetida');
    await usuario.type(within(dialogo).getByLabelText('E-mail'), 'ana.lima@empresa.com.br');
    await usuario.type(within(dialogo).getByLabelText('Senha'), 'senha-super-ok');
    await usuario.click(within(dialogo).getByRole('button', { name: /^cadastrar$/i }));

    await waitFor(() =>
      expect(within(dialogo).getByText('Este e-mail já está cadastrado.')).toBeInTheDocument(),
    );
  });

  it('desativa um usuário via PATCH (ativar/desativar)', async () => {
    let corpoPatch: unknown = null;
    server.use(
      http.get('/api/usuarios', () => HttpResponse.json(UM_USUARIO)),
      http.patch('/api/usuarios/:id', async ({ request }) => {
        corpoPatch = await request.json();
        return HttpResponse.json({ ...UM_USUARIO.items[0], ativo: false });
      }),
    );
    const usuario = userEvent.setup();
    renderComProvedores(<AdminUsuariosPage />);

    await usuario.click(await screen.findByRole('button', { name: /desativar/i }));
    await waitFor(() => expect(corpoPatch).toEqual({ ativo: false }));
  });
});
