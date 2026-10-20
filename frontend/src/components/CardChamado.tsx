import type { ReactNode } from 'react';

import type { Severidade, StatusChamado } from '@/types/dominio';
import { CategoriaChip } from '@/components/CategoriaChip';
import { SeveridadeBadge } from '@/components/SeveridadeBadge';
import { StatusBadge } from '@/components/StatusBadge';

export interface ResumoChamado {
  protocolo: string;
  titulo: string;
  descricao?: string;
  categoria: string;
  categoriaIcone?: string;
  severidade: Severidade;
  status: StatusChamado;
  abertoEm?: string;
  atualizadoEm?: string;
  responsavel?: string;
  mensagens?: number;
}

interface Props {
  chamado: ResumoChamado;
  rodape?: ReactNode;
}

/** Card de chamado da lista "Meus Chamados" (seção 8.4). */
export function CardChamado({ chamado, rodape }: Props) {
  return (
    <article className="rounded-card border border-line bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2">
            <span className="font-mono text-xs text-muted">{chamado.protocolo}</span>
            <CategoriaChip
              nome={chamado.categoria}
              {...(chamado.categoriaIcone ? { icone: chamado.categoriaIcone } : {})}
            />
            {chamado.severidade === 'CRITICO' && <SeveridadeBadge severidade="CRITICO" />}
          </div>
          <h3 className="truncate text-base font-semibold text-ink">{chamado.titulo}</h3>
          {chamado.descricao && (
            <p className="mt-1 line-clamp-2 text-sm text-secondary">{chamado.descricao}</p>
          )}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <StatusBadge status={chamado.status} />
          <SeveridadeBadge severidade={chamado.severidade} />
        </div>
      </div>
      {rodape && (
        <div className="mt-3 border-t border-line pt-2.5 text-xs text-muted">{rodape}</div>
      )}
    </article>
  );
}
