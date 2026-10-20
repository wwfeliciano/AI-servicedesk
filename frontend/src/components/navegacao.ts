import {
  Bell,
  BookOpen,
  LayoutGrid,
  type LucideIcon,
  MessageCircle,
  Sparkles,
  Ticket,
  UserCog,
} from 'lucide-react';

import type { Perfil } from '@/types/dominio';

export interface ItemNav {
  rotulo: string;
  para: string;
  icone: LucideIcon;
  /** Perfis que veem o item; ausente = todos os autenticados. */
  perfis?: Perfil[];
  /** Marca "Novo" (chip) ao lado do item. */
  novo?: boolean;
  /** Entrada de visão de produto ainda não implementada (fase futura). */
  emBreve?: boolean;
  /** Exibe o contador de notificações não lidas (polling). */
  contadorNotificacoes?: boolean;
}

/**
 * Itens do menu lateral (seção 8.3/8.4). O "Assistente IA" é visão de produto
 * (ADR 2026-10-17): aparece marcado "em breve" e desabilitado até a fase de IA.
 * As rotas levam a páginas vazias na F0.5.
 */
export const ITENS_NAV: ItemNav[] = [
  { rotulo: 'Dashboard', para: '/dashboard', icone: LayoutGrid },
  { rotulo: 'Meus Chamados', para: '/chamados', icone: Ticket },
  { rotulo: 'Novo Chamado', para: '/chamados/novo', icone: Sparkles, novo: true },
  { rotulo: 'Base de Conhecimento', para: '/base-conhecimento', icone: BookOpen },
  { rotulo: 'Assistente IA', para: '/assistente', icone: Sparkles, emBreve: true },
  { rotulo: 'Notificações', para: '/notificacoes', icone: Bell, contadorNotificacoes: true },
  { rotulo: 'Usuários', para: '/admin/usuarios', icone: UserCog, perfis: ['ADMIN'] },
  { rotulo: 'Integrações', para: '/admin/integracoes', icone: MessageCircle, perfis: ['ADMIN'] },
];
