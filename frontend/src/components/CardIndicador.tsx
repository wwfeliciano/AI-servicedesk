import type { LucideIcon } from 'lucide-react';

import { cx } from '@/lib/formato';

interface Props {
  rotulo: string;
  valor: number | string;
  legenda?: string;
  icone?: LucideIcon;
  /** Classe da etiqueta semântica (ex.: 'bg-info-soft text-info-ink'). */
  etiqueta?: string;
}

/** Card de indicador do Dashboard (Abertos, Em andamento, Resolvidos, Urgentes). */
export function CardIndicador({
  rotulo,
  valor,
  legenda = 'chamados',
  icone: Icone,
  etiqueta = 'bg-neutral-soft text-neutral-ink',
}: Props) {
  return (
    <div className="rounded-card border border-line bg-surface p-5 shadow-card">
      <div className="mb-3 flex items-center justify-between">
        {Icone ? (
          <span className="grid size-8 place-items-center rounded-controle bg-surface-2 text-secondary">
            <Icone aria-hidden className="size-4" />
          </span>
        ) : (
          <span />
        )}
        <span className={cx('rounded-full px-2.5 py-0.5 text-xs font-semibold', etiqueta)}>
          {rotulo}
        </span>
      </div>
      <p className="text-3xl font-semibold tracking-tight text-ink">{valor}</p>
      <p className="mt-0.5 text-xs text-muted">{legenda}</p>
    </div>
  );
}
