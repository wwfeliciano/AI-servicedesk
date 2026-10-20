import { useEffect, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { Loader2, Plus, Search } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { listarCategorias, listarChamados, type FiltroChamados } from '@/api/chamados';
import { CardChamado } from '@/components/CardChamado';
import { cx, dataCurta } from '@/lib/formato';
import { useDebounce } from '@/lib/useDebounce';
import { useSessao } from '@/stores/sessao';
import type { GrupoStatus, Severidade, StatusChamado } from '@/types/dominio';

const PAGE_SIZE = 10;
const ABAS: { chave: '' | GrupoStatus; rotulo: string; contador: keyof Contadores }[] = [
  { chave: '', rotulo: 'Todos', contador: 'todos' },
  { chave: 'abertos', rotulo: 'Abertos', contador: 'abertos' },
  { chave: 'em_andamento', rotulo: 'Em andamento', contador: 'em_andamento' },
  { chave: 'resolvidos', rotulo: 'Resolvidos', contador: 'resolvidos' },
  { chave: 'encerrados', rotulo: 'Encerrados', contador: 'encerrados' },
];

interface Contadores {
  todos: number;
  abertos: number;
  em_andamento: number;
  resolvidos: number;
  encerrados: number;
}

export function ChamadosPage() {
  const navegar = useNavigate();
  const [params, setParams] = useSearchParams();
  const usuario = useSessao((e) => e.usuario);
  const ehTecnico = usuario?.tipo_perfil === 'ANALISTA' || usuario?.tipo_perfil === 'ADMIN';

  // Estado derivado da URL (para o botão Voltar do navegador funcionar — seção 8.4).
  const qUrl = params.get('q') ?? '';
  const grupo = (params.get('grupo') ?? '') as '' | GrupoStatus;
  const idCategoriaUrl = params.get('categoria');
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1);

  const [busca, setBusca] = useState(qUrl);
  const buscaDebounced = useDebounce(busca, 300);

  // Reflete a busca (debounced) na URL, resetando a página.
  useEffect(() => {
    if (buscaDebounced === qUrl) return;
    const p = new URLSearchParams(params);
    if (buscaDebounced) p.set('q', buscaDebounced);
    else p.delete('q');
    p.delete('page');
    setParams(p, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buscaDebounced]);

  const categorias = useQuery({ queryKey: ['categorias'], queryFn: listarCategorias });

  const filtro: FiltroChamados = {
    page,
    page_size: PAGE_SIZE,
    ...(qUrl ? { q: qUrl } : {}),
    ...(grupo ? { grupo } : {}),
    ...(idCategoriaUrl ? { id_categoria: Number(idCategoriaUrl) } : {}),
  };

  const lista = useQuery({
    queryKey: ['chamados', filtro],
    queryFn: () => listarChamados(filtro),
    placeholderData: keepPreviousData,
  });

  const contadores: Contadores = lista.data?.contadores ?? {
    todos: 0,
    abertos: 0,
    em_andamento: 0,
    resolvidos: 0,
    encerrados: 0,
  };
  const totalPaginas = lista.data ? Math.max(1, Math.ceil(lista.data.total / PAGE_SIZE)) : 1;

  function definirParam(mudancas: Record<string, string | null>) {
    const p = new URLSearchParams(params);
    for (const [k, v] of Object.entries(mudancas)) {
      if (v) p.set(k, v);
      else p.delete(k);
    }
    setParams(p);
  }

  return (
    <section>
      <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl text-ink">{ehTecnico ? 'Chamados' : 'Meus Chamados'}</h1>
          <p className="mt-1 text-sm text-secondary">
            {lista.data ? `${lista.data.total} chamado${lista.data.total === 1 ? '' : 's'} no total` : '—'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => navegar('/chamados/novo')}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          <Plus aria-hidden className="size-4" /> Novo
        </button>
      </header>

      {/* Busca */}
      <div className="mb-4 flex items-center gap-2 rounded-controle border border-line-2 bg-surface px-3">
        <Search aria-hidden className="size-4 text-muted" />
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por título ou ID do chamado…"
          aria-label="Buscar chamados"
          className="w-full bg-transparent py-2.5 text-sm text-ink placeholder:text-muted focus:outline-none"
        />
      </div>

      {/* Abas com contadores */}
      <div className="mb-3 flex flex-wrap gap-2">
        {ABAS.map((aba) => {
          const ativa = grupo === aba.chave;
          return (
            <button
              key={aba.rotulo}
              type="button"
              onClick={() => definirParam({ grupo: aba.chave || null, page: null })}
              className={cx(
                'flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-semibold transition',
                ativa ? 'bg-brand text-white' : 'border border-line bg-surface text-secondary',
              )}
            >
              {aba.rotulo}
              <span
                className={cx(
                  'rounded-full px-1.5 text-[10px]',
                  ativa ? 'bg-white/20' : 'bg-surface-2 text-muted',
                )}
              >
                {contadores[aba.contador]}
              </span>
            </button>
          );
        })}
      </div>

      {/* Chips de categoria */}
      <div className="mb-5 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => definirParam({ categoria: null, page: null })}
          className={cx(
            'rounded-md px-2.5 py-1 text-xs font-semibold',
            !idCategoriaUrl ? 'bg-brand-soft text-brand-soft-ink' : 'bg-surface-2 text-muted',
          )}
        >
          Todas as categorias
        </button>
        {(categorias.data ?? []).map((c) => (
          <button
            key={c.id_categoria}
            type="button"
            onClick={() => definirParam({ categoria: String(c.id_categoria), page: null })}
            className={cx(
              'rounded-md px-2.5 py-1 text-xs font-semibold',
              idCategoriaUrl === String(c.id_categoria)
                ? 'bg-brand-soft text-brand-soft-ink'
                : 'bg-surface-2 text-muted',
            )}
          >
            {c.icone ? `${c.icone} ` : ''}
            {c.nome_categoria}
          </button>
        ))}
      </div>

      {/* Lista */}
      {lista.isLoading ? (
        <div className="grid place-items-center rounded-card border border-line bg-surface py-16 text-muted">
          <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
        </div>
      ) : lista.isError ? (
        <div className="grid place-items-center gap-3 rounded-card border border-line bg-surface py-16 text-center">
          <p className="text-sm text-secondary">Não foi possível carregar os chamados.</p>
          <button
            type="button"
            onClick={() => void lista.refetch()}
            className="rounded-controle border border-line-2 px-3 py-2 text-sm font-medium text-ink"
          >
            Tentar novamente
          </button>
        </div>
      ) : lista.data && lista.data.items.length > 0 ? (
        <div className="flex flex-col gap-3">
          {lista.data.items.map((c) => (
            <Link key={c.id_chamado} to={`/chamados/${c.id_chamado}`}>
              <CardChamado
                chamado={{
                  protocolo: c.protocolo,
                  titulo: c.titulo,
                  descricao: c.descricao,
                  categoria: c.categoria.nome_categoria,
                  ...(c.categoria.icone ? { categoriaIcone: c.categoria.icone } : {}),
                  severidade: c.severidade as Severidade,
                  status: c.status_chamado as StatusChamado,
                  ...(c.tecnico_responsavel ? { responsavel: c.tecnico_responsavel.nome } : {}),
                }}
                rodape={
                  <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span>Aberto: {dataCurta(c.data_criacao)}</span>
                    <span>Atualizado: {dataCurta(c.data_atualizacao)}</span>
                    {ehTecnico && <span>Solicitante: {c.solicitante.nome}</span>}
                    {c.tecnico_responsavel && <span>👤 {c.tecnico_responsavel.nome}</span>}
                    <span className="ml-auto">{c.qtd_mensagens} msg ›</span>
                  </span>
                }
              />
            </Link>
          ))}
        </div>
      ) : (
        <div className="grid place-items-center rounded-card border border-dashed border-line-2 bg-surface py-16 text-center text-sm text-muted">
          Nenhum chamado encontrado com esses filtros.
        </div>
      )}

      {/* Paginação */}
      {lista.data && lista.data.total > PAGE_SIZE && (
        <div className="mt-4 flex items-center justify-between text-sm text-muted">
          <span>
            Página {page} de {totalPaginas}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => definirParam({ page: String(page - 1) })}
              className="rounded-controle border border-line-2 px-3 py-1.5 font-medium text-ink disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= totalPaginas}
              onClick={() => definirParam({ page: String(page + 1) })}
              className="rounded-controle border border-line-2 px-3 py-1.5 font-medium text-ink disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
