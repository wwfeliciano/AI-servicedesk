import type { ReactNode } from 'react';

interface Props {
  eyebrow?: string;
  titulo: string;
  descricao?: string;
  /** Fase em que a tela ganha conteúdo real (ex.: "F1", "F2"). */
  fase?: string;
  children?: ReactNode;
}

/**
 * Esqueleto de página da F0.5: as telas existem e são roteáveis, mas o conteúdo
 * real entra nas fases seguintes. Mantém o cabeçalho na identidade nova.
 */
export function PaginaVazia({ eyebrow, titulo, descricao, fase, children }: Props) {
  return (
    <section>
      <header className="mb-6">
        {eyebrow && (
          <p className="text-[10px] font-semibold tracking-[0.16em] text-brand-500 uppercase">
            {eyebrow}
          </p>
        )}
        <h1 className="mt-1 text-2xl text-ink">{titulo}</h1>
        {descricao && <p className="mt-1 text-sm text-secondary">{descricao}</p>}
      </header>
      {children ?? (
        <div className="grid place-items-center rounded-card border border-dashed border-line-2 bg-surface px-6 py-16 text-center">
          <p className="text-sm text-muted">
            Tela em construção{fase ? ` — conteúdo na fase ${fase}` : ''}.
          </p>
        </div>
      )}
    </section>
  );
}
