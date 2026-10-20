import createClient, { type Middleware } from 'openapi-fetch';

import type { paths } from '@/api/schema';
import { obterAccessToken, useSessao } from '@/stores/sessao';

/**
 * Cliente HTTP tipado (seção 8.1). baseUrl relativa: em dev o Vite faz proxy de
 * /api; em produção o Nginx do container "web". 
 *
 * Autenticação:
 *  - o access token fica só em memória (store de sessão) e é injetado no header;
 *  - em 401, tenta uma vez o /api/auth/refresh (cookie HttpOnly) e repete a
 *    requisição original; se o refresh falhar, limpa a sessão (vai para /login).
 */
// baseUrl absoluta a partir da origem atual (relativa quebra em jsdom/testes e
// mantém o proxy de /api em dev e o Nginx em produção).
const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
// `fetch` resolvido em tempo de chamada: garante que um patch posterior do
// globalThis.fetch (ex.: MSW nos testes) seja respeitado.
export const api = createClient<paths>({
  baseUrl,
  fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
});

/** Injeta `Authorization: Bearer <access_token>` quando há sessão. */
const middlewareAuth: Middleware = {
  onRequest({ request }) {
    const token = obterAccessToken();
    if (token) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },
};
api.use(middlewareAuth);

// Controle de refresh concorrente: só uma chamada de refresh por vez.
let refreshEmAndamento: Promise<boolean> | null = null;

/** Chama /api/auth/refresh uma vez; atualiza o access token na sessão. */
async function tentarRefresh(): Promise<boolean> {
  refreshEmAndamento ??= (async () => {
    try {
      const resp = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });
      if (!resp.ok) return false;
      const dados = (await resp.json()) as { access_token: string };
      useSessao.getState().definirAccessToken(dados.access_token);
      return true;
    } catch {
      return false;
    } finally {
      // Libera para uma próxima tentativa futura.
      setTimeout(() => {
        refreshEmAndamento = null;
      }, 0);
    }
  })();
  return refreshEmAndamento;
}

/**
 * Middleware de retry em 401: ao receber 401 numa rota que não seja a própria de
 * auth, tenta o refresh e repete a requisição original uma única vez.
 */
const middlewareRetry401: Middleware = {
  async onResponse({ request, response }) {
    if (response.status !== 401) return response;
    const url = new URL(request.url);
    // Não tenta refresh para as próprias rotas de login/refresh/logout.
    if (url.pathname.startsWith('/api/auth/')) return response;
    // Evita laço: se esta já é a repetição, não tenta de novo.
    if (request.headers.get('X-Repetido') === '1') return response;

    const ok = await tentarRefresh();
    if (!ok) {
      useSessao.getState().limparSessao();
      return response;
    }
    const novoToken = obterAccessToken();
    const repetida = new Request(request.url, request);
    repetida.headers.set('X-Repetido', '1');
    if (novoToken) repetida.headers.set('Authorization', `Bearer ${novoToken}`);
    return fetch(repetida);
  },
};
api.use(middlewareRetry401);
