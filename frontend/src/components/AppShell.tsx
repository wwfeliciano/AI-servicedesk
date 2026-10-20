import { useState } from 'react';
import { LogOut, Menu, X } from 'lucide-react';
import { Outlet, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { logout } from '@/api/auth';
import { ControleTema } from '@/components/ControleTema';
import { Marca } from '@/components/Marca';
import { MenuLateral } from '@/components/MenuLateral';
import { cx } from '@/lib/formato';

/**
 * Casca da aplicação (seção 8.3): menu lateral fixo no desktop; no celular vira
 * gaveta aberta pela barra superior. O conteúdo das rotas entra no <Outlet/>.
 */
export function AppShell() {
  const [gaveta, setGaveta] = useState(false);
  const navegar = useNavigate();

  async function sair() {
    await logout();
    toast.success('Sessão encerrada.');
    navegar('/login', { replace: true });
  }

  return (
    <div className="min-h-dvh bg-canvas lg:grid lg:grid-cols-[248px_1fr]">
      {/* Sidebar desktop */}
      <aside className="hidden lg:block">
        <div className="sticky top-0 h-dvh">
          <MenuLateral />
        </div>
      </aside>

      {/* Gaveta mobile */}
      {gaveta && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink/50"
            onClick={() => setGaveta(false)}
            aria-hidden
          />
          <div className="absolute inset-y-0 left-0 w-[248px]">
            <MenuLateral onNavegar={() => setGaveta(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-line bg-surface px-4 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setGaveta((v) => !v)}
              aria-label={gaveta ? 'Fechar navegação' : 'Abrir navegação'}
              aria-expanded={gaveta}
              className="grid size-9 place-items-center rounded-controle border border-line text-secondary lg:hidden"
            >
              {gaveta ? <X aria-hidden className="size-4" /> : <Menu aria-hidden className="size-4" />}
            </button>
            <div className="lg:hidden">
              <Marca comSub={false} />
            </div>
            <nav aria-label="Trilha" className="hidden text-xs text-muted lg:block">
              Portal do colaborador <span className="mx-2">/</span>
              <span className="font-medium text-secondary">Visão geral</span>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <ControleTema />
            <button
              type="button"
              onClick={() => void sair()}
              className="grid size-9 place-items-center rounded-controle border border-line text-secondary transition hover:border-danger hover:text-danger"
              aria-label="Sair"
              title="Sair"
            >
              <LogOut aria-hidden className="size-4" />
            </button>
          </div>
        </header>

        <main className={cx('flex-1 px-4 py-6 lg:px-8 lg:py-8')}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
