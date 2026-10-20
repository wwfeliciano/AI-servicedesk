import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';

import { PerfilPage } from '@/pages/PerfilPage';
import { useSessao } from '@/stores/sessao';
import { server } from '@/test/msw';

function renderPerfil() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => useSessao.setState({ usuario: null, accessToken: null, estado: 'verificando' }));

describe('PerfilPage — WhatsApp (F6.3)', () => {
  it('exige consentimento e gera o código + link wa.me', async () => {
    useSessao.setState({
      usuario: { id_usuario: 1, nome: 'Ana', email: 'a@x.com', tipo_perfil: 'CLIENTE' },
      accessToken: 't',
      estado: 'autenticado',
    });
    server.use(
      http.post('/api/perfil/whatsapp/vinculo', () =>
        HttpResponse.json({
          codigo: '123456',
          link_wa: 'https://wa.me/5515999999999?text=VINCULAR%20123456',
          expira_em_segundos: 600,
        }),
      ),
    );
    renderPerfil();

    const botao = await screen.findByRole('button', { name: /vincular whatsapp/i });
    // Desabilitado sem consentimento.
    expect(botao).toBeDisabled();

    await userEvent.click(screen.getByRole('checkbox', { name: /aceito receber/i }));
    expect(botao).toBeEnabled();
    await userEvent.click(botao);

    expect(await screen.findByText('123456')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /abrir no whatsapp/i });
    expect(link).toHaveAttribute('href', expect.stringContaining('wa.me/5515999999999'));
  });

  it('mostra o estado vinculado e permite desvincular', async () => {
    useSessao.setState({
      usuario: { id_usuario: 1, nome: 'Ana', email: 'a@x.com', tipo_perfil: 'CLIENTE' },
      accessToken: 't',
      estado: 'autenticado',
    });
    let desvinculou = false;
    server.use(
      http.get('/api/perfil/whatsapp', () =>
        HttpResponse.json({
          vinculado: true,
          numero: '5515999990000',
          opt_in: true,
          notificar_email: true,
        }),
      ),
      http.delete('/api/perfil/whatsapp', () => {
        desvinculou = true;
        return HttpResponse.json({
          vinculado: false,
          numero: null,
          opt_in: false,
          notificar_email: true,
        });
      }),
    );
    renderPerfil();

    expect(await screen.findByText('WhatsApp vinculado')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /desvincular/i }));
    await waitFor(() => expect(desvinculou).toBe(true));
  });
});
