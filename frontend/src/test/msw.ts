import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

/**
 * Handlers padrão da API para os testes (MSW). Cada teste pode sobrescrever com
 * `server.use(...)` para simular erros (FE01, EMAIL_DUPLICADO, 429 etc.).
 */
export const handlers = [
  http.get('/api/config/publica', () =>
    HttpResponse.json({
      whatsapp_suporte: null,
      email_suporte: 'ti@empresa.com.br',
      google_sso: false,
      versao: '0.1.0',
    }),
  ),
  // Sem sessão por padrão: o refresh inicial falha (anônimo).
  http.post('/api/auth/refresh', () => new HttpResponse(null, { status: 401 })),
  http.post('/api/auth/login', () =>
    HttpResponse.json({
      access_token: 'token-de-teste',
      token_type: 'bearer',
      expires_in: 1800,
      usuario: {
        id_usuario: 1,
        nome: 'Ana Lima',
        email: 'ana.lima@empresa.com.br',
        tipo_perfil: 'ADMIN',
        cargo: 'Analista',
      },
    }),
  ),
  http.get('/api/categorias', () =>
    HttpResponse.json([
      { id_categoria: 1, nome_categoria: 'TI', icone: '💻', ordem: 1, ativa: true },
      { id_categoria: 2, nome_categoria: 'RH', icone: '👥', ordem: 2, ativa: true },
    ]),
  ),
  http.get('/api/chamados/resumo', () =>
    HttpResponse.json({
      abertos: 1,
      em_andamento: 0,
      resolvidos: 0,
      encerrados: 0,
      urgentes: 0,
    }),
  ),
  http.get('/api/chamados', () =>
    HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      contadores: { todos: 0, abertos: 0, em_andamento: 0, resolvidos: 0, encerrados: 0 },
    }),
  ),
  http.get('/api/notificacoes/contagem', () => HttpResponse.json({ nao_lidas: 0 })),
  http.get('/api/notificacoes', () =>
    HttpResponse.json({ items: [], total: 0, nao_lidas: 0, page: 1, page_size: 20 }),
  ),
  http.get('/api/chamados/:id/historico', () => HttpResponse.json([])),
  http.get('/api/chamados/:id/followups', () => HttpResponse.json([])),
  http.get('/api/chamados/:id/solucoes', () => HttpResponse.json([])),
  http.get('/api/chamados/:id/anexos', () => HttpResponse.json([])),
  http.get('/api/usuarios/tecnicos', () => HttpResponse.json([])),
  http.get('/api/base-conhecimento', () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 10 }),
  ),
  http.get('/api/perfil/whatsapp', () =>
    HttpResponse.json({
      vinculado: false,
      numero: null,
      opt_in: false,
      notificar_email: true,
    }),
  ),
  http.get('/api/sla/mes', () => HttpResponse.json({ total: 0, no_prazo: 0, percentual: 0 })),
];

export const server = setupServer(...handlers);
