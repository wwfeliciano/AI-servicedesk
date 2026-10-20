import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';
import type { GrupoStatus, Severidade } from '@/types/dominio';

export type ChamadoSaida = components['schemas']['ChamadoSaida'];
export type ChamadoLista = components['schemas']['ChamadoLista'];
export type ResumoSaida = components['schemas']['ResumoSaida'];
export type CategoriaSaida = components['schemas']['CategoriaSaida'];
export type ContadoresChamados = components['schemas']['ContadoresChamados'];
export type HistoricoSaida = components['schemas']['HistoricoSaida'];
export type SolucaoSaida = components['schemas']['SolucaoSaida'];
export type FollowUpSaida = components['schemas']['FollowUpSaida'];
export type TecnicoSaida = components['schemas']['TecnicoSaida'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Categorias ativas (etapa 1 do wizard). */
export async function listarCategorias(): Promise<CategoriaSaida[]> {
  const { data, error } = await api.GET('/api/categorias', {});
  if (error || !data) lancar(error);
  return data;
}

export interface FiltroChamados {
  q?: string;
  grupo?: GrupoStatus;
  id_categoria?: number;
  page?: number;
  page_size?: number;
}

/** Lista de chamados com busca, filtros, contadores e paginação (escopo do perfil). */
export async function listarChamados(filtro: FiltroChamados = {}): Promise<ChamadoLista> {
  const query: Record<string, string | number> = {
    page: filtro.page ?? 1,
    page_size: filtro.page_size ?? 10,
  };
  if (filtro.q) query.q = filtro.q;
  if (filtro.grupo) query.grupo = filtro.grupo;
  if (filtro.id_categoria) query.id_categoria = filtro.id_categoria;

  const { data, error } = await api.GET('/api/chamados', { params: { query } });
  if (error || !data) lancar(error);
  return data;
}

/** Indicadores do Dashboard (abertos/em_andamento/resolvidos/encerrados/urgentes). */
export async function obterResumo(): Promise<ResumoSaida> {
  const { data, error } = await api.GET('/api/chamados/resumo', {});
  if (error || !data) lancar(error);
  return data;
}

/** Detalhe de um chamado por id (404 se fora do escopo/inexistente). */
export async function obterChamado(id: number): Promise<ChamadoSaida> {
  const { data, error } = await api.GET('/api/chamados/{id_chamado}', {
    params: { path: { id_chamado: id } },
  });
  if (error || !data) lancar(error);
  return data;
}

export interface NovoChamado {
  id_categoria: number;
  severidade: Severidade;
  titulo: string;
  descricao: string;
}

/** Abre um chamado para o próprio usuário. Lança ErroAPI (CATEGORIA_INVALIDA, VALIDACAO...). */
export async function abrirChamado(novo: NovoChamado): Promise<ChamadoSaida> {
  const { data, error } = await api.POST('/api/chamados', {
    body: {
      id_categoria: novo.id_categoria,
      severidade: novo.severidade,
      titulo: novo.titulo,
      descricao: novo.descricao,
    },
  });
  if (error || !data) lancar(error);
  return data;
}


/** Triagem: NOVO → PENDENTE (ANALISTA/ADMIN). */
export async function triar(
  id: number,
  dados: { id_categoria?: number; severidade?: Severidade; observacao?: string } = {},
): Promise<ChamadoSaida> {
  const { data, error } = await api.POST('/api/chamados/{id_chamado}/triagem', {
    params: { path: { id_chamado: id } },
    body: dados,
  });
  if (error || !data) lancar(error);
  return data;
}

/** Atribuição: → ATRIBUIDO (RN03). */
export async function atribuir(
  id: number,
  idTecnico: number,
  observacao?: string,
): Promise<ChamadoSaida> {
  const { data, error } = await api.POST('/api/chamados/{id_chamado}/atribuicao', {
    params: { path: { id_chamado: id } },
    body: { id_tecnico: idTecnico, ...(observacao ? { observacao } : {}) },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Conclusão: registra a solução → CONCLUIDO (RN01). */
export async function concluir(id: number, descricaoSolucao: string): Promise<ChamadoSaida> {
  const { data, error } = await api.POST('/api/chamados/{id_chamado}/solucoes', {
    params: { path: { id_chamado: id } },
    body: { descricao_solucao: descricaoSolucao },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Resposta do solicitante à solução: aprovar/reprovar (RN02). */
export async function responderSolucao(
  idSolucao: number,
  aprovada: boolean,
  motivo?: string,
): Promise<ChamadoSaida> {
  const { data, error } = await api.POST('/api/solucoes/{id_solucao}/resposta', {
    params: { path: { id_solucao: idSolucao } },
    body: { aprovada, ...(motivo ? { motivo } : {}) },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Linha do tempo (histórico de status) do chamado. */
export async function listarHistorico(id: number): Promise<HistoricoSaida[]> {
  const { data, error } = await api.GET('/api/chamados/{id_chamado}/historico', {
    params: { path: { id_chamado: id } },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Soluções do chamado (para o cartão de solução no detalhe). */
export async function listarSolucoes(id: number): Promise<SolucaoSaida[]> {
  const { data, error } = await api.GET('/api/chamados/{id_chamado}/solucoes', {
    params: { path: { id_chamado: id } },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Follow-ups (mensagens) do chamado. */
export async function listarFollowups(id: number): Promise<FollowUpSaida[]> {
  const { data, error } = await api.GET('/api/chamados/{id_chamado}/followups', {
    params: { path: { id_chamado: id } },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Adiciona um follow-up ao chamado. */
export async function adicionarFollowup(id: number, mensagem: string): Promise<FollowUpSaida> {
  const { data, error } = await api.POST('/api/chamados/{id_chamado}/followups', {
    params: { path: { id_chamado: id } },
    body: { mensagem },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Técnicos ativos (ANALISTA/ADMIN) para a atribuição. */
export async function listarTecnicos(): Promise<TecnicoSaida[]> {
  const { data, error } = await api.GET('/api/usuarios/tecnicos', {});
  if (error || !data) lancar(error);
  return data;
}
