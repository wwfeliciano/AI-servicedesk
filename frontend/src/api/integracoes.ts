import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';

export type EventoOutbox = components['schemas']['EventoOutboxSaida'];
export type PaginaOutbox = components['schemas']['PaginaOutboxSaida'];
export type SessaoWhatsapp = components['schemas']['SessaoWhatsappSaida'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Status da sessão do WhatsApp (ADMIN). */
export async function obterSessaoWhatsapp(): Promise<SessaoWhatsapp> {
  const { data, error } = await api.GET('/api/admin/integracoes', {});
  if (error || !data) lancar(error);
  return data;
}

export interface FiltroOutbox {
  status?: 'PENDENTE' | 'PROCESSANDO' | 'ENVIADO' | 'FALHOU';
  page?: number;
  page_size?: number;
}

/** Fila do outbox (ADMIN), por status, com contadores. */
export async function listarOutbox(filtro: FiltroOutbox = {}): Promise<PaginaOutbox> {
  const query: Record<string, string | number> = {
    page: filtro.page ?? 1,
    page_size: filtro.page_size ?? 20,
  };
  if (filtro.status) query.status = filtro.status;
  const { data, error } = await api.GET('/api/admin/outbox', { params: { query } });
  if (error || !data) lancar(error);
  return data;
}

/** Reenfileira um evento (FALHOU → PENDENTE). */
export async function reenviarOutbox(idEvento: number): Promise<EventoOutbox> {
  const { data, error } = await api.POST('/api/admin/outbox/{id_evento}/reenviar', {
    params: { path: { id_evento: idEvento } },
  });
  if (error || !data) lancar(error);
  return data;
}
