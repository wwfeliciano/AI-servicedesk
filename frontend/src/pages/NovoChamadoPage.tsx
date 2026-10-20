import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, Paperclip, Siren, X } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { enviarAnexo, MAX_POR_CHAMADO } from '@/api/anexos';
import { abrirChamado, listarCategorias, type ChamadoSaida } from '@/api/chamados';
import { OpcaoCard } from '@/components/OpcaoCard';
import { Stepper } from '@/components/Stepper';
import { ZonaUpload } from '@/components/ZonaUpload';
import { ehErroAPI } from '@/lib/erros';
import { cx } from '@/lib/formato';
import { useRascunhoChamado } from '@/stores/rascunhoChamado';
import type { Severidade } from '@/types/dominio';

const ETAPAS = ['Categoria', 'Prioridade', 'Detalhes'];

const PRIORIDADES: { valor: Severidade; titulo: string; descricao: string }[] = [
  { valor: 'BAIXA', titulo: 'Baixa', descricao: 'Sem impacto imediato' },
  { valor: 'MEDIA', titulo: 'Média', descricao: 'Impacto moderado' },
  { valor: 'ALTA', titulo: 'Alta', descricao: 'Afeta a produtividade' },
  { valor: 'CRITICO', titulo: 'Urgente', descricao: 'Bloqueio total' },
];

function formatarTamanho(bytes: number): string {
  return bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function NovoChamadoPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const rascunho = useRascunhoChamado();
  const [confirmacao, setConfirmacao] = useState<ChamadoSaida | null>(null);
  const [anexosFalharam, setAnexosFalharam] = useState(false);
  const [erroDetalhe, setErroDetalhe] = useState<{ titulo?: string; descricao?: string }>({});

  const categorias = useQuery({ queryKey: ['categorias'], queryFn: listarCategorias });

  // Prefill vindo da Base de Conhecimento ("Abrir chamado" por um artigo, seção 8.5):
  // ?categoria=<id>&titulo=<texto>. Só aplica num rascunho ainda vazio, para não
  // sobrescrever o que o usuário já começou a preencher. Roda uma vez.
  const [params] = useSearchParams();
  const definirRascunho = rascunho.definir;
  useEffect(() => {
    const idCategoria = Number(params.get('categoria'));
    const tituloRef = params.get('titulo') ?? '';
    if (!idCategoria && !tituloRef) return;
    if (rascunho.id_categoria != null || rascunho.titulo) return;
    definirRascunho({
      ...(idCategoria ? { id_categoria: idCategoria } : {}),
      ...(tituloRef ? { titulo: `Dúvida: ${tituloRef}`.slice(0, 150) } : {}),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mutacao = useMutation({
    mutationFn: abrirChamado,
    onSuccess: async (chamado) => {
      // Sobe os anexos selecionados APÓS criar o chamado. Se algum falhar, o
      // chamado continua criado e a confirmação avisa (o usuário reenvia no detalhe).
      const anexos = rascunho.anexos;
      let falhou = false;
      for (const arquivo of anexos) {
        try {
          await enviarAnexo(chamado.id_chamado, arquivo);
        } catch {
          falhou = true;
        }
      }
      setAnexosFalharam(falhou);
      setConfirmacao(chamado);
      rascunho.limpar();
      void cliente.invalidateQueries({ queryKey: ['chamados'] });
      void cliente.invalidateQueries({ queryKey: ['resumo'] });
    },
    onError: (erro) => {
      toast.error(ehErroAPI(erro) ? erro.mensagem : 'Não foi possível abrir o chamado.');
    },
  });

  // ----- Tela de confirmação -----
  if (confirmacao) {
    return (
      <section className="mx-auto max-w-lg py-10 text-center">
        <span className="mx-auto mb-5 grid size-16 place-items-center rounded-full bg-success-soft text-success-ink">
          <CheckCircle2 aria-hidden className="size-8" />
        </span>
        <h1 className="text-2xl text-ink">Chamado aberto!</h1>
        <p className="mt-2 text-sm text-secondary">
          Seu chamado foi registrado com o protocolo abaixo. Acompanhe o andamento em Meus Chamados.
        </p>
        <p className="mt-6 mb-4 font-mono text-3xl font-semibold tracking-tight text-brand">
          {confirmacao.protocolo}
        </p>
        {anexosFalharam && (
          <p className="mb-6 rounded-controle border border-warning/30 bg-warning-soft px-3 py-2 text-xs text-warning-ink">
            O chamado foi criado, mas não foi possível enviar um ou mais anexos. Você pode reenviá-los
            na tela do chamado.
          </p>
        )}
        <div className="flex justify-center gap-3">
          <button
            type="button"
            onClick={() => navegar(`/chamados/${confirmacao.id_chamado}`)}
            className="rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            Ver chamado
          </button>
          <Link
            to="/chamados"
            className="rounded-controle border border-line-2 px-4 py-2.5 text-sm font-medium text-ink"
          >
            Meus chamados
          </Link>
        </div>
      </section>
    );
  }

  const etapa = rascunho.etapa;

  function proximo() {
    setErroDetalhe({});
    if (etapa === 0 && rascunho.id_categoria == null) return;
    if (etapa < 2) {
      rascunho.definir({ etapa: etapa + 1 });
      return;
    }
    // Etapa 3: valida título/descrição (FE02) antes de enviar.
    const titulo = rascunho.titulo.trim();
    const descricao = rascunho.descricao.trim();
    const erros: { titulo?: string; descricao?: string } = {};
    if (!titulo) erros.titulo = 'Informe o título do chamado.';
    if (titulo.length > 150) erros.titulo = 'O título deve ter no máximo 150 caracteres.';
    if (!descricao) erros.descricao = 'Descreva o problema.';
    if (descricao.length > 500) erros.descricao = 'A descrição deve ter no máximo 500 caracteres.';
    if (erros.titulo || erros.descricao) {
      setErroDetalhe(erros);
      return;
    }
    mutacao.mutate({
      id_categoria: rascunho.id_categoria as number,
      severidade: rascunho.severidade,
      titulo,
      descricao,
    });
  }

  function cancelar() {
    // FE03: descarta o rascunho e volta ao Dashboard.
    rascunho.limpar();
    navegar('/dashboard');
  }

  const podeAvancar = etapa !== 0 || rascunho.id_categoria != null;

  return (
    <section className="mx-auto max-w-3xl">
      <header className="mb-6 flex items-center gap-3">
        <button
          type="button"
          onClick={cancelar}
          aria-label="Voltar ao Dashboard"
          className="grid size-9 place-items-center rounded-controle border border-line text-secondary"
        >
          <ArrowLeft aria-hidden className="size-4" />
        </button>
        <div>
          <h1 className="text-2xl text-ink">Novo Chamado</h1>
          <p className="text-sm text-secondary">Preencha as informações para abrir seu chamado.</p>
        </div>
      </header>

      <div className="mb-6">
        <Stepper etapas={ETAPAS} atual={etapa} />
      </div>

      <div className="rounded-card border border-line bg-surface p-5">
        {/* Etapa 1 — Categoria */}
        {etapa === 0 && (
          <>
            <h2 className="text-base font-semibold text-ink">Qual área você precisa de ajuda?</h2>
            <p className="mt-1 mb-4 text-sm text-secondary">
              Selecione a categoria que melhor descreve seu problema.
            </p>
            {categorias.isLoading ? (
              <div className="grid place-items-center py-10 text-muted">
                <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
              </div>
            ) : (
              <div
                role="radiogroup"
                aria-label="Categoria"
                className="grid grid-cols-2 gap-3 sm:grid-cols-3"
              >
                {(categorias.data ?? []).map((c) => (
                  <OpcaoCard
                    key={c.id_categoria}
                    titulo={c.nome_categoria}
                    {...(c.icone ? { icone: c.icone } : {})}
                    selecionado={rascunho.id_categoria === c.id_categoria}
                    onSelecionar={() => rascunho.definir({ id_categoria: c.id_categoria })}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Etapa 2 — Prioridade (campo enviado é severidade) */}
        {etapa === 1 && (
          <>
            <h2 className="text-base font-semibold text-ink">Qual a urgência do problema?</h2>
            <p className="mt-1 mb-4 text-sm text-secondary">
              Prioridades mais altas são atendidas primeiro.
            </p>
            <div role="radiogroup" aria-label="Prioridade" className="flex flex-col gap-3">
              {PRIORIDADES.map((p) => (
                <OpcaoCard
                  key={p.valor}
                  titulo={p.titulo}
                  descricao={p.descricao}
                  icone={p.valor === 'CRITICO' ? <Siren className="size-5 text-danger" /> : undefined}
                  selecionado={rascunho.severidade === p.valor}
                  onSelecionar={() => rascunho.definir({ severidade: p.valor })}
                />
              ))}
            </div>
          </>
        )}

        {/* Etapa 3 — Detalhes */}
        {etapa === 2 && (
          <>
            <h2 className="text-base font-semibold text-ink">Descreva o problema</h2>
            <p className="mt-1 mb-4 text-sm text-secondary">
              Quanto mais detalhes, mais rápido conseguimos ajudar.
            </p>
            <label className="mb-4 flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Título do chamado *</span>
              <input
                value={rascunho.titulo}
                onChange={(e) => rascunho.definir({ titulo: e.target.value })}
                maxLength={150}
                placeholder="Ex: Não consigo acessar o sistema de ponto"
                aria-invalid={!!erroDetalhe.titulo}
                className={cx(
                  'rounded-controle border bg-surface px-3 py-2.5 text-sm text-ink',
                  erroDetalhe.titulo ? 'border-danger' : 'border-line-2',
                )}
              />
              {erroDetalhe.titulo && (
                <span className="text-xs text-danger-ink">{erroDetalhe.titulo}</span>
              )}
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Descrição detalhada *</span>
              <textarea
                value={rascunho.descricao}
                onChange={(e) => rascunho.definir({ descricao: e.target.value })}
                maxLength={500}
                rows={6}
                placeholder="Descreva o problema: quando começou, o que você tentou, qual a mensagem de erro…"
                aria-invalid={!!erroDetalhe.descricao}
                className={cx(
                  'resize-y rounded-controle border bg-surface px-3 py-2.5 text-sm text-ink',
                  erroDetalhe.descricao ? 'border-danger' : 'border-line-2',
                )}
              />
              <span
                className={cx(
                  'self-end text-xs',
                  rascunho.descricao.length === 0 || rascunho.descricao.length > 500
                    ? 'text-danger-ink'
                    : 'text-muted',
                )}
              >
                {rascunho.descricao.length}/500
              </span>
              {erroDetalhe.descricao && (
                <span className="text-xs text-danger-ink">{erroDetalhe.descricao}</span>
              )}
            </label>

            {/* Anexos (opcional) */}
            <div className="mt-4">
              <p className="mb-2 text-xs font-semibold text-secondary">Anexos (opcional)</p>
              <ZonaUpload
                desabilitado={rascunho.anexos.length >= MAX_POR_CHAMADO}
                dica={`${rascunho.anexos.length} de ${MAX_POR_CHAMADO} anexos`}
                onArquivos={(arquivos) => {
                  const total = [...rascunho.anexos, ...arquivos].slice(0, MAX_POR_CHAMADO);
                  rascunho.definir({ anexos: total });
                }}
              />
              {rascunho.anexos.length > 0 && (
                <ul className="mt-3 flex flex-col gap-2">
                  {rascunho.anexos.map((a, i) => (
                    <li
                      key={`${a.name}-${i}`}
                      className="flex items-center gap-2 rounded-controle border border-line bg-surface-2 px-3 py-2 text-sm"
                    >
                      <Paperclip aria-hidden className="size-4 text-muted" />
                      <span className="min-w-0 flex-1 truncate text-ink">{a.name}</span>
                      <span className="text-xs text-muted">{formatarTamanho(a.size)}</span>
                      <button
                        type="button"
                        aria-label={`Remover ${a.name}`}
                        onClick={() =>
                          rascunho.definir({
                            anexos: rascunho.anexos.filter((_, j) => j !== i),
                          })
                        }
                        className="grid size-6 place-items-center rounded text-muted hover:text-danger"
                      >
                        <X aria-hidden className="size-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}

        {/* Ações */}
        <div className="mt-6 flex items-center justify-between border-t border-line pt-4">
          <div className="flex gap-2">
            {etapa > 0 && (
              <button
                type="button"
                onClick={() => rascunho.definir({ etapa: etapa - 1 })}
                className="flex items-center gap-1.5 rounded-controle border border-line-2 px-4 py-2.5 text-sm font-medium text-ink"
              >
                <ArrowLeft aria-hidden className="size-4" /> Voltar
              </button>
            )}
            <button
              type="button"
              onClick={cancelar}
              className="rounded-controle px-4 py-2.5 text-sm font-medium text-muted hover:text-ink"
            >
              Cancelar
            </button>
          </div>
          <button
            type="button"
            onClick={proximo}
            disabled={!podeAvancar || mutacao.isPending}
            className="flex items-center gap-1.5 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {mutacao.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
            {etapa < 2 ? (
              <>
                Próximo <ArrowRight aria-hidden className="size-4" />
              </>
            ) : (
              'Enviar chamado'
            )}
          </button>
        </div>
      </div>
    </section>
  );
}
