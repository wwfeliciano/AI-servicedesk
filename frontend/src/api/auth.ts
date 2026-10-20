import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';
import type { Perfil, Usuario } from '@/types/dominio';
import { useSessao } from '@/stores/sessao';

type LoginSaida = components['schemas']['LoginSaida'];
type UsuarioPublico = components['schemas']['UsuarioPublico'];

/** Converte o usuário público da API no tipo de domínio do front. */
function paraUsuario(u: UsuarioPublico): Usuario {
  return {
    id_usuario: u.id_usuario,
    nome: u.nome,
    email: u.email,
    tipo_perfil: u.tipo_perfil as Perfil,
    ...(u.cargo ? { cargo: u.cargo } : {}),
  };
}

/** Lança o corpo de erro da API (ErroAPI) para o chamador tratar. */
function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** Login: grava a sessão (access token em memória) e devolve o usuário. */
export async function login(email: string, senha: string): Promise<Usuario> {
  const { data, error } = await api.POST('/api/auth/login', {
    body: { email, senha },
  });
  if (error || !data) lancar(error);
  const saida = data as LoginSaida;
  const usuario = paraUsuario(saida.usuario);
  useSessao.getState().definirSessao(usuario, saida.access_token);
  return usuario;
}

/** Logout: revoga o refresh no servidor e limpa a sessão local. */
export async function logout(): Promise<void> {
  try {
    await api.POST('/api/auth/logout', {});
  } finally {
    useSessao.getState().limparSessao();
  }
}

/**
 * Restaura a sessão ao abrir o app: tenta /api/auth/refresh pelo cookie e, com o
 * novo access token, carrega /api/auth/me. Marca anônimo se não houver sessão.
 */
export async function restaurarSessao(): Promise<void> {
  const sessao = useSessao.getState();
  try {
    const resp = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    if (!resp.ok) {
      sessao.marcarAnonimo();
      return;
    }
    const dados = (await resp.json()) as LoginSaida;
    sessao.definirSessao(paraUsuario(dados.usuario), dados.access_token);
  } catch {
    sessao.marcarAnonimo();
  }
}

/** Troca de senha do usuário autenticado (PUT /api/auth/senha). */
export async function trocarSenha(senhaAtual: string, senhaNova: string): Promise<void> {
  const { error } = await api.PUT('/api/auth/senha', {
    body: { senha_atual: senhaAtual, senha_nova: senhaNova },
  });
  if (error) lancar(error);
}

/** Solicita o e-mail de redefinição (FA02). Resposta genérica (não revela a conta). */
export async function esqueciSenha(email: string): Promise<string> {
  const { data, error } = await api.POST('/api/auth/esqueci-senha', { body: { email } });
  if (error || !data) lancar(error);
  return data.mensagem;
}

/** Redefine a senha com o token recebido por e-mail. */
export async function redefinirSenha(token: string, senhaNova: string): Promise<string> {
  const { data, error } = await api.POST('/api/auth/redefinir-senha', {
    body: { token, senha_nova: senhaNova },
  });
  if (error || !data) lancar(error);
  return data.mensagem;
}
