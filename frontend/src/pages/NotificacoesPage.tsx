import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bell, CheckCheck, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import {
  listarNotificacoes,
  marcarLida,
  marcarTodasLidas,
  type NotificacaoSaida,
} from '@/api/notificacoes';
import { cx, tempoRelativoCurto } from '@/lib/formato';

export function NotificacoesPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();

  const lista = useQuery({
    queryKey: ['notificacoes'],
    queryFn: () => listarNotificacoes(1, 50),
    placeholderData: keepPreviousData,
  });

  function invalidar() {
    void cliente.invalidateQueries({ queryKey: ['notificacoes'] });
    void cliente.invalidateQueries({ queryKey: ['notificacoes', 'contagem'] });
  }

  const marcarUma = useMutation({
    mutationFn: marcarLida,
    onSuccess: invalidar,
  });
  const marcarTodas = useMutation({
    mutationFn: marcarTodasLidas,
    onSuccess: invalidar,
  });

  async function abrir(n: NotificacaoSaida) {
    if (!n.lida) await marcarUma.mutateAsync(n.id_notificacao).catch(() => undefined);
    if (n.id_chamado) navegar(`/chamados/${n.id_chamado}`);
  }

  const itens = lista.data?.items ?? [];
  const naoLidas = lista.data?.nao_lidas ?? 0;

  return (
    <section>
      <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.16em] text-brand-500 uppercase">
            Avisos
          </p>
          <h1 className="mt-1 text-2xl text-ink">Notificações</h1>
          <p className="mt-1 text-sm text-secondary">
            {naoLidas > 0 ? `${naoLidas} não lida${naoLidas > 1 ? 's' : ''}` : 'Tudo em dia.'}
          </p>
        </div>
        {naoLidas > 0 && (
          <button
            type="button"
            onClick={() => marcarTodas.mutate()}
            disabled={marcarTodas.isPending}
            className="flex items-center gap-2 rounded-controle border border-line-2 px-3.5 py-2 text-sm font-medium text-ink disabled:opacity-60"
          >
            <CheckCheck aria-hidden className="size-4 text-brand" /> Marcar todas como lidas
          </button>
        )}
      </header>

      {lista.isLoading ? (
        <div className="grid place-items-center rounded-card border border-line bg-surface py-16 text-muted">
          <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
        </div>
      ) : itens.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {itens.map((n) => (
            <li key={n.id_notificacao}>
              <button
                type="button"
                onClick={() => void abrir(n)}
                className={cx(
                  'flex w-full items-start gap-3 rounded-card border p-4 text-left transition hover:border-brand-500',
                  n.lida ? 'border-line bg-surface' : 'border-brand-500/40 bg-brand-soft',
                )}
              >
                <span
                  className={cx(
                    'mt-0.5 grid size-8 flex-none place-items-center rounded-lg',
                    n.tipo === 'CHAMADO_URGENTE'
                      ? 'bg-danger-soft text-danger-ink'
                      : 'bg-brand-soft text-brand-soft-ink',
                  )}
                >
                  <Bell aria-hidden className="size-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-ink">{n.titulo}</span>
                    {!n.lida && <span className="size-2 rounded-full bg-brand" aria-label="não lida" />}
                  </span>
                  <span className="mt-0.5 block text-sm text-secondary">{n.mensagem}</span>
                  <span className="mt-1 block text-xs text-muted">
                    {tempoRelativoCurto(n.data_criacao)}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div className="grid place-items-center gap-2 rounded-card border border-dashed border-line-2 bg-surface py-16 text-center">
          <Bell aria-hidden className="size-6 text-muted" />
          <p className="text-sm text-muted">Você não tem notificações.</p>
        </div>
      )}
    </section>
  );
}
