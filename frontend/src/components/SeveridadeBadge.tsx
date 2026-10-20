import { Siren } from 'lucide-react';

import type { Severidade } from '@/types/dominio';
import { cx } from '@/lib/formato';

const ROTULOS: Record<Severidade, string> = {
  BAIXA: 'Baixa',
  MEDIA: 'Média',
  ALTA: 'Alta',
  CRITICO: 'Urgente',
};

/** Cores por severidade (seção 6.1 na paleta Foundations). */
const ESTILOS: Record<Severidade, string> = {
  BAIXA: 'bg-success-soft text-success-ink',
  MEDIA: 'bg-info-soft text-info-ink',
  ALTA: 'bg-warning-soft text-warning-ink',
  CRITICO: 'bg-danger-soft text-danger-ink',
};

interface Props {
  severidade: Severidade;
}

/** Badge de severidade. CRITICO ("Urgente") leva a sirene do protótipo. */
export function SeveridadeBadge({ severidade }: Props) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold',
        ESTILOS[severidade],
      )}
    >
      {severidade === 'CRITICO' && <Siren aria-hidden className="size-3" />}
      {ROTULOS[severidade]}
    </span>
  );
}
