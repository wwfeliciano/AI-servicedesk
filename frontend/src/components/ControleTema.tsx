import { Moon, Sun } from 'lucide-react';

import { resolverTema, useTema } from '@/stores/tema';

/**
 * Botão de alternância de tema (claro/escuro). Mostra o ícone do tema para o qual
 * vai trocar. A preferência fica persistida (store `useTema`).
 */
export function ControleTema() {
  const preferencia = useTema((e) => e.preferencia);
  const alternar = useTema((e) => e.alternar);
  const efetivo = resolverTema(preferencia);
  const vaiParaEscuro = efetivo === 'light';

  return (
    <button
      type="button"
      onClick={alternar}
      aria-label={vaiParaEscuro ? 'Ativar tema escuro' : 'Ativar tema claro'}
      title={vaiParaEscuro ? 'Tema escuro' : 'Tema claro'}
      className="grid size-9 place-items-center rounded-controle border border-line text-secondary transition hover:border-brand-500 hover:text-brand"
    >
      {vaiParaEscuro ? <Moon aria-hidden className="size-4" /> : <Sun aria-hidden className="size-4" />}
    </button>
  );
}
