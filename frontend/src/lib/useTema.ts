import { useEffect } from 'react';

import { resolverTema, useTema } from '@/stores/tema';

/**
 * Aplica o tema efetivo ao `data-theme` do <html> e, quando a preferência é
 * 'sistema', acompanha as mudanças do `prefers-color-scheme` em tempo real.
 * Chamado uma vez no topo da árvore (App).
 */
export function useAplicarTema(): void {
  const preferencia = useTema((e) => e.preferencia);

  useEffect(() => {
    const raiz = document.documentElement;
    const aplicar = () => {
      raiz.setAttribute('data-theme', resolverTema(preferencia));
    };
    aplicar();

    if (preferencia !== 'sistema') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', aplicar);
    return () => mq.removeEventListener('change', aplicar);
  }, [preferencia]);
}
