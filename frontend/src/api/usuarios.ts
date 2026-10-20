import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';
import type { Perfil } from '@/types/dominio';

export type UsuarioDetalhe = components['schemas']['UsuarioDetalhe'];
export type PaginaUsuarios = components['schemas']['PaginaUsuariosSaida'];
export type ConfigPublica = components['schemas']['ConfigPublica'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

export interface FiltroUsuarios {
  q?: string;
  perfil?: Perfil;
  ativo?: boolean;
  page?: number;
  page_size?: number;
}

/** Lista paginada de usuários (ADMIN). */
export async function listarUsuarios(filtro: FiltroUsuarios = {}): Promise<PaginaUsuarios> {
  const query: Record<string, string | number | boolean> = {
    page: filtro.page ?? 1,
    page_size: filtro.page_size ?? 10,
  };
  if (filtro.q) query.q = filtro.q;
  if (filtro.perfil) query.perfil = filtro.perfil;
  if (filtro.ativo !== undefined) query.ativo = filtro.ativo;

  const { data, error } = await api.GET('/api/usuarios', {
    params: { query },
  });
  if (error || !data) lancar(error);
  return data;
}

export interface NovoUsuario {
  nome: string;
  email: string;
  senha: string;
  tipo_perfil: Perfil;
  cargo?: string;
}

/** Cadastra um usuário (ADMIN). Lança ErroAPI (EMAIL_DUPLICADO, VALIDACAO...). */
export async function cadastrarUsuario(novo: NovoUsuario): Promise<UsuarioDetalhe> {
  const { data, error } = await api.POST('/api/usuarios', {
    body: {
      nome: novo.nome,
      email: novo.email,
      senha: novo.senha,
      tipo_perfil: novo.tipo_perfil,
      ...(novo.cargo ? { cargo: novo.cargo } : {}),
    },
  });
  if (error || !data) lancar(error);
  return data;
}

/** Configuração pública da tela de login (rota pública). */
export async function obterConfigPublica(): Promise<ConfigPublica> {
  const { data, error } = await api.GET('/api/config/publica', {});
  if (error || !data) lancar(error);
  return data;
}

export interface AtualizacaoUsuario {
  nome?: string;
  cargo?: string;
  tipo_perfil?: Perfil;
  ativo?: boolean;
}

/** Atualiza/ativa/desativa um usuário (ADMIN; PATCH). Lança ErroAPI com campos. */
export async function atualizarUsuario(
  id: number,
  dados: AtualizacaoUsuario,
): Promise<UsuarioDetalhe> {
  const { data, error } = await api.PATCH('/api/usuarios/{id_usuario}', {
    params: { path: { id_usuario: id } },
    body: dados,
  });
  if (error || !data) lancar(error);
  return data;
}
