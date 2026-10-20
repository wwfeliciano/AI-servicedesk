import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';

import { BaseConhecimentoPage } from '@/pages/BaseConhecimentoPage';
import { useSessao } from '@/stores/sessao';
import { server } from '@/test/msw';

function artigo(id: number, titulo: string, categoria = 'TI', idCategoria = 1) {
  return {
    id_base: id,
    id_solucao: id + 100,
    titulo,
    conteudo: `Passo a passo de ${titulo}.`,
    categoria: { id_categoria: idCategoria, nome_categoria: categoria, icone: '💻' },
    data_inclusao: '2026-10-17T12:00:00Z',
  };
}

function renderPagina(rota = '/base-conhecimento') {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[rota]}>
        <BaseConhecimentoPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => useSessao.setState({ usuario: null, accessToken: null, estado: 'verificando' }));

describe('BaseConhecimentoPage (F5.2)', () => {
  it('lista artigos e expande o conteúdo no acordeão', async () => {
    server.use(
      http.get('/api/base-conhecimento', () =>
        HttpResponse.json({
          items: [artigo(1, 'Solução de VPN'), artigo(2, 'Resetar senha', 'RH', 2)],
          total: 2,
          page: 1,
          page_size: 10,
        }),
      ),
    );
    renderPagina();

    expect(await screen.findByText('Solução de VPN')).toBeInTheDocument();
    expect(screen.getByText('Resetar senha')).toBeInTheDocument();
    // Conteúdo fica oculto até expandir.
    expect(screen.queryByText('Passo a passo de Solução de VPN.')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Solução de VPN/i }));
    expect(await screen.findByText('Passo a passo de Solução de VPN.')).toBeInTheDocument();
    // O acordeão aberto expõe o "Abrir chamado" com o prefill da categoria.
    const link = screen.getByRole('link', { name: /abrir chamado/i });
    expect(link).toHaveAttribute('href', expect.stringContaining('categoria=1'));
    expect(link.getAttribute('href')).toContain('titulo=Solu');
  });

  it('busca por palavra-chave repassando q para a API', async () => {
    let qRecebido: string | null = null;
    server.use(
      http.get('/api/base-conhecimento', ({ request }) => {
        qRecebido = new URL(request.url).searchParams.get('q');
        return HttpResponse.json({
          items: qRecebido ? [artigo(1, 'Solução de VPN')] : [],
          total: qRecebido ? 1 : 0,
          page: 1,
          page_size: 10,
        });
      }),
    );
    renderPagina();

    await userEvent.type(screen.getByLabelText('Buscar na base de conhecimento'), 'vpn');
    await waitFor(() => expect(qRecebido).toBe('vpn'));
    expect(await screen.findByText('Solução de VPN')).toBeInTheDocument();
  });

  it('filtra por categoria repassando id_categoria para a API', async () => {
    let idCategoria: string | null = null;
    server.use(
      http.get('/api/base-conhecimento', ({ request }) => {
        idCategoria = new URL(request.url).searchParams.get('id_categoria');
        return HttpResponse.json({ items: [], total: 0, page: 1, page_size: 10 });
      }),
    );
    renderPagina();

    // O chip de categoria vem de /api/categorias (handler padrão: TI=1, RH=2).
    await userEvent.click(await screen.findByRole('button', { name: /RH/i }));
    await waitFor(() => expect(idCategoria).toBe('2'));
  });

  it('não mostra o botão Editar para CLIENTE', async () => {
    useSessao.setState({
      usuario: { id_usuario: 7, nome: 'Ana', email: 'a@x.com', tipo_perfil: 'CLIENTE' },
      accessToken: 't',
      estado: 'autenticado',
    });
    server.use(
      http.get('/api/base-conhecimento', () =>
        HttpResponse.json({ items: [artigo(1, 'Solução de VPN')], total: 1, page: 1, page_size: 10 }),
      ),
    );
    renderPagina();
    await userEvent.click(await screen.findByRole('button', { name: /Solução de VPN/i }));
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument();
  });

  it('permite ANALISTA/ADMIN editar um artigo (PATCH)', async () => {
    useSessao.setState({
      usuario: { id_usuario: 3, nome: 'Rafael', email: 'r@x.com', tipo_perfil: 'ANALISTA' },
      accessToken: 't',
      estado: 'autenticado',
    });
    let editou = false;
    server.use(
      http.get('/api/base-conhecimento', () =>
        HttpResponse.json({ items: [artigo(1, 'Solução de VPN')], total: 1, page: 1, page_size: 10 }),
      ),
      http.patch('/api/base-conhecimento/:id', () => {
        editou = true;
        return HttpResponse.json(artigo(1, 'Solução de VPN (revisada)'));
      }),
    );
    renderPagina();

    await userEvent.click(await screen.findByRole('button', { name: /Solução de VPN/i }));
    await userEvent.click(screen.getByRole('button', { name: /editar/i }));
    expect(await screen.findByRole('dialog', { name: /editar artigo/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /salvar/i }));
    await waitFor(() => expect(editou).toBe(true));
  });
});
