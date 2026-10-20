import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { Navigate, useLocation } from 'react-router-dom';

import type { Perfil } from '@/types/dominio';
import { useSessao } from '@/stores/sessao';

interface Props {
  perfis?: Perfil[];
  children: ReactNode;
}

/** Tela de carregamento enquanto a sessão é restaurada (evita piscar o /login). */
function Carregando() {
  return (
    <div className="grid min-h-dvh place-items-center bg-canvas text-muted">
      <Loader2 aria-label="Carregando" className="size-6 animate-spin text-brand" />
    </div>
  );
}

/**
 * Proteção de rota por perfil (seção 8.1). Aguarda a restauração da sessão; se
 * anônimo, manda para /login (guardando a origem); se autenticado sem o perfil
 * exigido, volta ao Dashboard.
 */
export function RequirePerfil({ perfis, children }: Props) {
  const estado = useSessao((e) => e.estado);
  const usuario = useSessao((e) => e.usuario);
  const local = useLocation();

  if (estado === 'verificando') return <Carregando />;
  if (estado === 'anonimo' || !usuario) {
    return <Navigate to="/login" replace state={{ de: local.pathname }} />;
  }
  if (perfis && !perfis.includes(usuario.tipo_perfil)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
