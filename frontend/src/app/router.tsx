import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppShell } from '@/components/AppShell';
import { RequirePerfil } from '@/components/RequirePerfil';
import { AdminUsuariosPage } from '@/pages/AdminUsuariosPage';
import { AdminIntegracoesPage } from '@/pages/AdminIntegracoesPage';
import { BaseConhecimentoPage } from '@/pages/BaseConhecimentoPage';
import { ChamadoDetalhePage } from '@/pages/ChamadoDetalhePage';
import { ChamadosPage } from '@/pages/ChamadosPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { EsqueciSenhaPage } from '@/pages/EsqueciSenhaPage';
import { LoginPage } from '@/pages/LoginPage';
import { NaoEncontradaPage } from '@/pages/NaoEncontradaPage';
import { NotificacoesPage } from '@/pages/NotificacoesPage';
import { NovoChamadoPage } from '@/pages/NovoChamadoPage';
import { PerfilPage } from '@/pages/PerfilPage';
import { RedefinirSenhaPage } from '@/pages/RedefinirSenhaPage';

/**
 * Rotas da SPA (seção 8.1, 8.4). O Login fica fora do AppShell; as demais são
 * protegidas por perfil (stub na F0.5). As telas estão vazias — ganham conteúdo
 * nas fases seguintes.
 */
export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/esqueci-senha', element: <EsqueciSenhaPage /> },
  { path: '/redefinir-senha', element: <RedefinirSenhaPage /> },
  {
    element: (
      <RequirePerfil>
        <AppShell />
      </RequirePerfil>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'chamados', element: <ChamadosPage /> },
      { path: 'chamados/novo', element: <NovoChamadoPage /> },
      { path: 'chamados/:id', element: <ChamadoDetalhePage /> },
      { path: 'base-conhecimento', element: <BaseConhecimentoPage /> },
      { path: 'notificacoes', element: <NotificacoesPage /> },
      { path: 'perfil', element: <PerfilPage /> },
      {
        path: 'admin/usuarios',
        element: (
          <RequirePerfil perfis={['ADMIN']}>
            <AdminUsuariosPage />
          </RequirePerfil>
        ),
      },
      {
        path: 'admin/integracoes',
        element: (
          <RequirePerfil perfis={['ADMIN']}>
            <AdminIntegracoesPage />
          </RequirePerfil>
        ),
      },
    ],
  },
  { path: '*', element: <NaoEncontradaPage /> },
]);
