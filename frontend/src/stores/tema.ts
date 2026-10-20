import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Preferência de tema. 'sistema' segue o `prefers-color-scheme` do SO. */
export type PreferenciaTema = 'claro' | 'escuro' | 'sistema';

/** Tema efetivo aplicado ao `data-theme` do documento. */
export type TemaEfetivo = 'light' | 'dark';

interface EstadoTema {
  preferencia: PreferenciaTema;
  definirPreferencia: (p: PreferenciaTema) => void;
  alternar: () => void;
}

/**
 * Tema do app (seção 8.2: claro e escuro). Persistido em localStorage para a
 * escolha sobreviver ao recarregar. O hook `useAplicarTema` reflete isso no
 * atributo `data-theme` do <html>; os tokens CSS trocam por tema.
 */
export const useTema = create<EstadoTema>()(
  persist(
    (set, get) => ({
      preferencia: 'sistema',
      definirPreferencia: (preferencia) => set({ preferencia }),
      alternar: () => {
        // Alterna com base no que está visível agora (resolve 'sistema').
        const atual = resolverTema(get().preferencia);
        set({ preferencia: atual === 'dark' ? 'claro' : 'escuro' });
      },
    }),
    { name: 'mentory-tema' },
  ),
);

/** Resolve a preferência para o tema efetivo, consultando o SO quando 'sistema'. */
export function resolverTema(preferencia: PreferenciaTema): TemaEfetivo {
  if (preferencia === 'claro') return 'light';
  if (preferencia === 'escuro') return 'dark';
  const prefereEscuro =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefereEscuro ? 'dark' : 'light';
}
