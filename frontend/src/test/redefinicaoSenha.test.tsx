import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { EsqueciSenhaPage } from '@/pages/EsqueciSenhaPage';
import { RedefinirSenhaPage } from '@/pages/RedefinirSenhaPage';
import { server } from '@/test/msw';

function renderCom(ui: React.ReactElement, rota = '/') {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[rota]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('EsqueciSenhaPage (F7.1)', () => {
  it('envia o e-mail e mostra a confirmação genérica', async () => {
    server.use(
      http.post('/api/auth/esqueci-senha', () =>
        HttpResponse.json({ mensagem: 'Se o e-mail estiver cadastrado, enviaremos um link.' }),
      ),
    );
    renderCom(<EsqueciSenhaPage />, '/esqueci-senha');

    await userEvent.type(screen.getByLabelText(/e-mail corporativo/i), 'ana@empresa.com.br');
    await userEvent.click(screen.getByRole('button', { name: /enviar link/i }));

    expect(await screen.findByText('Verifique seu e-mail')).toBeInTheDocument();
  });
});

describe('RedefinirSenhaPage (F7.1)', () => {
  it('sem token mostra link inválido', () => {
    renderCom(<RedefinirSenhaPage />, '/redefinir-senha');
    expect(screen.getByText('Link inválido')).toBeInTheDocument();
  });

  it('com token, redefine a senha', async () => {
    let redefiniu = false;
    server.use(
      http.post('/api/auth/redefinir-senha', () => {
        redefiniu = true;
        return HttpResponse.json({ mensagem: 'Senha redefinida com sucesso.' });
      }),
    );
    renderCom(<RedefinirSenhaPage />, '/redefinir-senha?token=abc123');

    const [nova, confirmar] = screen.getAllByLabelText(/senha/i);
    await userEvent.type(nova, 'senha-nova-456');
    await userEvent.type(confirmar, 'senha-nova-456');
    await userEvent.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => expect(redefiniu).toBe(true));
    expect(await screen.findByText('Senha redefinida')).toBeInTheDocument();
  });
});
