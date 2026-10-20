import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';

export type NotificacaoSaida = components['schemas']['NotificacaoSaida'];
export type ListaNotificacoes = components['schemas']['ListaNotificacoes'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Lista as notificações do usuário (não lidas primeiro). */
export async function listarNotificacoes(page = 1, pageSize = 20): Promise<ListaNotificacoes> {
  const { data, error } = await api.GET('/api/notificacoes', {
    params: { query: { page, page_size: pageSize } },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Contador de não lidas (badge do menu). */
export async function contarNaoLidas(): Promise<number> {
  const { data, error } = await api.GET('/api/notificacoes/contagem', {});
  if (error || !data) lancar(error);
  return data.nao_lidas;
}

/** Marca uma notificação como lida. */
export async function marcarLida(idNotificacao: number): Promise<void> {
  const { error } = await api.POST('/api/notificacoes/{id_notificacao}/lida', {
    params: { path: { id_notificacao: idNotificacao } },
  });
  if (error) lancar(error);
}

/** Marca todas as notificações como lidas. */
export async function marcarTodasLidas(): Promise<void> {
  const { error } = await api.POST('/api/notificacoes/lidas', {});
  if (error) lancar(error);
}
