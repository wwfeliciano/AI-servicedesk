import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, Plus, Search, UserPlus, X } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import {
  atualizarUsuario,
  cadastrarUsuario,
  listarUsuarios,
  type FiltroUsuarios,
  type UsuarioDetalhe,
} from '@/api/usuarios';
import { PaginaVazia } from '@/components/PaginaVazia';
import { ehErroAPI } from '@/lib/erros';
import { cx, dataCurta } from '@/lib/formato';
import type { Perfil } from '@/types/dominio';

const PERFIS: Perfil[] = ['CLIENTE', 'ANALISTA', 'ADMIN'];
const ROTULO: Record<Perfil, string> = {
  CLIENTE: 'Cliente',
  ANALISTA: 'Analista',
  ADMIN: 'Administrador',
};
const PAGE_SIZE = 10;

export function AdminUsuariosPage() {
  const cliente = useQueryClient();
  const [q, setQ] = useState('');
  const [perfil, setPerfil] = useState<Perfil | ''>('');
  const [page, setPage] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [editando, setEditando] = useState<UsuarioDetalhe | null>(null);

  const filtro: FiltroUsuarios = {
    page,
    page_size: PAGE_SIZE,
    ...(q ? { q } : {}),
    ...(perfil ? { perfil } : {}),
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['usuarios', filtro],
    queryFn: () => listarUsuarios(filtro),
    placeholderData: keepPreviousData,
  });

  const toggle = useMutation({
    mutationFn: (v: { id: number; ativo: boolean }) => atualizarUsuario(v.id, { ativo: v.ativo }),
    onSuccess: (u) => {
      toast.success(u.ativo ? 'Usuário ativado.' : 'Usuário desativado.');
      void cliente.invalidateQueries({ queryKey: ['usuarios'] });
    },
    onError: (e) => toast.error(ehErroAPI(e) ? e.mensagem : 'Não foi possível alterar.'),
  });

  const totalPaginas = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <PaginaVazia
      eyebrow="Administração"
      titulo="Usuários"
      descricao="Cadastro e gestão de usuários do portal."
    >
      {/* Filtros + ação */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex min-w-56 flex-1 items-center gap-2 rounded-controle border border-line-2 bg-surface px-3">
          <Search aria-hidden className="size-4 text-muted" />
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            placeholder="Buscar por nome ou e-mail…"
            aria-label="Buscar usuários"
            className="w-full bg-transparent py-2.5 text-sm text-ink placeholder:text-muted focus:outline-none"
          />
        </div>
        <select
          value={perfil}
          onChange={(e) => {
            setPerfil(e.target.value as Perfil | '');
            setPage(1);
          }}
          aria-label="Filtrar por perfil"
          className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
        >
          <option value="">Todos os perfis</option>
          {PERFIS.map((p) => (
            <option key={p} value={p}>
              {ROTULO[p]}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setModalAberto(true)}
          className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          <Plus aria-hidden className="size-4" /> Novo usuário
        </button>
      </div>

      {/* Tabela */}
      <div className="overflow-hidden rounded-card border border-line bg-surface">
        {isLoading ? (
          <div className="grid place-items-center py-16 text-muted">
            <Loader2 aria-label="Carregando" className="size-5 animate-spin text-brand" />
          </div>
        ) : isError ? (
          <div className="grid place-items-center gap-3 py-16 text-center">
            <p className="text-sm text-secondary">Não foi possível carregar os usuários.</p>
            <button
              type="button"
              onClick={() => void refetch()}
              className="rounded-controle border border-line-2 px-3 py-2 text-sm font-medium text-ink"
            >
              Tentar novamente
            </button>
          </div>
        ) : data && data.items.length > 0 ? (
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-2 text-[10px] tracking-wide text-muted">
                <th className="px-5 py-3 font-semibold">NOME</th>
                <th className="px-5 py-3 font-semibold">PERFIL</th>
                <th className="px-5 py-3 font-semibold">SITUAÇÃO</th>
                <th className="px-5 py-3 font-semibold">CADASTRO</th>
                <th className="px-5 py-3 font-semibold">AÇÕES</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((u: UsuarioDetalhe) => (
                <tr key={u.id_usuario} className="border-t border-line">
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-ink">{u.nome}</p>
                    <p className="text-xs text-muted">{u.email}</p>
                  </td>
                  <td className="px-5 py-3.5 text-sm text-secondary">
                    {ROTULO[u.tipo_perfil as Perfil] ?? u.tipo_perfil}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={cx(
                        'rounded-md px-2 py-0.5 text-xs font-semibold',
                        u.ativo
                          ? 'bg-success-soft text-success-ink'
                          : 'bg-neutral-soft text-neutral-ink',
                      )}
                    >
                      {u.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-sm text-muted">{dataCurta(u.data_cadastro)}</td>
                  <td className="px-5 py-3.5">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setEditando(u)}
                        className="rounded-controle border border-line-2 px-2.5 py-1 text-xs font-medium text-ink"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => toggle.mutate({ id: u.id_usuario, ativo: !u.ativo })}
                        disabled={toggle.isPending}
                        className={cx(
                          'rounded-controle border px-2.5 py-1 text-xs font-medium disabled:opacity-50',
                          u.ativo
                            ? 'border-danger/40 text-danger-ink'
                            : 'border-success/40 text-success-ink',
                        )}
                      >
                        {u.ativo ? 'Desativar' : 'Ativar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="grid place-items-center py-16 text-center text-sm text-muted">
            Nenhum usuário encontrado com esse filtro.
          </div>
        )}
      </div>

      {/* Paginação */}
      {data && data.total > 0 && (
        <div className="mt-4 flex items-center justify-between text-sm text-muted">
          <span>
            {data.total} usuário{data.total === 1 ? '' : 's'} · página {data.page} de {totalPaginas}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-controle border border-line-2 px-3 py-1.5 font-medium text-ink disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= totalPaginas}
              onClick={() => setPage((p) => Math.min(totalPaginas, p + 1))}
              className="rounded-controle border border-line-2 px-3 py-1.5 font-medium text-ink disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        </div>
      )}

      {modalAberto && <ModalNovoUsuario onFechar={() => setModalAberto(false)} />}
      {editando && <ModalEditarUsuario usuario={editando} onFechar={() => setEditando(null)} />}
    </PaginaVazia>
  );
}

const esquema = z.object({
  nome: z.string().min(1, 'Informe o nome.').max(150),
  email: z.string().min(1, 'Informe o e-mail.').email('E-mail inválido.'),
  senha: z.string().min(8, 'A senha deve ter ao menos 8 caracteres.'),
  tipo_perfil: z.enum(['CLIENTE', 'ANALISTA', 'ADMIN']),
  cargo: z.string().max(100).optional(),
});
type FormNovo = z.infer<typeof esquema>;

function ModalNovoUsuario({ onFechar }: { onFechar: () => void }) {
  const cliente = useQueryClient();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormNovo>({
    resolver: zodResolver(esquema),
    defaultValues: { tipo_perfil: 'CLIENTE' },
  });

  const mutacao = useMutation({
    mutationFn: cadastrarUsuario,
    onSuccess: (u) => {
      toast.success(`Usuário ${u.nome} cadastrado.`);
      void cliente.invalidateQueries({ queryKey: ['usuarios'] });
      onFechar();
    },
    onError: (erro) => {
      // Erros de campo (EMAIL_DUPLICADO → campos.email; senha fraca → campos.senha).
      if (ehErroAPI(erro)) {
        if (erro.campos?.email || erro.codigo === 'EMAIL_DUPLICADO') {
          setError('email', { message: erro.campos?.email ?? erro.mensagem });
        } else if (erro.campos?.senha) {
          setError('senha', { message: erro.campos.senha });
        } else {
          toast.error(erro.mensagem);
        }
      } else {
        toast.error('Não foi possível cadastrar o usuário.');
      }
    },
  });

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onFechar} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Novo usuário"
        className="relative w-full max-w-lg rounded-card-lg border border-line bg-surface shadow-pop"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="flex items-center gap-2 text-base font-semibold text-ink">
            <UserPlus aria-hidden className="size-4 text-brand" /> Novo usuário
          </h2>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="grid size-8 place-items-center rounded-controle text-muted hover:bg-surface-2"
          >
            <X aria-hidden className="size-4" />
          </button>
        </div>

        <form
          className="flex flex-col gap-4 px-5 py-5"
          onSubmit={handleSubmit((d) =>
            mutacao.mutate({
              nome: d.nome,
              email: d.email,
              senha: d.senha,
              tipo_perfil: d.tipo_perfil,
              ...(d.cargo ? { cargo: d.cargo } : {}),
            }),
          )}
          noValidate
        >
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-secondary">Nome</span>
            <input
              className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
              aria-invalid={!!errors.nome}
              {...register('nome')}
            />
            {errors.nome && <span className="text-xs text-danger-ink">{errors.nome.message}</span>}
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-secondary">E-mail</span>
            <input
              type="email"
              className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
              aria-invalid={!!errors.email}
              {...register('email')}
            />
            {errors.email && <span className="text-xs text-danger-ink">{errors.email.message}</span>}
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Senha</span>
              <input
                type="password"
                autoComplete="new-password"
                className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
                aria-invalid={!!errors.senha}
                {...register('senha')}
              />
              {errors.senha && (
                <span className="text-xs text-danger-ink">{errors.senha.message}</span>
              )}
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Perfil</span>
              <select
                className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
                {...register('tipo_perfil')}
              >
                {PERFIS.map((p) => (
                  <option key={p} value={p}>
                    {ROTULO[p]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-secondary">Cargo (opcional)</span>
            <input
              className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
              {...register('cargo')}
            />
          </label>

          <div className="mt-1 flex justify-end gap-2">
            <button
              type="button"
              onClick={onFechar}
              className="rounded-controle border border-line-2 px-4 py-2.5 text-sm font-medium text-ink"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={mutacao.isPending}
              className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {mutacao.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
              Cadastrar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


const esquemaEdicao = z.object({
  nome: z.string().min(1, 'Informe o nome.').max(150),
  cargo: z.string().max(100).optional(),
  tipo_perfil: z.enum(['CLIENTE', 'ANALISTA', 'ADMIN']),
});
type FormEdicao = z.infer<typeof esquemaEdicao>;

function ModalEditarUsuario({
  usuario,
  onFechar,
}: {
  usuario: UsuarioDetalhe;
  onFechar: () => void;
}) {
  const cliente = useQueryClient();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormEdicao>({
    resolver: zodResolver(esquemaEdicao),
    defaultValues: {
      nome: usuario.nome,
      cargo: usuario.cargo ?? '',
      tipo_perfil: usuario.tipo_perfil as Perfil,
    },
  });

  const mutacao = useMutation({
    mutationFn: (d: FormEdicao) =>
      atualizarUsuario(usuario.id_usuario, {
        nome: d.nome,
        cargo: d.cargo ?? '',
        tipo_perfil: d.tipo_perfil,
      }),
    onSuccess: (u) => {
      toast.success(`Usuário ${u.nome} atualizado.`);
      void cliente.invalidateQueries({ queryKey: ['usuarios'] });
      onFechar();
    },
    onError: (erro) => {
      if (ehErroAPI(erro) && erro.campos) {
        for (const [campo, msg] of Object.entries(erro.campos)) {
          if (campo === 'nome' || campo === 'tipo_perfil') {
            setError(campo, { message: msg });
          }
        }
        if (!erro.campos.nome && !erro.campos.tipo_perfil) toast.error(erro.mensagem);
      } else {
        toast.error('Não foi possível atualizar o usuário.');
      }
    },
  });

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onFechar} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Editar usuário"
        className="relative w-full max-w-lg rounded-card-lg border border-line bg-surface shadow-pop"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">Editar usuário</h2>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="grid size-8 place-items-center rounded-controle text-muted hover:bg-surface-2"
          >
            <X aria-hidden className="size-4" />
          </button>
        </div>
        <form className="flex flex-col gap-4 px-5 py-5" onSubmit={handleSubmit((d) => mutacao.mutate(d))} noValidate>
          <p className="text-xs text-muted">{usuario.email}</p>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-secondary">Nome</span>
            <input
              className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
              aria-invalid={!!errors.nome}
              {...register('nome')}
            />
            {errors.nome && <span className="text-xs text-danger-ink">{errors.nome.message}</span>}
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Cargo</span>
              <input
                className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
                {...register('cargo')}
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-secondary">Perfil</span>
              <select
                className="rounded-controle border border-line-2 bg-surface px-3 py-2.5 text-sm text-ink"
                {...register('tipo_perfil')}
              >
                {PERFIS.map((p) => (
                  <option key={p} value={p}>
                    {ROTULO[p]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="mt-1 flex justify-end gap-2">
            <button type="button" onClick={onFechar} className="rounded-controle border border-line-2 px-4 py-2.5 text-sm font-medium text-ink">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={mutacao.isPending}
              className="flex items-center gap-2 rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {mutacao.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
