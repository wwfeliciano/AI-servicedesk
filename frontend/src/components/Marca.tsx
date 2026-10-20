import { MessageSquareText } from 'lucide-react';

import { cx } from '@/lib/formato';

interface Props {
  /** Mostra o subtítulo "Help Desk" abaixo do nome. */
  comSub?: boolean;
  /** Variante para fundo escuro (painel do login na cor da marca). */
  invertido?: boolean;
}

/** Logotipo do Mentory: quadrado teal + nome, com o ponto do esboço ("Mentory."). */
export function Marca({ comSub = true, invertido = false }: Props) {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className={cx(
          'grid size-9 place-items-center rounded-[11px]',
          invertido ? 'bg-white/15 text-white' : 'bg-brand text-white',
        )}
      >
        <MessageSquareText aria-hidden className="size-5" />
      </span>
      <span className="leading-tight">
        <span
          className={cx(
            'block text-lg font-semibold tracking-tight',
            invertido ? 'text-white' : 'text-ink',
          )}
        >
          Mentory<span className="text-brand-500">.</span>
        </span>
        {comSub && (
          <span className={cx('block text-xs', invertido ? 'text-white/70' : 'text-muted')}>
            Help Desk
          </span>
        )}
      </span>
    </div>
  );
}
