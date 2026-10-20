import { create } from 'zustand';

import type { Usuario } from '@/types/dominio';

/**
 * Sessão em memória (seção 8.1): o access token nunca vai para o localStorage.
 * A restauração ao abrir o app usa o cookie HttpOnly de refresh (/api/auth/refresh).
 *
 * `estado` acompanha a restauração inicial:
 *  - 'verificando': ainda tentando restaurar (mostra tela de carregamento);
 *  - 'autenticado' / 'anonimo': resultado conhecido.
 */
export type EstadoAutenticacao = 'verificando' | 'autenticado' | 'anonimo';

interface EstadoSessao {
  usuario: Usuario | null;
  accessToken: string | null;
  estado: EstadoAutenticacao;
  definirSessao: (usuario: Usuario, accessToken: string) => void;
  definirAccessToken: (accessToken: string) => void;
  limparSessao: () => void;
  marcarAnonimo: () => void;
}

export const useSessao = create<EstadoSessao>((set) => ({
  usuario: null,
  accessToken: null,
  estado: 'verificando',
  definirSessao: (usuario, accessToken) =>
    set({ usuario, accessToken, estado: 'autenticado' }),
  definirAccessToken: (accessToken) => set({ accessToken }),
  limparSessao: () => set({ usuario: null, accessToken: null, estado: 'anonimo' }),
  marcarAnonimo: () => set({ usuario: null, accessToken: null, estado: 'anonimo' }),
}));

/** Lê o access token atual fora de componentes (usado pelo cliente HTTP). */
export function obterAccessToken(): string | null {
  return useSessao.getState().accessToken;
}
