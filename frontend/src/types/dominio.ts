/** Perfis de acesso (dicionário de dados: sem acento, em português). */
export type Perfil = 'CLIENTE' | 'ANALISTA' | 'ADMIN';

/** Status do chamado — enum do banco (migration 0001, seção 5.2). */
export type StatusChamado = 'NOVO' | 'PENDENTE' | 'ATRIBUIDO' | 'CONCLUIDO' | 'FECHADO';

/** Severidade (o passo da tela se chama "Prioridade"; o campo enviado é severidade). */
export type Severidade = 'BAIXA' | 'MEDIA' | 'ALTA' | 'CRITICO';

/**
 * Grupos de status das abas e indicadores (seção 6.1):
 * abertos = NOVO+PENDENTE · em_andamento = ATRIBUIDO · resolvidos = CONCLUIDO ·
 * encerrados = FECHADO.
 */
export type GrupoStatus = 'abertos' | 'em_andamento' | 'resolvidos' | 'encerrados';

/** Usuário autenticado (sessão em memória; preenchido de verdade na F1). */
export interface Usuario {
  id_usuario: number;
  nome: string;
  email: string;
  tipo_perfil: Perfil;
  cargo?: string;
}
