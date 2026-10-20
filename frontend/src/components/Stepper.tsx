import { Check } from 'lucide-react';

import { cx } from '@/lib/formato';

interface Props {
  etapas: string[];
  /** Índice (base 0) da etapa ativa. */
  atual: number;
}

/**
 * Stepper do wizard de novo chamado (seção 8.4): etapa concluída fica verde com ✓;
 * a ativa usa a cor da marca; as futuras ficam neutras.
 */
export function Stepper({ etapas, atual }: Props) {
  return (
    <ol className="flex items-center gap-2">
      {etapas.map((etapa, i) => {
        const concluida = i < atual;
        const ativa = i === atual;
        return (
          <li key={etapa} className="flex flex-1 items-center gap-2">
            <span
              className={cx(
                'flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold',
                concluida && 'bg-success text-white',
                ativa && 'bg-brand text-white',
                !concluida && !ativa && 'bg-neutral-soft text-muted',
              )}
              aria-current={ativa ? 'step' : undefined}
            >
              {concluida ? <Check aria-hidden className="size-4" /> : i + 1}
            </span>
            <span className={cx('text-sm', ativa ? 'font-semibold text-brand' : 'text-muted')}>
              {etapa}
            </span>
            {i < etapas.length - 1 && <span className="mx-1 h-px flex-1 bg-line" aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}
