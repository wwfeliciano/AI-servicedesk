import type { ReactNode } from 'react';

import { cx } from '@/lib/formato';

interface Props {
  titulo: string;
  descricao?: string;
  icone?: ReactNode;
  selecionado: boolean;
  onSelecionar: () => void;
}

/** Card de opção com seleção por rádio (categoria/severidade do wizard). */
export function OpcaoCard({ titulo, descricao, icone, selecionado, onSelecionar }: Props) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selecionado}
      onClick={onSelecionar}
      className={cx(
        'flex w-full flex-col items-start gap-1 rounded-card border p-4 text-left transition',
        selecionado
          ? 'border-brand bg-brand-soft'
          : 'border-line bg-surface hover:border-brand-500/50',
      )}
    >
      {icone && <span className="text-2xl">{icone}</span>}
      <span className="font-semibold text-ink">{titulo}</span>
      {descricao && <span className="text-sm text-secondary">{descricao}</span>}
    </button>
  );
}
