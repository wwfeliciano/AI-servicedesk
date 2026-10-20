import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { z } from 'zod';

import { esqueciSenha } from '@/api/auth';
import { ControleTema } from '@/components/ControleTema';
import { Marca } from '@/components/Marca';
import { ehErroAPI } from '@/lib/erros';

const esquema = z.object({
  email: z.string().min(1, 'Informe o e-mail.').email('E-mail inválido.'),
});
type Form = z.infer<typeof esquema>;

export function EsqueciSenhaPage() {
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({ resolver: zodResolver(esquema) });

  async function aoEnviar(dados: Form) {
    setErro(null);
    try {
      const msg = await esqueciSenha(dados.email);
      setMensagem(msg);
    } catch (e) {
      setErro(ehErroAPI(e) ? e.mensagem : 'Não foi possível enviar o e-mail.');
    }
  }

  return (
    <div className="grid min-h-dvh place-items-center bg-canvas px-6 py-12">
      <div className="absolute right-4 top-4">
        <ControleTema />
      </div>
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <Marca />
        </div>
        {mensagem ? (
          <div className="rounded-card border border-line bg-surface p-6 text-center shadow-card">
            <span className="mx-auto mb-4 grid size-12 place-items-center rounded-full bg-success-soft text-success-ink">
              <CheckCircle2 aria-hidden className="size-6" />
            </span>
            <h1 className="text-lg font-semibold text-ink">Verifique seu e-mail</h1>
            <p className="mt-2 text-sm text-secondary">{mensagem}</p>
            <Link
              to="/login"
              className="mt-5 inline-block rounded-controle border border-line-2 px-4 py-2.5 text-sm font-medium text-ink"
            >
              Voltar ao login
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-semibold text-ink">Esqueci minha senha</h1>
            <p className="mt-1.5 mb-6 text-sm text-secondary">
              Informe seu e-mail corporativo e enviaremos um link para redefinir a senha.
            </p>
            {erro && (
              <div
                role="alert"
                className="mb-4 rounded-controle border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger-ink"
              >
                {erro}
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
                {errors.email && (
                  <span className="text-xs text-danger-ink">{errors.email.message}</span>
                )}
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 rounded-controle bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
              >
                {isSubmitting && <Loader2 aria-hidden className="size-4 animate-spin" />}
                Enviar link
              </button>
            </form>
            <p className="mt-6 text-center text-xs text-muted">
              Lembrou a senha?{' '}
              <Link to="/login" className="font-medium text-brand">
                Voltar ao login
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
