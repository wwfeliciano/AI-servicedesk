import { create } from 'zustand';

import type { Severidade } from '@/types/dominio';

/**
 * Rascunho do wizard de Novo Chamado (seção 8.1): estado do cliente em memória
 * (Zustand). Sair da tela descarta — não persiste em localStorage. Os anexos
 * selecionados ficam aqui (objetos File) e são enviados após criar o chamado.
 */
interface EstadoRascunho {
  etapa: number; // 0 Categoria · 1 Prioridade · 2 Detalhes
  id_categoria: number | null;
  severidade: Severidade;
  titulo: string;
  descricao: string;
  anexos: File[];
  definir: (dados: Partial<Omit<EstadoRascunho, 'definir' | 'limpar'>>) => void;
  limpar: () => void;
}

const INICIAL = {
  etapa: 0,
  id_categoria: null,
  severidade: 'BAIXA' as Severidade,
  titulo: '',
  descricao: '',
  anexos: [] as File[],
};

export const useRascunhoChamado = create<EstadoRascunho>((set) => ({
  ...INICIAL,
  definir: (dados) => set(dados),
  limpar: () => set({ ...INICIAL, anexos: [] }),
}));
