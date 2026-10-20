import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';

export type ArtigoSaida = components['schemas']['ArtigoSaida'];
export type PaginaArtigosSaida = components['schemas']['PaginaArtigosSaida'];
export type ArtigoCategoria = components['schemas']['ArtigoCategoria'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

export interface FiltroArtigos {
  q?: string;
  id_categoria?: number;
  page?: number;
  page_size?: number;
}

/** Busca/lista artigos da Base de Conhecimento (qualquer autenticado; RF06, UC04). */
export async function listarArtigos(filtro: FiltroArtigos = {}): Promise<PaginaArtigosSaida> {
  const query: Record<string, string | number> = {
    page: filtro.page ?? 1,
    page_size: filtro.page_size ?? 10,
  };
  if (filtro.q) query.q = filtro.q;
  if (filtro.id_categoria) query.id_categoria = filtro.id_categoria;

  const { data, error } = await api.GET('/api/base-conhecimento', { params: { query } });
  if (error || !data) lancar(error);
  return data;
}

/** Detalhe de um artigo por id (404 se inexistente). */
export async function obterArtigo(idBase: number): Promise<ArtigoSaida> {
  const { data, error } = await api.GET('/api/base-conhecimento/{id_base}', {
    params: { path: { id_base: idBase } },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Publica um artigo a partir de uma solução aprovada (ANALISTA/ADMIN; RN05). */
export async function publicarArtigo(dados: {
  id_solucao: number;
  titulo: string;
  conteudo: string;
}): Promise<ArtigoSaida> {
  const { data, error } = await api.POST('/api/base-conhecimento', { body: dados });
  if (error || !data) lancar(error);
  return data;
}

/** Edita o título/conteúdo de um artigo (ANALISTA/ADMIN). */
export async function editarArtigo(
  idBase: number,
  dados: { titulo?: string; conteudo?: string },
): Promise<ArtigoSaida> {
  const { data, error } = await api.PATCH('/api/base-conhecimento/{id_base}', {
    params: { path: { id_base: idBase } },
    body: dados,
  });
  if (error || !data) lancar(error);
  return data;
}
