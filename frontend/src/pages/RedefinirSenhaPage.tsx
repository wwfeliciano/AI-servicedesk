import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { redefinirSenha } from '@/api/auth';
import { ControleTema } from '@/components/ControleTema';
import { Marca } from '@/components/Marca';
import { ehErroAPI } from '@/lib/erros';

const esquema = z
  .object({
    senha_nova: z.string().min(8, 'A nova senha deve ter ao menos 8 caracteres.'),
    confirmar: z.string().min(1, 'Confirme a nova senha.'),
  })
  .refine((d) => d.senha_nova === d.confirmar, {
    path: ['confirmar'],
    message: 'As senhas não coincidem.',
  });
type Form = z.infer<typeof esquema>;

export function RedefinirSenhaPage() {
  const navegar = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [concluido, setConcluido] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({ resolver: zodResolver(esquema) });

  async function aoEnviar(dados: Form) {
    setErro(null);
    try {
      await redefinirSenha(token, dados.senha_nova);
      setConcluido(true);
      setTimeout(() => navegar('/login', { replace: true }), 2500);
    } catch (e) {
      setErro(ehErroAPI(e) ? e.mensagem : 'Não foi possível redefinir a senha.');
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
        {concluido ? (
          <div className="rounded-card border border-line bg-surface p-6 text-center shadow-card">
            <span className="mx-auto mb-4 grid size-12 place-items-center rounded-full bg-success-soft text-success-ink">
              <CheckCircle2 aria-hidden className="size-6" />
            </span>
            <h1 className="text-lg font-semibold text-ink">Senha redefinida</h1>
            <p className="mt-2 text-sm text-secondary">
              Você já pode entrar com a nova senha. Redirecionando…
            </p>
          </div>
        ) : !token ? (
          <div className="rounded-card border border-line bg-surface p-6 text-center shadow-card">
            <h1 className="text-lg font-semibold text-ink">Link inválido</h1>
            <p className="mt-2 text-sm text-secondary">
              Este link de redefinição é inválido. Solicite um novo.
            </p>
            <Link
              to="/esqueci-senha"
              className="mt-5 inline-block rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white"
            >
              Esqueci minha senha
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-semibold text-ink">Criar nova senha</h1>
            <p className="mt-1.5 mb-6 text-sm text-secondary">
              Escolha uma nova senha para a sua conta.
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
                <span className="text-xs font-semibold text-secondary">Nova senha</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={!!errors.senha_nova}
                  className="rounded-controle border border-line-2 bg-surface px-3 py-3 text-sm text-ink"
                  {...register('senha_nova')}
                />
                {errors.senha_nova && (
                  <span className="text-xs text-danger-ink">{errors.senha_nova.message}</span>
                )}
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold text-secondary">Confirmar nova senha</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={!!errors.confirmar}
                  className="rounded-controle border border-line-2 bg-surface px-3 py-3 text-sm text-ink"
                  {...register('confirmar')}
                />
                {errors.confirmar && (
                  <span className="text-xs text-danger-ink">{errors.confirmar.message}</span>
                )}
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 rounded-controle bg-brand px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
              >
                {isSubmitting && <Loader2 aria-hidden className="size-4 animate-spin" />}
                Redefinir senha
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
