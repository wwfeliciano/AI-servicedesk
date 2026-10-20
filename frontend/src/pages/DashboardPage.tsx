import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  CircleDot,
  Clock,
  FileText,
  Gauge,
  Inbox,
  Loader2,
  Plus,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { listarChamados, obterResumo } from '@/api/chamados';
import { obterSlaDoMes } from '@/api/sla';
import { CardChamado } from '@/components/CardChamado';
import { CardIndicador } from '@/components/CardIndicador';
import { primeiroNome, saudacao, tempoRelativoCurto } from '@/lib/formato';
import { useSessao } from '@/stores/sessao';
import type { Severidade, StatusChamado } from '@/types/dominio';

export function DashboardPage() {
  const navegar = useNavigate();
  const usuario = useSessao((e) => e.usuario);
  const nome = usuario ? primeiroNome(usuario.nome) : '';

  const resumo = useQuery({ queryKey: ['resumo'], queryFn: obterResumo });
  const recentes = useQuery({
    queryKey: ['chamados', 'recentes'],
    queryFn: () => listarChamados({ page: 1, page_size: 5 }),
  });
  const sla = useQuery({ queryKey: ['sla', 'mes'], queryFn: obterSlaDoMes });

  const urgentes = resumo.data?.urgentes ?? 0;

  return (
    <section>
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.16em] text-brand-500 uppercase">
            Seu portal de suporte
          </p>
          <h1 className="mt-1 text-2xl text-ink">
            {saudacao()}, {nome}
          </h1>
          <p className="mt-1 text-sm text-secondary">Seu painel de suporte.</p>
        </div>
        <button
          type="button"
          onClick={() => navegar('/chamados/novo')}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          <Plus aria-hidden className="size-4" /> Novo Chamado
        </button>
      </header>

      {/* Alerta de urgentes */}
      {urgentes > 0 && (
        <div className="mb-6 flex items-center gap-3 rounded-card border border-danger/30 bg-danger-soft p-4">
          <span className="grid size-8 flex-none place-items-center rounded-lg bg-danger text-white">
            <AlertTriangle aria-hidden className="size-4" />
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-ink">
              {urgentes} chamado{urgentes > 1 ? 's' : ''} urgente{urgentes > 1 ? 's' : ''} aguardando
              atenção
            </p>
            <p className="text-xs text-secondary">
              Esses chamados têm prioridade máxima e são atendidos primeiro.
            </p>
          </div>
          <Link
            to="/chamados?grupo=abertos"
            className="ml-auto flex-none rounded-controle bg-danger px-3.5 py-2 text-xs font-semibold text-white"
          >
            Ver agora
          </Link>
        </div>
      )}

      {/* Indicadores */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <CardIndicador
          rotulo="Abertos"
          valor={resumo.data?.abertos ?? '—'}
          legenda="aguardando triagem"
          icone={Inbox}
          etiqueta="bg-info-soft text-info-ink"
        />
        <CardIndicador
          rotulo="Em andamento"
          valor={resumo.data?.em_andamento ?? '—'}
          legenda="atribuídos"
          icone={Clock}
          etiqueta="bg-warning-soft text-warning-ink"
        />
        <CardIndicador
          rotulo="Resolvidos"
          valor={resumo.data?.resolvidos ?? '—'}
          legenda="concluídos"
          icone={CheckCircle2}
          etiqueta="bg-success-soft text-success-ink"
        />
        <CardIndicador
          rotulo="Urgentes"
          valor={resumo.data?.urgentes ?? '—'}
          legenda="severidade crítica"
          icone={CircleDot}
          etiqueta="bg-danger-soft text-danger-ink"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        {/* Chamados recentes */}
        <section className="rounded-card border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-5 py-4">
            <h2 className="text-sm font-semibold text-ink">Chamados recentes</h2>
            <Link to="/chamados" className="text-xs font-medium text-brand">
              Ver todos →
            </Link>
          </div>
          <div className="p-4">
            {recentes.isLoading ? (
              <div className="grid place-items-center py-10 text-muted">
                <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
              </div>
            ) : recentes.data && recentes.data.items.length > 0 ? (
              <div className="flex flex-col gap-3">
                {recentes.data.items.map((c) => (
                  <Link key={c.id_chamado} to={`/chamados/${c.id_chamado}`}>
                    <CardChamado
                      chamado={{
                        protocolo: c.protocolo,
                        titulo: c.titulo,
                        categoria: c.categoria.nome_categoria,
                        ...(c.categoria.icone ? { categoriaIcone: c.categoria.icone } : {}),
                        severidade: c.severidade as Severidade,
                        status: c.status_chamado as StatusChamado,
                        ...(c.tecnico_responsavel
                          ? { responsavel: c.tecnico_responsavel.nome }
                          : {}),
                      }}
                      rodape={
                        <span className="flex items-center gap-2">
                          {tempoRelativoCurto(c.data_criacao)}
                          {c.tecnico_responsavel && <>· → {c.tecnico_responsavel.nome}</>}
                        </span>
                      }
                    />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="py-10 text-center text-sm text-muted">
                Você ainda não tem chamados. Que tal abrir o primeiro?
              </p>
            )}
          </div>
        </section>

        {/* Ações rápidas */}
        <aside className="flex flex-col gap-3">
          <div className="rounded-card border border-line bg-surface p-2.5">
            <p className="px-2 py-2 text-sm font-semibold text-ink">Ações rápidas</p>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => navegar('/chamados/novo')}
                className="flex items-center gap-2.5 rounded-controle bg-brand px-3.5 py-3 text-left text-sm font-semibold text-white"
              >
                <Plus aria-hidden className="size-4" /> Abrir novo chamado
              </button>
              <Link
                to="/base-conhecimento"
                className="flex items-center gap-2.5 rounded-controle border border-line bg-surface-2 px-3.5 py-3 text-sm font-semibold text-ink"
              >
                <BookOpen aria-hidden className="size-4 text-brand" /> Base de conhecimento
              </Link>
              <Link
                to="/chamados"
                className="flex items-center gap-2.5 rounded-controle border border-line bg-surface-2 px-3.5 py-3 text-sm font-semibold text-ink"
              >
                <FileText aria-hidden className="size-4 text-brand" /> Ver histórico
              </Link>
            </div>
          </div>

          {/* SLA do mês (F7.2) */}
          <div className="rounded-card border border-line bg-surface p-4">
            <p className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Gauge aria-hidden className="size-4 text-brand" /> SLA do mês
            </p>
            {sla.isLoading ? (
              <div className="grid place-items-center py-4 text-muted">
                <Loader2 aria-label="Carregando" className="size-4 animate-spin text-brand" />
              </div>
            ) : sla.isError ? (
              <p className="mt-2 text-xs text-muted">Não foi possível carregar o SLA.</p>
            ) : sla.data && sla.data.total > 0 ? (
              <>
                <p className="mt-2 text-3xl font-semibold tracking-tight text-brand">
                  {sla.data.percentual.toLocaleString('pt-BR')}%
                </p>
                <p className="mt-1 text-xs text-secondary">
                  {sla.data.no_prazo} de {sla.data.total} chamado
                  {sla.data.total === 1 ? '' : 's'} concluído
                  {sla.data.total === 1 ? '' : 's'} no prazo
                </p>
                <div
                  className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2"
                  role="progressbar"
                  aria-valuenow={Math.round(sla.data.percentual)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="h-full rounded-full bg-success"
                    style={{ width: `${sla.data.percentual}%` }}
                  />
                </div>
              </>
            ) : (
              <p className="mt-2 text-xs text-muted">
                Ainda não há chamados concluídos neste mês.
              </p>
            )}
          </div>
        </aside>
      </div>

      {resumo.isError && (
        <p className="mt-4 text-sm text-danger-ink">Não foi possível carregar os indicadores.</p>
      )}
    </section>
  );
}
