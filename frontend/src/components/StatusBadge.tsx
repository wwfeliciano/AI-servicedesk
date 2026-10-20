import type { StatusChamado } from '@/types/dominio';
import { cx } from '@/lib/formato';

/** Rótulos exibidos (PT-BR, seção 6.1). NOVO/PENDENTE aparecem como "Aberto". */
const ROTULOS: Record<StatusChamado, string> = {
  NOVO: 'Aberto',
  PENDENTE: 'Aberto',
  ATRIBUIDO: 'Em andamento',
  CONCLUIDO: 'Resolvido',
  FECHADO: 'Encerrado',
};

/** Cores por estado (seção 6.1 na paleta Foundations). */
const ESTILOS: Record<StatusChamado, string> = {
  NOVO: 'bg-info-soft text-info-ink',
  PENDENTE: 'bg-info-soft text-info-ink',
  ATRIBUIDO: 'bg-warning-soft text-warning-ink',
  CONCLUIDO: 'bg-success-soft text-success-ink',
  FECHADO: 'bg-neutral-soft text-neutral-ink',
};

interface Props {
  status: StatusChamado;
}

/** Badge de status. Sempre com texto, nunca só cor (acessibilidade, seção 8.2). */
export function StatusBadge({ status }: Props) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold',
        ESTILOS[status],
      )}
    >
      <span aria-hidden className="size-1.5 rounded-full bg-current" />
      {ROTULOS[status]}
    </span>
  );
}
