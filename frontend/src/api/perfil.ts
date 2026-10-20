import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';

export type StatusVinculo = components['schemas']['StatusSaida'];
export type VinculoGerado = components['schemas']['VinculoSaida'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Status do vínculo de WhatsApp e preferências (F6.3). */
export async function obterStatusWhatsapp(): Promise<StatusVinculo> {
  const { data, error } = await api.GET('/api/perfil/whatsapp', {});
  if (error || !data) lancar(error);
  return data;
}

/** Gera o código de vínculo + link wa.me (exige consentimento). */
export async function gerarVinculoWhatsapp(consentimento: boolean): Promise<VinculoGerado> {
  const { data, error } = await api.POST('/api/perfil/whatsapp/vinculo', {
    body: { consentimento },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Desvincula o WhatsApp (opt-out). */
export async function desvincularWhatsapp(): Promise<StatusVinculo> {
  const { data, error } = await api.DELETE('/api/perfil/whatsapp', {});
  if (error || !data) lancar(error);
  return data;
}

/** Atualiza as preferências de notificação (e-mail / WhatsApp). */
export async function atualizarPreferencias(dados: {
  notificar_email?: boolean;
  whatsapp_opt_in?: boolean;
}): Promise<StatusVinculo> {
  const { data, error } = await api.PATCH('/api/perfil/preferencias', { body: dados });
  if (error || !data) lancar(error);
  return data;
}
