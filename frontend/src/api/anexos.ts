import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';
import { obterAccessToken } from '@/stores/sessao';

export type AnexoSaida = components['schemas']['AnexoSaida'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Tipos e limite aceitos no cliente (espelham o backend, B9/B10). */
export const MIMES_ACEITOS = ['image/png', 'image/jpeg', 'application/pdf'] as const;
export const MAX_BYTES = 10 * 1024 * 1024;
export const MAX_POR_CHAMADO = 5;

/** Lista os anexos de um chamado. */
export async function listarAnexos(idChamado: number): Promise<AnexoSaida[]> {
  const { data, error } = await api.GET('/api/chamados/{id_chamado}/anexos', {
    params: { path: { id_chamado: idChamado } },
  });
  if (error || !data) lancar(error);
  return data;
}

/**
 * Envia um anexo (multipart). openapi-fetch não cobre bem upload de arquivo, então
 * usamos `fetch` direto com o token em memória e o mesmo baseUrl/origin do client.
 */
export async function enviarAnexo(idChamado: number, arquivo: File): Promise<AnexoSaida> {
  const form = new FormData();
  form.append('arquivo', arquivo);
  const token = obterAccessToken();
  const resp = await fetch(`/api/chamados/${idChamado}/anexos`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!resp.ok) {
    let corpo: unknown = null;
    try {
      corpo = await resp.json();
    } catch {
      corpo = { codigo: 'ERRO', mensagem: 'Falha ao enviar o anexo.' };
    }
    lancar(corpo);
  }
  return (await resp.json()) as AnexoSaida;
}

/** URL de download do anexo (abre em nova aba; o backend exige o token no header,
 * então o download é feito por fetch autenticado, não por link direto). */
export async function baixarAnexo(anexo: AnexoSaida): Promise<void> {
  const token = obterAccessToken();
  const resp = await fetch(`/api/anexos/${anexo.id_anexo}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) lancar({ codigo: 'ERRO', mensagem: 'Não foi possível baixar o anexo.' });
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = anexo.nome_original;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
