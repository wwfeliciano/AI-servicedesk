import { useEffect, useState } from 'react';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronDown, FilePlus2, Loader2, PencilLine, Search } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import {
  editarArtigo,
  listarArtigos,
  type ArtigoSaida,
  type FiltroArtigos,
} from '@/api/baseConhecimento';
import { listarCategorias } from '@/api/chamados';
import { ehErroAPI } from '@/lib/erros';
import { cx, dataCurta } from '@/lib/formato';
import { useDebounce } from '@/lib/useDebounce';
import { useSessao } from '@/stores/sessao';

const PAGE_SIZE = 10;

export function BaseConhecimentoPage() {
  const [params, setParams] = useSearchParams();
  const usuario = useSessao((e) => e.usuario);
  const ehTecnico = usuario?.tipo_perfil === 'ANALISTA' || usuario?.tipo_perfil === 'ADMIN';

  // Estado derivado da URL (busca, categoria e página) para o Voltar do navegador.
  const qUrl = params.get('q') ?? '';
  const idCategoriaUrl = params.get('categoria');
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1);

  const [busca, setBusca] = useState(qUrl);
  const buscaDebounced = useDebounce(busca, 300);
  const [aberto, setAberto] = useState<number | null>(null);
  const [editando, setEditando] = useState<ArtigoSaida | null>(null);

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

  const filtro: FiltroArtigos = {
    page,
    page_size: PAGE_SIZE,
    ...(qUrl ? { q: qUrl } : {}),
    ...(idCategoriaUrl ? { id_categoria: Number(idCategoriaUrl) } : {}),
  };
  const lista = useQuery({
    queryKey: ['base-conhecimento', filtro],
    queryFn: () => listarArtigos(filtro),
    placeholderData: keepPreviousData,
  });

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
      <header className="mb-5">
        <p className="text-xs font-semibold tracking-wide text-brand uppercase">
          Encontre sua resposta
        </p>
        <h1 className="mt-1 text-2xl text-ink">Base de Conhecimento</h1>
        <p className="mt-1 text-sm text-secondary">
          Guias práticos escritos a partir de soluções já aprovadas.
        </p>
      </header>

      {/* Busca */}
      <div className="mb-4 flex items-center gap-2 rounded-controle border border-line-2 bg-surface px-3">
        <Search aria-hidden className="size-4 text-muted" />
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por palavra-chave…"
          aria-label="Buscar na base de conhecimento"
          className="w-full bg-transparent py-2.5 text-sm text-ink placeholder:text-muted focus:outline-none"
        />
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

      {/* Lista em acordeão */}
      {lista.isLoading ? (
        <div className="grid place-items-center rounded-card border border-line bg-surface py-16 text-muted">
          <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
        </div>
      ) : lista.isError ? (
        <div className="grid place-items-center gap-3 rounded-card border border-line bg-surface py-16 text-center">
          <p className="text-sm text-secondary">Não foi possível carregar a base de conhecimento.</p>
          <button
            type="button"
            onClick={() => void lista.refetch()}
            className="rounded-controle border border-line-2 px-3 py-2 text-sm font-medium text-ink"
          >
            Tentar novamente
          </button>
        </div>
      ) : lista.data && lista.data.items.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {lista.data.items.map((a) => (
            <ArtigoItem
              key={a.id_base}
              artigo={a}
              aberto={aberto === a.id_base}
              onAlternar={() => setAberto(aberto === a.id_base ? null : a.id_base)}
              ehTecnico={ehTecnico}
              onEditar={() => setEditando(a)}
            />
          ))}
        </ul>
      ) : (
        <div className="grid place-items-center gap-2 rounded-card border border-dashed border-line-2 bg-surface py-16 text-center text-sm text-muted">
          {qUrl || idCategoriaUrl
            ? 'Nenhum artigo encontrado com esses filtros.'
            : 'Ainda não há artigos publicados na base.'}
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

      {editando && <ModalEditar artigo={editando} onFechar={() => setEditando(null)} />}
    </section>
  );
}

function ArtigoItem({
  artigo,
  aberto,
  onAlternar,
  ehTecnico,
  onEditar,
}: {
  artigo: ArtigoSaida;
  aberto: boolean;
  onAlternar: () => void;
  ehTecnico: boolean;
  onEditar: () => void;
}) {
  // "Abrir chamado" pré-preenche a categoria do artigo no wizard (seção 8.5).
  const paramsAbrir = new URLSearchParams({
    categoria: String(artigo.categoria.id_categoria),
    titulo: artigo.titulo,
  });

  return (
    <li className="rounded-card border border-line bg-surface">
      <h3>
        <button
          type="button"
          aria-expanded={aberto}
          onClick={onAlternar}
          className="flex w-full items-center gap-3 px-5 py-4 text-left"
        >
          <span className="rounded-md bg-brand-soft px-2 py-0.5 text-xs font-semibold text-brand-soft-ink">
            {artigo.categoria.icone ? `${artigo.categoria.icone} ` : ''}
            {artigo.categoria.nome_categoria}
          </span>
          <span className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">
            {artigo.titulo}
          </span>
          <ChevronDown
            aria-hidden
            className={cx('size-4 shrink-0 text-muted transition', aberto && 'rotate-180')}
          />
        </button>
      </h3>
      {aberto && (
        <div className="border-t border-line px-5 py-4">
          <p className="text-sm whitespace-pre-wrap text-secondary">{artigo.conteudo}</p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Link
              to={`/chamados/novo?${paramsAbrir.toString()}`}
              className="flex items-center gap-1.5 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              <FilePlus2 aria-hidden className="size-4" /> Não resolveu? Abrir chamado
            </Link>
            {ehTecnico && (
              <button
                type="button"
                onClick={onEditar}
                className="flex items-center gap-1.5 rounded-controle border border-line-2 px-4 py-2 text-sm font-medium text-ink"
              >
                <PencilLine aria-hidden className="size-4" /> Editar
              </button>
            )}
            <span className="ml-auto text-xs text-muted">
              Publicado em {dataCurta(artigo.data_inclusao)}
            </span>
          </div>
        </div>
      )}
    </li>
  );
}

function ModalEditar({ artigo, onFechar }: { artigo: ArtigoSaida; onFechar: () => void }) {
  const cliente = useQueryClient();
  const [titulo, setTitulo] = useState(artigo.titulo);
  const [conteudo, setConteudo] = useState(artigo.conteudo);

  const mutacao = useMutation({
    mutationFn: () => editarArtigo(artigo.id_base, { titulo: titulo.trim(), conteudo: conteudo.trim() }),
    onSuccess: () => {
      toast.success('Artigo atualizado.');
      void cliente.invalidateQueries({ queryKey: ['base-conhecimento'] });
      onFechar();
    },
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível salvar o artigo.'),
  });

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onFechar} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Editar artigo"
        className="relative w-full max-w-lg rounded-card-lg border border-line bg-surface p-5 shadow-pop"
      >
        <h2 className="mb-4 text-base font-semibold text-ink">Editar artigo</h2>
        <label className="mb-3 flex flex-col gap-1.5">
          <span className="text-xs font-semibold text-secondary">Título</span>
          <input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            maxLength={150}
            className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-semibold text-secondary">Conteúdo</span>
          <textarea
            value={conteudo}
            onChange={(e) => setConteudo(e.target.value)}
            rows={8}
            className="resize-y rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
          />
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onFechar}
            className="rounded-controle border border-line-2 px-4 py-2 text-sm font-medium text-ink"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => mutacao.mutate()}
            disabled={mutacao.isPending || !titulo.trim() || !conteudo.trim()}
            className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {mutacao.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}
