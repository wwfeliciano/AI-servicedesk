import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';

import { LoginPage } from '@/pages/LoginPage';
import { useSessao } from '@/stores/sessao';
import { server } from '@/test/msw';
import { renderComProvedores } from '@/test/utils';

afterEach(() => {
  useSessao.setState({ usuario: null, accessToken: null, estado: 'verificando' });
});

describe('LoginPage (F1.3)', () => {
  it('faz login e grava a sessão em memória', async () => {
    const usuario = userEvent.setup();
    renderComProvedores(<LoginPage />, { rota: '/login' });

    await usuario.type(screen.getByLabelText('E-mail corporativo'), 'ana.lima@empresa.com.br');
    await usuario.type(screen.getByLabelText('Senha'), 'senha-super-ok');
    await usuario.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    await waitFor(() => {
      const s = useSessao.getState();
      expect(s.estado).toBe('autenticado');
      expect(s.accessToken).toBe('token-de-teste');
      expect(s.usuario?.tipo_perfil).toBe('ADMIN');
    });
  });

  it('FE01: mostra a mensagem genérica em credencial inválida (401)', async () => {
    server.use(
      http.post('/api/auth/login', () =>
        HttpResponse.json(
          { codigo: 'NAO_AUTENTICADO', mensagem: 'E-mail ou senha inválidos.' },
          { status: 401 },
        ),
      ),
    );
    const usuario = userEvent.setup();
    renderComProvedores(<LoginPage />, { rota: '/login' });

    await usuario.type(screen.getByLabelText('E-mail corporativo'), 'ana.lima@empresa.com.br');
    await usuario.type(screen.getByLabelText('Senha'), 'errada');
    await usuario.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha inválidos.');
    expect(useSessao.getState().estado).not.toBe('autenticado');
  });

  it('valida campos obrigatórios sem chamar a API', async () => {
    const usuario = userEvent.setup();
    renderComProvedores(<LoginPage />, { rota: '/login' });

    await usuario.click(screen.getByRole('button', { name: /entrar no sistema/i }));
    expect(await screen.findByText('Informe o e-mail.')).toBeInTheDocument();
    expect(screen.getByText('Informe a senha.')).toBeInTheDocument();
  });
});
