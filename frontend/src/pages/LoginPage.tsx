import { useEffect, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Clock, FileText, Loader2, ShieldCheck } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { login } from '@/api/auth';
import { obterConfigPublica } from '@/api/usuarios';
import { ControleTema } from '@/components/ControleTema';
import { Marca } from '@/components/Marca';
import { ehErroAPI } from '@/lib/erros';
import { useSessao } from '@/stores/sessao';

const esquema = z.object({
  email: z.string().min(1, 'Informe o e-mail.').email('E-mail inválido.'),
  senha: z.string().min(1, 'Informe a senha.'),
});
type FormLogin = z.infer<typeof esquema>;

interface LocalComOrigem {
  de?: string;
}

/**
 * Login (seção 8.4, F1.3). React Hook Form + Zod; mensagem genérica FE01 e aviso
 * de 429; "Entrar com Google Workspace" só quando `google_sso`; atalho de suporte
 * via WhatsApp/e-mail da config pública.
 */
export function LoginPage() {
  const navegar = useNavigate();
  const local = useLocation();
  const estado = useSessao((e) => e.estado);
  const [erroGeral, setErroGeral] = useState<string | null>(null);

  const { data: config } = useQuery({
    queryKey: ['config-publica'],
    queryFn: obterConfigPublica,
    staleTime: 5 * 60_000,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormLogin>({ resolver: zodResolver(esquema) });

  // Se já autenticado (ex.: voltou ao /login), vai para o destino.
  const destino = (local.state as LocalComOrigem | null)?.de ?? '/dashboard';
  useEffect(() => {
    if (estado === 'autenticado') navegar(destino, { replace: true });
  }, [estado, destino, navegar]);

  async function aoEnviar(dados: FormLogin) {
    setErroGeral(null);
    try {
      await login(dados.email, dados.senha);
      navegar(destino, { replace: true });
    } catch (erro) {
      // FE01: mensagem genérica; 429 vem com código MUITAS_TENTATIVAS do backend.
      setErroGeral(ehErroAPI(erro) ? erro.mensagem : 'Não foi possível entrar. Tente novamente.');
    }
  }

  const suporte = config?.whatsapp_suporte
    ? `https://wa.me/${config.whatsapp_suporte}`
    : config?.email_suporte
      ? `mailto:${config.email_suporte}`
      : null;

  return (
    <div className="min-h-dvh bg-canvas lg:grid lg:grid-cols-2">
      <aside className="relative hidden flex-col overflow-hidden bg-brand-700 p-11 text-white lg:flex">
        <Marca comSub invertido />
        <h2 className="mt-auto max-w-[13ch] text-4xl font-semibold tracking-tight">
          Suporte que resolve de verdade.
        </h2>
        <p className="mt-3 max-w-[40ch] text-sm text-white/80">
          Abra chamados, acompanhe o andamento e encontre respostas rápidas — tudo num só lugar.
        </p>
        <ul className="mt-7 flex flex-col gap-2.5">
          {[
            { Icone: Clock, t: 'Resposta rápida', d: 'SLA por categoria e prioridade' },
            { Icone: ShieldCheck, t: 'Acompanhamento', d: 'Atualizações por portal e e-mail' },
            { Icone: FileText, t: 'Histórico completo', d: 'Todos os seus chamados num painel' },
          ].map(({ Icone, t, d }) => (
            <li
              key={t}
              className="flex items-start gap-3 rounded-card border border-white/15 bg-white/10 p-3.5"
            >
              <span className="grid size-8 place-items-center rounded-lg bg-white/15">
                <Icone aria-hidden className="size-4" />
              </span>
              <span className="leading-tight">
                <span className="block text-sm font-semibold">{t}</span>
                <span className="block text-xs text-white/70">{d}</span>
              </span>
            </li>
          ))}
        </ul>
      </aside>

      <div className="relative flex min-h-dvh flex-col justify-center px-6 py-12 sm:px-12 lg:px-16">
        <div className="absolute right-4 top-4">
          <ControleTema />
        </div>
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Marca />
          </div>
          <h1 className="text-2xl font-semibold text-ink">Bem-vindo de volta</h1>
          <p className="mt-1.5 mb-6 text-sm text-secondary">
            Acesse o portal de suporte com suas credenciais corporativas.
          </p>

          {erroGeral && (
            <div
              role="alert"
              className="mb-4 rounded-controle border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger-ink"
            >
              {erroGeral}
            </div>
          )}

          <form className="flex flex-col gap-4" onSubmit={handleSubmit(aoEnviar)} noValidate>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">E-mail corporativo</span>
              <input
                type="email"
                autoComplete="email"
                placeholder="voce@empresa.com.br"
                aria-invalid={!!errors.email}
                className="rounded-controle border border-line-2 bg-surface px-3 py-3 text-sm text-ink placeholder:text-muted"
                {...register('email')}
              />
              {errors.email && <span className="text-xs text-danger-ink">{errors.email.message}</span>}
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Senha</span>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                aria-invalid={!!errors.senha}
                className="rounded-controle border border-line-2 bg-surface px-3 py-3 text-sm text-ink placeholder:text-muted"
                {...register('senha')}
              />
              {errors.senha && <span className="text-xs text-danger-ink">{errors.senha.message}</span>}
            </label>

            <div className="-mt-1 text-right">
              <Link to="/esqueci-senha" className="text-xs font-medium text-brand">
                Esqueci minha senha
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-1 flex items-center justify-center gap-2 rounded-controle bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {isSubmitting && <Loader2 aria-hidden className="size-4 animate-spin" />}
              {isSubmitting ? 'Entrando…' : 'Entrar no sistema'}
            </button>
          </form>

          {config?.google_sso && (
            <>
              <div className="my-5 flex items-center gap-3 text-xs text-muted">
                <span className="h-px flex-1 bg-line" />
                ou
                <span className="h-px flex-1 bg-line" />
              </div>
              <button
                type="button"
                className="flex w-full items-center justify-center gap-2.5 rounded-controle border border-line-2 bg-surface px-4 py-3 text-sm font-semibold text-ink"
              >
                Entrar com Google Workspace
              </button>
            </>
          )}

          <p className="mt-6 text-center text-xs text-muted">
            Problemas com acesso?{' '}
            {suporte ? (
              <a href={suporte} className="font-medium text-brand">
                Contate o TI
              </a>
            ) : (
              <Link to="/login" className="font-medium text-brand">
                Contate o TI
              </Link>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
