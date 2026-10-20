import { cx } from '@/lib/formato';

interface Props {
  nome: string;
  /** Emoji vindo de categorias.icone (seção 8.2). */
  icone?: string;
  ativo?: boolean;
}

/** Chip de categoria (neutro; filtro ativo usa a cor da marca suave). */
export function CategoriaChip({ nome, icone, ativo = false }: Props) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-md px-2.5 py-0.5 text-xs font-semibold',
        ativo ? 'bg-brand-soft text-brand-soft-ink' : 'bg-neutral-soft text-neutral-ink',
      )}
    >
      {icone && <span aria-hidden>{icone}</span>}
      {nome}
    </span>
  );
}
