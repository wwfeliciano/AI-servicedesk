import { useEffect, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, Loader2, MessageCircle, Smartphone } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { trocarSenha } from '@/api/auth';
import {
  atualizarPreferencias,
  desvincularWhatsapp,
  gerarVinculoWhatsapp,
  obterStatusWhatsapp,
  type VinculoGerado,
} from '@/api/perfil';
import { PaginaVazia } from '@/components/PaginaVazia';
import { ehErroAPI } from '@/lib/erros';
import { iniciais } from '@/lib/formato';
import { useSessao } from '@/stores/sessao';

const ROTULO_PERFIL: Record<string, string> = {
  ADMIN: 'Administrador',
  ANALISTA: 'Analista',
  CLIENTE: 'Cliente',
};

const esquema = z
  .object({
    senha_atual: z.string().min(1, 'Informe a senha atual.'),
    senha_nova: z.string().min(8, 'A nova senha deve ter ao menos 8 caracteres.'),
    confirmar: z.string().min(1, 'Confirme a nova senha.'),
  })
  .refine((d) => d.senha_nova === d.confirmar, {
    path: ['confirmar'],
    message: 'As senhas não coincidem.',
  });
type FormSenha = z.infer<typeof esquema>;

export function PerfilPage() {
  const usuario = useSessao((e) => e.usuario);
  const [erroGeral, setErroGeral] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormSenha>({ resolver: zodResolver(esquema) });

  async function aoEnviar(dados: FormSenha) {
    setErroGeral(null);
    try {
      await trocarSenha(dados.senha_atual, dados.senha_nova);
      toast.success('Senha alterada com sucesso.');
      reset();
    } catch (erro) {
      if (ehErroAPI(erro)) {
        if (erro.codigo === 'CREDENCIAL_INVALIDA') {
          setError('senha_atual', { message: erro.mensagem });
        } else if (erro.campos?.senha) {
          setError('senha_nova', { message: erro.campos.senha });
        } else {
          setErroGeral(erro.mensagem);
        }
      } else {
        setErroGeral('Não foi possível alterar a senha.');
      }
    }
  }

  return (
    <PaginaVazia eyebrow="Sua conta" titulo="Perfil" descricao="Seus dados e troca de senha.">
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* Dados do usuário */}
        <section className="rounded-card border border-line bg-surface p-5 shadow-card">
          <div className="flex items-center gap-3">
            <span className="grid size-12 place-items-center rounded-full bg-brand-soft text-base font-semibold text-brand-soft-ink">
              {iniciais(usuario?.nome ?? '?')}
            </span>
            <div className="min-w-0">
              <p className="truncate font-semibold text-ink">{usuario?.nome ?? '—'}</p>
              <p className="truncate text-sm text-secondary">{usuario?.email ?? '—'}</p>
            </div>
          </div>
          <dl className="mt-5 grid grid-cols-1 gap-3 text-sm">
            <div className="flex justify-between gap-3 border-t border-line pt-3">
              <dt className="text-muted">Perfil</dt>
              <dd className="font-medium text-ink">
                {usuario ? (ROTULO_PERFIL[usuario.tipo_perfil] ?? usuario.tipo_perfil) : '—'}
              </dd>
            </div>
            {usuario?.cargo && (
              <div className="flex justify-between gap-3 border-t border-line pt-3">
                <dt className="text-muted">Cargo</dt>
                <dd className="font-medium text-ink">{usuario.cargo}</dd>
              </div>
            )}
          </dl>
        </section>

        {/* Troca de senha */}
        <section className="rounded-card border border-line bg-surface p-5 shadow-card">
          <h2 className="text-base font-semibold text-ink">Trocar senha</h2>
          <p className="mt-1 text-sm text-secondary">
            Ao trocar a senha, suas outras sessões são encerradas.
          </p>

          {erroGeral && (
            <div
              role="alert"
              className="mt-4 rounded-controle border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger-ink"
            >
              {erroGeral}
            </div>
          )}

          <form className="mt-4 flex max-w-sm flex-col gap-4" onSubmit={handleSubmit(aoEnviar)} noValidate>
            {(
              [
                ['senha_atual', 'Senha atual', 'current-password'],
                ['senha_nova', 'Nova senha', 'new-password'],
                ['confirmar', 'Confirmar nova senha', 'new-password'],
              ] as const
            ).map(([campo, rotulo, autocomplete]) => (
              <label key={campo} className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold text-secondary">{rotulo}</span>
                <input
                  type="password"
                  autoComplete={autocomplete}
                  aria-invalid={!!errors[campo]}
                  className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
                  {...register(campo)}
                />
                {errors[campo] && (
                  <span className="text-xs text-danger-ink">{errors[campo]?.message}</span>
                )}
              </label>
            ))}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-1 flex items-center justify-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {isSubmitting && <Loader2 aria-hidden className="size-4 animate-spin" />}
              {isSubmitting ? 'Salvando…' : 'Alterar senha'}
            </button>
          </form>
        </section>

        {/* WhatsApp e preferências (F6.3) */}
        <SecaoWhatsapp />
      </div>
    </PaginaVazia>
  );
}

function SecaoWhatsapp() {
  const cliente = useQueryClient();
  const [consentimento, setConsentimento] = useState(false);
  const [vinculo, setVinculo] = useState<VinculoGerado | null>(null);

  // Enquanto há um código gerado e ainda não vinculou, consulta o status a cada 3 s.
  const status = useQuery({
    queryKey: ['perfil', 'whatsapp'],
    queryFn: obterStatusWhatsapp,
    refetchInterval: vinculo ? 3000 : false,
  });
  const vinculado = status.data?.vinculado ?? false;

  // Quando o vínculo é concluído (via WhatsApp), encerra o modo "aguardando".
  useEffect(() => {
    if (vinculo && vinculado) setVinculo(null);
  }, [vinculo, vinculado]);

  const mGerar = useMutation({
    mutationFn: () => gerarVinculoWhatsapp(consentimento),
    onSuccess: (v) => {
      setVinculo(v);
      void cliente.invalidateQueries({ queryKey: ['perfil', 'whatsapp'] });
    },
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível gerar o vínculo.'),
  });

  const mDesvincular = useMutation({
    mutationFn: desvincularWhatsapp,
    onSuccess: () => {
      setVinculo(null);
      toast.success('WhatsApp desvinculado.');
      void cliente.invalidateQueries({ queryKey: ['perfil', 'whatsapp'] });
    },
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível desvincular.'),
  });

  const mPreferencia = useMutation({
    mutationFn: atualizarPreferencias,
    onSuccess: () => void cliente.invalidateQueries({ queryKey: ['perfil', 'whatsapp'] }),
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível salvar.'),
  });

  return (
    <section className="rounded-card border border-line bg-surface p-5 shadow-card lg:col-span-2">
      <h2 className="flex items-center gap-2 text-base font-semibold text-ink">
        <MessageCircle aria-hidden className="size-5 text-brand" /> WhatsApp
      </h2>
      <p className="mt-1 text-sm text-secondary">
        Receba avisos e atenda chamados pelo WhatsApp. Você pode desvincular quando quiser.
      </p>

      {status.isLoading ? (
        <div className="grid place-items-center py-8 text-muted">
          <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
        </div>
      ) : vinculado ? (
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-controle border border-success/30 bg-success-soft px-4 py-3">
          <Check aria-hidden className="size-5 text-success-ink" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-success-ink">WhatsApp vinculado</p>
            {status.data?.numero && (
              <p className="text-xs text-success-ink/80">Número: {status.data.numero}</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => mDesvincular.mutate()}
            disabled={mDesvincular.isPending}
            className="rounded-controle border border-line-2 bg-surface px-3 py-2 text-sm font-medium text-ink disabled:opacity-60"
          >
            Desvincular
          </button>
        </div>
      ) : vinculo ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-[auto_1fr] sm:items-center">
          <div className="grid place-items-center rounded-card border border-line bg-white p-3">
            <QRCodeSVG value={vinculo.link_wa} size={132} aria-label="QR code para vincular" />
          </div>
          <div className="min-w-0">
            <p className="text-sm text-secondary">
              Abra o WhatsApp e envie a mensagem com o código abaixo (ou escaneie o QR):
            </p>
            <p className="my-2 font-mono text-2xl font-semibold tracking-widest text-brand">
              {vinculo.codigo}
            </p>
            <a
              href={vinculo.link_wa}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-controle bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              <Smartphone aria-hidden className="size-4" /> Abrir no WhatsApp
            </a>
            <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
              <Loader2 aria-hidden className="size-3 animate-spin" /> Aguardando a confirmação pelo
              WhatsApp…
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <label className="flex items-start gap-2 text-sm text-secondary">
            <input
              type="checkbox"
              checked={consentimento}
              onChange={(e) => setConsentimento(e.target.checked)}
              className="mt-0.5 size-4 rounded border-line-2"
            />
            <span>Aceito receber notificações e atender chamados pelo WhatsApp.</span>
          </label>
          <button
            type="button"
            onClick={() => mGerar.mutate()}
            disabled={!consentimento || mGerar.isPending}
            className="mt-3 flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {mGerar.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
            Vincular WhatsApp
          </button>
        </div>
      )}

      {/* Preferências de notificação */}
      <div className="mt-6 border-t border-line pt-4">
        <h3 className="text-sm font-semibold text-ink">Preferências de notificação</h3>
        <div className="mt-3 flex flex-col gap-2">
          <label className="flex items-center justify-between gap-3 text-sm text-ink">
            <span>Receber notificações por e-mail</span>
            <input
              type="checkbox"
              checked={status.data?.notificar_email ?? true}
              disabled={mPreferencia.isPending || status.isLoading}
              onChange={(e) => mPreferencia.mutate({ notificar_email: e.target.checked })}
              className="size-4 rounded border-line-2"
            />
          </label>
          <label className="flex items-center justify-between gap-3 text-sm text-ink">
            <span>Receber notificações por WhatsApp</span>
            <input
              type="checkbox"
              checked={status.data?.opt_in ?? false}
              disabled={mPreferencia.isPending || status.isLoading || !vinculado}
              onChange={(e) => mPreferencia.mutate({ whatsapp_opt_in: e.target.checked })}
              className="size-4 rounded border-line-2 disabled:opacity-50"
            />
          </label>
          {!vinculado && (
            <p className="text-xs text-muted">
              Vincule o WhatsApp para ativar as notificações por esse canal.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
