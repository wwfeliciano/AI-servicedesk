import { useState } from 'react';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, RefreshCw, Smartphone } from 'lucide-react';
import { toast } from 'sonner';

import {
  listarOutbox,
  obterSessaoWhatsapp,
  reenviarOutbox,
  type FiltroOutbox,
} from '@/api/integracoes';
import { ehErroAPI } from '@/lib/erros';
import { cx, tempoRelativoCurto } from '@/lib/formato';

const STATUS: { chave: FiltroOutbox['status'] | ''; rotulo: string }[] = [
  { chave: '', rotulo: 'Todos' },
  { chave: 'PENDENTE', rotulo: 'Pendentes' },
  { chave: 'PROCESSANDO', rotulo: 'Processando' },
  { chave: 'ENVIADO', rotulo: 'Enviados' },
  { chave: 'FALHOU', rotulo: 'Falhas' },
];

const COR_SESSAO: Record<string, string> = {
  WORKING: 'bg-success-soft text-success-ink',
  SCAN_QR_CODE: 'bg-warning-soft text-warning-ink',
  FAILED: 'bg-danger-soft text-danger-ink',
  STOPPED: 'bg-danger-soft text-danger-ink',
};

export function AdminIntegracoesPage() {
  const cliente = useQueryClient();
  const [filtro, setFiltro] = useState<FiltroOutbox['status'] | ''>('');

  const sessao = useQuery({
    queryKey: ['integracoes', 'sessao'],
    queryFn: obterSessaoWhatsapp,
    refetchInterval: 15000,
  });
  const outbox = useQuery({
    queryKey: ['integracoes', 'outbox', filtro],
    queryFn: () => listarOutbox(filtro ? { status: filtro } : {}),
    placeholderData: keepPreviousData,
  });

  const mReenviar = useMutation({
    mutationFn: reenviarOutbox,
    onSuccess: () => {
      toast.success('Evento reenfileirado.');
      void cliente.invalidateQueries({ queryKey: ['integracoes', 'outbox'] });
    },
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível reenviar.'),
  });

  const contadores = outbox.data?.contadores ?? {};
  const statusSessao = sessao.data?.status ?? 'DESCONHECIDO';

  return (
    <section>
      <header className="mb-5">
        <h1 className="text-2xl text-ink">Integrações</h1>
        <p className="mt-1 text-sm text-secondary">
          Sessão do WhatsApp e fila de envios externos (e-mail e WhatsApp).
        </p>
      </header>

      {/* Sessão do WhatsApp */}
      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface p-4">
        <Smartphone aria-hidden className="size-5 text-brand" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink">Sessão do WhatsApp</p>
          <p className="text-xs text-secondary">
            {sessao.data?.atualizado_em
              ? `Atualizada ${tempoRelativoCurto(sessao.data.atualizado_em)}`
              : 'Sem informação de sessão ainda.'}
            {sessao.data?.detalhe ? ` · ${sessao.data.detalhe}` : ''}
          </p>
        </div>
        <span
          className={cx(
            'rounded-full px-3 py-1 text-xs font-semibold',
            COR_SESSAO[statusSessao] ?? 'bg-surface-2 text-muted',
          )}
        >
          {statusSessao}
        </span>
      </div>

      {/* Filtro por status (com contadores) */}
      <div className="mb-3 flex flex-wrap gap-2">
        {STATUS.map((s) => {
          const ativo = filtro === s.chave;
          const n = s.chave ? (contadores[s.chave] ?? 0) : undefined;
          return (
            <button
              key={s.rotulo}
              type="button"
              onClick={() => setFiltro(s.chave)}
              className={cx(
                'flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-semibold transition',
                ativo ? 'bg-brand text-white' : 'border border-line bg-surface text-secondary',
              )}
            >
              {s.rotulo}
              {n !== undefined && (
                <span
                  className={cx(
                    'rounded-full px-1.5 text-[10px]',
                    ativo ? 'bg-white/20' : 'bg-surface-2 text-muted',
                  )}
                >
                  {n}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Fila do outbox */}
      {outbox.isLoading ? (
        <div className="grid place-items-center rounded-card border border-line bg-surface py-16 text-muted">
          <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
        </div>
      ) : outbox.data && outbox.data.items.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {outbox.data.items.map((e) => (
            <li
              key={e.id_evento}
              className="flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface px-4 py-3 text-sm"
            >
              <span className="font-mono text-xs text-muted">#{e.id_evento}</span>
              <span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs font-semibold text-secondary">
                {e.canal}
              </span>
              <span className="min-w-0 flex-1 truncate text-ink">
                {e.tipo} → {e.destino}
              </span>
              {e.tentativas > 0 && (
                <span className="text-xs text-muted">{e.tentativas} tent.</span>
              )}
              <span
                className={cx(
                  'rounded-full px-2.5 py-0.5 text-xs font-semibold',
                  e.status === 'ENVIADO'
                    ? 'bg-success-soft text-success-ink'
                    : e.status === 'FALHOU'
                      ? 'bg-danger-soft text-danger-ink'
                      : 'bg-surface-2 text-muted',
                )}
              >
                {e.status}
              </span>
              {e.status === 'FALHOU' && (
                <button
                  type="button"
                  onClick={() => mReenviar.mutate(e.id_evento)}
                  disabled={mReenviar.isPending}
                  className="flex items-center gap-1.5 rounded-controle border border-line-2 px-3 py-1.5 text-xs font-semibold text-ink disabled:opacity-60"
                >
                  <RefreshCw aria-hidden className="size-3.5" /> Reenviar
                </button>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="grid place-items-center rounded-card border border-dashed border-line-2 bg-surface py-16 text-center text-sm text-muted">
          Nenhum evento nesse filtro.
        </div>
      )}
    </section>
  );
}
