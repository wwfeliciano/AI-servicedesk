import { useState } from 'react';
import type { ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  Loader2,
  Paperclip,
  Send,
  X,
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { toast } from 'sonner';

import { baixarAnexo, enviarAnexo, listarAnexos, MAX_POR_CHAMADO } from '@/api/anexos';
import { publicarArtigo } from '@/api/baseConhecimento';
import {
  adicionarFollowup,
  atribuir,
  concluir,
  listarFollowups,
  listarHistorico,
  listarSolucoes,
  listarTecnicos,
  obterChamado,
  responderSolucao,
  triar,
  type ChamadoSaida,
} from '@/api/chamados';
import { SeveridadeBadge } from '@/components/SeveridadeBadge';
import { StatusBadge } from '@/components/StatusBadge';
import { ZonaUpload } from '@/components/ZonaUpload';
import { ehErroAPI } from '@/lib/erros';
import { dataCurta, tempoRelativoCurto } from '@/lib/formato';
import { useSessao } from '@/stores/sessao';
import type { Perfil, Severidade, StatusChamado } from '@/types/dominio';

const ROTULO_HISTORICO: Record<string, string> = {
  NOVO: 'Aberto',
  PENDENTE: 'Triado',
  ATRIBUIDO: 'Em andamento',
  CONCLUIDO: 'Resolvido',
  FECHADO: 'Encerrado',
};

export function ChamadoDetalhePage() {
  const { id } = useParams();
  const idNum = Number(id);
  const cliente = useQueryClient();
  const usuario = useSessao((e) => e.usuario);
  const perfil: Perfil = usuario?.tipo_perfil ?? 'CLIENTE';
  const ehTecnico = perfil === 'ANALISTA' || perfil === 'ADMIN';
  const habilitado = Number.isInteger(idNum) && idNum > 0;

  const [modal, setModal] = useState<null | 'atribuir' | 'concluir' | 'reprovar' | 'publicar'>(null);
  const [mensagem, setMensagem] = useState('');

  const chamado = useQuery({
    queryKey: ['chamado', idNum],
    queryFn: () => obterChamado(idNum),
    enabled: habilitado,
    retry: false,
  });
  const ok = chamado.isSuccess;

  const historico = useQuery({
    queryKey: ['chamado', idNum, 'historico'],
    queryFn: () => listarHistorico(idNum),
    enabled: ok,
  });
  const followups = useQuery({
    queryKey: ['chamado', idNum, 'followups'],
    queryFn: () => listarFollowups(idNum),
    enabled: ok,
  });
  const solucoes = useQuery({
    queryKey: ['chamado', idNum, 'solucoes'],
    queryFn: () => listarSolucoes(idNum),
    enabled: ok,
  });
  const anexos = useQuery({
    queryKey: ['chamado', idNum, 'anexos'],
    queryFn: () => listarAnexos(idNum),
    enabled: ok,
  });

  function invalidarTudo() {
    for (const k of ['historico', 'followups', 'solucoes', 'anexos'] as const) {
      void cliente.invalidateQueries({ queryKey: ['chamado', idNum, k] });
    }
    void cliente.invalidateQueries({ queryKey: ['chamado', idNum] });
    void cliente.invalidateQueries({ queryKey: ['chamados'] });
    void cliente.invalidateQueries({ queryKey: ['resumo'] });
    void cliente.invalidateQueries({ queryKey: ['notificacoes', 'contagem'] });
  }

  function aoErro(erro: unknown, padrao: string) {
    toast.error(ehErroAPI(erro) ? erro.mensagem : padrao);
  }

  const mTriar = useMutation({
    mutationFn: () => triar(idNum, {}),
    onSuccess: () => {
      toast.success('Chamado triado.');
      invalidarTudo();
    },
    onError: (e) => aoErro(e, 'Não foi possível triar.'),
  });
  const mAtribuir = useMutation({
    mutationFn: (idTecnico: number) => atribuir(idNum, idTecnico),
    onSuccess: () => {
      toast.success('Chamado atribuído.');
      setModal(null);
      invalidarTudo();
    },
    onError: (e) => aoErro(e, 'Não foi possível atribuir.'),
  });
  const mConcluir = useMutation({
    mutationFn: (descricao: string) => concluir(idNum, descricao),
    onSuccess: () => {
      toast.success('Solução registrada.');
      setModal(null);
      invalidarTudo();
    },
    onError: (e) => aoErro(e, 'Não foi possível concluir.'),
  });
  const mResponder = useMutation({
    mutationFn: (v: { idSolucao: number; aprovada: boolean; motivo?: string }) =>
      responderSolucao(v.idSolucao, v.aprovada, v.motivo),
    onSuccess: (_d, v) => {
      toast.success(v.aprovada ? 'Solução aprovada. Chamado encerrado.' : 'Solução reprovada.');
      setModal(null);
      invalidarTudo();
    },
    onError: (e) => aoErro(e, 'Não foi possível responder.'),
  });
  const mFollowup = useMutation({
    mutationFn: (texto: string) => adicionarFollowup(idNum, texto),
    onSuccess: () => {
      setMensagem('');
      void cliente.invalidateQueries({ queryKey: ['chamado', idNum, 'followups'] });
    },
    onError: (e) => aoErro(e, 'Não foi possível enviar a mensagem.'),
  });
  const mPublicar = useMutation({
    mutationFn: (v: { idSolucao: number; titulo: string; conteudo: string }) =>
      publicarArtigo({ id_solucao: v.idSolucao, titulo: v.titulo, conteudo: v.conteudo }),
    onSuccess: () => {
      toast.success('Artigo publicado na Base de Conhecimento.');
      setModal(null);
      void cliente.invalidateQueries({ queryKey: ['base-conhecimento'] });
    },
    onError: (e) => aoErro(e, 'Não foi possível publicar na base.'),
  });

  if (!habilitado || chamado.isLoading) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-muted">
        <Loader2 aria-label="Carregando" className="size-6 animate-spin text-brand" />
      </div>
    );
  }

  const naoEncontrado =
    chamado.isError && ehErroAPI(chamado.error) && chamado.error.codigo === 'NAO_ENCONTRADO';
  if (naoEncontrado || chamado.isError) {
    return (
      <section className="mx-auto max-w-3xl">
        <VoltarLink />
        <div className="grid place-items-center gap-2 rounded-card border border-dashed border-line-2 bg-surface py-16 text-center">
          <p className="font-mono text-sm text-brand">{naoEncontrado ? '404' : 'erro'}</p>
          <p className="text-sm text-secondary">
            {naoEncontrado ? 'Chamado não encontrado.' : 'Não foi possível carregar o chamado.'}
          </p>
        </div>
      </section>
    );
  }

  const c = chamado.data as ChamadoSaida;
  const st = c.status_chamado as StatusChamado;
  const souSolicitante = usuario?.id_usuario === c.solicitante.id_usuario;
  const solucaoPendente = (solucoes.data ?? []).find((s) => s.status_aprovacao === 'PENDENTE_APROVACAO');
  const solucaoAprovada = (solucoes.data ?? []).find((s) => s.status_aprovacao === 'APROVADA');
  const fechado = st === 'FECHADO';

  return (
    <section className="mx-auto max-w-3xl">
      <VoltarLink />

      <article className="rounded-card border border-line bg-surface">
        <header className="border-b border-line p-5">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm text-muted">{c.protocolo}</span>
            <span className="rounded-md bg-brand-soft px-2 py-0.5 text-xs font-semibold text-brand-soft-ink">
              {c.categoria.icone ? `${c.categoria.icone} ` : ''}
              {c.categoria.nome_categoria}
            </span>
          </div>
          <h1 className="text-xl text-ink">{c.titulo}</h1>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusBadge status={st} />
            <SeveridadeBadge severidade={c.severidade as Severidade} />
          </div>
        </header>

        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 p-5 text-sm sm:grid-cols-2">
          <Campo rotulo="Solicitante" valor={c.solicitante.nome} />
          <Campo rotulo="Responsável" valor={c.tecnico_responsavel?.nome ?? 'Sem responsável'} />
          <Campo rotulo="Aberto em" valor={dataCurta(c.data_criacao)} />
          <Campo rotulo="Atualizado em" valor={dataCurta(c.data_atualizacao)} />
        </dl>

        <div className="border-t border-line p-5">
          <h2 className="mb-2 text-xs font-semibold tracking-wide text-muted uppercase">Descrição</h2>
          <p className="text-sm whitespace-pre-wrap text-ink">{c.descricao}</p>
        </div>

        {/* Ações por perfil (ANALISTA/ADMIN) */}
        {ehTecnico && !fechado && (
          <div className="flex flex-wrap gap-2 border-t border-line p-5">
            {st === 'NOVO' && (
              <button
                type="button"
                onClick={() => mTriar.mutate()}
                disabled={mTriar.isPending}
                className="rounded-controle border border-line-2 px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
              >
                Triar (→ Aberto)
              </button>
            )}
            {(st === 'NOVO' || st === 'PENDENTE' || st === 'ATRIBUIDO') && (
              <button
                type="button"
                onClick={() => setModal('atribuir')}
                className="rounded-controle border border-line-2 px-4 py-2 text-sm font-semibold text-ink"
              >
                {st === 'ATRIBUIDO' ? 'Reatribuir' : 'Atribuir'}
              </button>
            )}
            {st === 'ATRIBUIDO' && (
              <button
                type="button"
                onClick={() => setModal('concluir')}
                className="rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Registrar solução
              </button>
            )}
          </div>
        )}

        {/* Cartão da solução para o solicitante quando CONCLUIDO */}
        {souSolicitante && st === 'CONCLUIDO' && solucaoPendente && (
          <div className="border-t border-line p-5">
            <div className="rounded-card border border-brand-500/40 bg-brand-soft p-4">
              <h2 className="flex items-center gap-2 text-sm font-semibold text-ink">
                <CheckCircle2 aria-hidden className="size-4 text-brand" /> Solução proposta
              </h2>
              <p className="mt-2 text-sm whitespace-pre-wrap text-secondary">
                {solucaoPendente.descricao_solucao}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() =>
                    mResponder.mutate({ idSolucao: solucaoPendente.id_solucao, aprovada: true })
                  }
                  disabled={mResponder.isPending}
                  className="rounded-controle bg-success px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                >
                  Aprovar e encerrar
                </button>
                <button
                  type="button"
                  onClick={() => setModal('reprovar')}
                  className="rounded-controle border border-line-2 px-4 py-2 text-sm font-semibold text-ink"
                >
                  Reprovar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Publicar na Base de Conhecimento (ANALISTA/ADMIN): só com solução aprovada (RN05) */}
        {ehTecnico && solucaoAprovada && (
          <div className="border-t border-line p-5">
            <div className="flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface-2 p-4">
              <BookOpen aria-hidden className="size-5 text-brand" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-ink">Base de Conhecimento</p>
                <p className="text-xs text-secondary">
                  A solução foi aprovada. Publique um artigo para ajudar outros usuários (RN05).
                </p>
              </div>
              <button
                type="button"
                onClick={() => setModal('publicar')}
                className="rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Publicar na base
              </button>
            </div>
          </div>
        )}

        {/* Anexos */}
        <div className="border-t border-line p-5">
          <h2 className="mb-3 text-xs font-semibold tracking-wide text-muted uppercase">Anexos</h2>
          {(anexos.data ?? []).length > 0 ? (
            <ul className="mb-4 flex flex-col gap-2">
              {(anexos.data ?? []).map((a) => (
                <li
                  key={a.id_anexo}
                  className="flex items-center gap-2 rounded-controle border border-line bg-surface-2 px-3 py-2 text-sm"
                >
                  <Paperclip aria-hidden className="size-4 text-muted" />
                  <span className="min-w-0 flex-1 truncate text-ink">{a.nome_original}</span>
                  <button
                    type="button"
                    aria-label={`Baixar ${a.nome_original}`}
                    onClick={() => void baixarAnexo(a)}
                    className="grid size-7 place-items-center rounded text-brand hover:bg-brand-soft"
                  >
                    <Download aria-hidden className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mb-4 text-sm text-muted">Nenhum anexo.</p>
          )}
          {!fechado && (
            <ZonaUpload
              desabilitado={(anexos.data ?? []).length >= MAX_POR_CHAMADO}
              onArquivos={async (arquivos) => {
                for (const a of arquivos) {
                  await enviarAnexo(idNum, a).catch((e) => aoErro(e, 'Falha ao enviar anexo.'));
                }
                void cliente.invalidateQueries({ queryKey: ['chamado', idNum, 'anexos'] });
              }}
            />
          )}
        </div>

        {/* Linha do tempo + follow-ups */}
        <div className="border-t border-line p-5">
          <h2 className="mb-3 text-xs font-semibold tracking-wide text-muted uppercase">
            Acompanhamento
          </h2>
          <ol className="mb-4 flex flex-col gap-3 border-l border-line pl-4">
            {(historico.data ?? []).map((e) => (
              <li key={e.id_historico} className="relative">
                <span className="absolute -left-[21px] top-1 size-2.5 rounded-full bg-brand" aria-hidden />
                <p className="text-sm text-ink">
                  {e.status_anterior
                    ? `${ROTULO_HISTORICO[e.status_anterior] ?? e.status_anterior} → ${ROTULO_HISTORICO[e.status_novo] ?? e.status_novo}`
                    : ROTULO_HISTORICO[e.status_novo] ?? e.status_novo}
                  {e.observacao ? ` · ${e.observacao}` : ''}
                </p>
                <p className="flex items-center gap-1 text-xs text-muted">
                  <Clock aria-hidden className="size-3" /> {tempoRelativoCurto(e.data_evento)}
                </p>
              </li>
            ))}
          </ol>

          {/* Mensagens (follow-ups) */}
          <div className="flex flex-col gap-2">
            {(followups.data ?? []).map((f) => (
              <div key={f.id_followup} className="rounded-card border border-line bg-surface-2 p-3">
                <p className="text-sm whitespace-pre-wrap text-ink">{f.mensagem}</p>
                <p className="mt-1 text-xs text-muted">{tempoRelativoCurto(f.data_envio)}</p>
              </div>
            ))}
          </div>

          {!fechado && (
            <form
              className="mt-3 flex gap-2"
              onSubmit={(ev) => {
                ev.preventDefault();
                if (mensagem.trim()) mFollowup.mutate(mensagem.trim());
              }}
            >
              <input
                value={mensagem}
                onChange={(ev) => setMensagem(ev.target.value)}
                placeholder="Escreva uma mensagem…"
                className="min-w-0 flex-1 rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
              />
              <button
                type="submit"
                disabled={mFollowup.isPending || !mensagem.trim()}
                className="flex items-center gap-1.5 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                <Send aria-hidden className="size-4" /> Enviar
              </button>
            </form>
          )}
          {fechado && (
            <p className="mt-3 text-xs text-muted">Chamado encerrado — não aceita novas mensagens.</p>
          )}
        </div>
      </article>

      {modal === 'atribuir' && (
        <ModalAtribuir
          onFechar={() => setModal(null)}
          onAtribuir={(idT) => mAtribuir.mutate(idT)}
          enviando={mAtribuir.isPending}
        />
      )}
      {modal === 'concluir' && (
        <ModalTexto
          titulo="Registrar solução"
          rotulo="Descreva a solução aplicada"
          botao="Concluir"
          onFechar={() => setModal(null)}
          onEnviar={(t) => mConcluir.mutate(t)}
          enviando={mConcluir.isPending}
        />
      )}
      {modal === 'reprovar' && solucaoPendente && (
        <ModalTexto
          titulo="Reprovar solução"
          rotulo="Motivo da reprovação"
          botao="Reprovar"
          onFechar={() => setModal(null)}
          onEnviar={(t) =>
            mResponder.mutate({ idSolucao: solucaoPendente.id_solucao, aprovada: false, motivo: t })
          }
          enviando={mResponder.isPending}
        />
      )}
      {modal === 'publicar' && solucaoAprovada && (
        <ModalPublicar
          tituloInicial={c.titulo}
          conteudoInicial={solucaoAprovada.descricao_solucao}
          onFechar={() => setModal(null)}
          onPublicar={(titulo, conteudo) =>
            mPublicar.mutate({ idSolucao: solucaoAprovada.id_solucao, titulo, conteudo })
          }
          enviando={mPublicar.isPending}
        />
      )}
    </section>
  );
}

function VoltarLink() {
  return (
    <Link to="/chamados" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-brand">
      <ArrowLeft aria-hidden className="size-4" /> Voltar para a lista
    </Link>
  );
}

function Campo({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="flex justify-between gap-3 border-b border-line pb-3 sm:border-0 sm:pb-0">
      <dt className="text-muted">{rotulo}</dt>
      <dd className="font-medium text-ink">{valor}</dd>
    </div>
  );
}

function ModalBase({ titulo, children, onFechar }: { titulo: string; children: ReactNode; onFechar: () => void }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onFechar} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className="relative w-full max-w-md rounded-card-lg border border-line bg-surface shadow-pop"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{titulo}</h2>
          <button type="button" onClick={onFechar} aria-label="Fechar" className="grid size-8 place-items-center rounded-controle text-muted hover:bg-surface-2">
            <X aria-hidden className="size-4" />
          </button>
        </div>
        <div className="px-5 py-5">{children}</div>
      </div>
    </div>
  );
}

function ModalTexto({
  titulo,
  rotulo,
  botao,
  onFechar,
  onEnviar,
  enviando,
}: {
  titulo: string;
  rotulo: string;
  botao: string;
  onFechar: () => void;
  onEnviar: (texto: string) => void;
  enviando: boolean;
}) {
  const [texto, setTexto] = useState('');
  return (
    <ModalBase titulo={titulo} onFechar={onFechar}>
      <label className="flex flex-col gap-1.5">
        <span className="text-xs font-semibold text-secondary">{rotulo}</span>
        <textarea
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          rows={5}
          className="resize-y rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
        />
      </label>
      <div className="mt-4 flex justify-end gap-2">
        <button type="button" onClick={onFechar} className="rounded-controle border border-line-2 px-4 py-2 text-sm font-medium text-ink">
          Cancelar
        </button>
        <button
          type="button"
          onClick={() => onEnviar(texto.trim())}
          disabled={enviando || !texto.trim()}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {enviando && <Loader2 aria-hidden className="size-4 animate-spin" />}
          {botao}
        </button>
      </div>
    </ModalBase>
  );
}
function ModalPublicar({
  tituloInicial,
  conteudoInicial,
  onFechar,
  onPublicar,
  enviando,
}: {
  tituloInicial: string;
  conteudoInicial: string;
  onFechar: () => void;
  onPublicar: (titulo: string, conteudo: string) => void;
  enviando: boolean;
}) {
  const [titulo, setTitulo] = useState(tituloInicial);
  const [conteudo, setConteudo] = useState(conteudoInicial);
  return (
    <ModalBase titulo="Publicar na Base de Conhecimento" onFechar={onFechar}>
      <p className="mb-4 text-xs text-secondary">
        O artigo será criado a partir desta solução aprovada. Ajuste o título e o conteúdo para
        ficarem úteis a quem buscar depois.
      </p>
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
          rows={7}
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
          onClick={() => onPublicar(titulo.trim(), conteudo.trim())}
          disabled={enviando || !titulo.trim() || !conteudo.trim()}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {enviando && <Loader2 aria-hidden className="size-4 animate-spin" />}
          Publicar
        </button>
      </div>
    </ModalBase>
  );
}


function ModalAtribuir({
  onFechar,
  onAtribuir,
  enviando,
}: {
  onFechar: () => void;
  onAtribuir: (idTecnico: number) => void;
  enviando: boolean;
}) {
  const [sel, setSel] = useState<number | null>(null);
  const tecnicos = useQuery({ queryKey: ['tecnicos'], queryFn: listarTecnicos });
  return (
    <ModalBase titulo="Atribuir chamado" onFechar={onFechar}>
      {tecnicos.isLoading ? (
        <div className="py-6 text-center text-muted">
          <Loader2 aria-label="Carregando" className="mx-auto size-5 animate-spin text-brand" />
        </div>
      ) : (
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-semibold text-secondary">Responsável</span>
          <select
            value={sel ?? ''}
            onChange={(e) => setSel(Number(e.target.value))}
            className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
          >
            <option value="" disabled>
              Selecione um técnico…
            </option>
            {(tecnicos.data ?? []).map((t) => (
              <option key={t.id_usuario} value={t.id_usuario}>
                {t.nome} ({t.tipo_perfil})
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="mt-4 flex justify-end gap-2">
        <button type="button" onClick={onFechar} className="rounded-controle border border-line-2 px-4 py-2 text-sm font-medium text-ink">
          Cancelar
        </button>
        <button
          type="button"
          onClick={() => sel && onAtribuir(sel)}
          disabled={enviando || sel == null}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {enviando && <Loader2 aria-hidden className="size-4 animate-spin" />}
          Atribuir
        </button>
      </div>
    </ModalBase>
  );
}
