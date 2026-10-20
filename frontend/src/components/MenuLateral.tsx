import { useQuery } from '@tanstack/react-query';
import { NavLink } from 'react-router-dom';

import { contarNaoLidas } from '@/api/notificacoes';
import type { Perfil } from '@/types/dominio';
import { ITENS_NAV } from '@/components/navegacao';
import { Marca } from '@/components/Marca';
import { useSessao } from '@/stores/sessao';
import { cx, iniciais } from '@/lib/formato';

interface Props {
  /** Fecha a gaveta ao navegar (mobile). */
  onNavegar?: () => void;
}

/**
 * Menu lateral (seção 8.3): sidebar branca, bloco do usuário com iniciais, itens
 * filtrados por perfil, chip "Novo", entrada "Assistente IA" marcada "em breve" e
 * contador de notificações não lidas (polling de 30 s, seção 8.4).
 */
export function MenuLateral({ onNavegar }: Props) {
  const usuario = useSessao((e) => e.usuario);
  const perfil: Perfil = usuario?.tipo_perfil ?? 'CLIENTE';
  const itens = ITENS_NAV.filter((i) => !i.perfis || i.perfis.includes(perfil));

  const naoLidas = useQuery({
    queryKey: ['notificacoes', 'contagem'],
    queryFn: contarNaoLidas,
    refetchInterval: 30_000, // polling 30 s (B11)
    enabled: !!usuario,
  });
  const totalNaoLidas = naoLidas.data ?? 0;

  return (
    <div className="flex h-full flex-col border-r border-line bg-sidebar px-4 py-6">
      <div className="px-2">
        <Marca />
      </div>

      <p className="mt-8 mb-3 px-3 text-[10px] font-semibold tracking-[0.15em] text-muted">
        SEU ESPAÇO
      </p>

      <nav className="flex flex-1 flex-col gap-1">
        {itens.map((item) => {
          const Icone = item.icone;
          if (item.emBreve) {
            return (
              <span
                key={item.para}
                aria-disabled
                title="Em breve"
                className="flex cursor-not-allowed items-center gap-3 rounded-controle px-3 py-2.5 text-sm font-medium text-muted/70"
              >
                <Icone aria-hidden className="size-[18px]" />
                {item.rotulo}
                <span className="ml-auto rounded bg-brand-soft px-1.5 py-0.5 text-[9px] font-semibold tracking-wide text-brand-soft-ink">
                  EM BREVE
                </span>
              </span>
            );
          }
          return (
            <NavLink
              key={item.para}
              to={item.para}
              end={item.para === '/chamados'}
              onClick={onNavegar}
              className={({ isActive }) =>
                cx(
                  'flex items-center gap-3 rounded-controle px-3 py-2.5 text-sm font-medium transition',
                  isActive
                    ? 'bg-sidebar-active-bg text-sidebar-active-ink'
                    : 'text-secondary hover:bg-surface-2',
                )
              }
            >
              <Icone aria-hidden className="size-[18px]" />
              {item.rotulo}
              {item.novo && (
                <span className="ml-auto rounded bg-brand-soft px-1.5 py-0.5 text-[9px] font-semibold tracking-wide text-brand-soft-ink">
                  NOVO
                </span>
              )}
              {item.contadorNotificacoes && totalNaoLidas > 0 && (
                <span className="ml-auto grid min-w-5 place-items-center rounded-full bg-danger px-1.5 text-[10px] font-semibold text-white">
                  {totalNaoLidas > 99 ? '99+' : totalNaoLidas}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <NavLink
        to="/perfil"
        onClick={onNavegar}
        className="mt-4 flex items-center gap-3 border-t border-line pt-4"
      >
        <span className="grid size-9 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-soft-ink">
          {iniciais(usuario?.nome ?? '?')}
        </span>
        <span className="min-w-0 leading-tight">
          <span className="block truncate text-sm font-semibold text-ink">
            {usuario?.nome ?? 'Visitante'}
          </span>
          <span className="block truncate text-xs text-muted">
            {usuario?.cargo ?? 'Perfil'}
          </span>
        </span>
      </NavLink>
    </div>
  );
}
