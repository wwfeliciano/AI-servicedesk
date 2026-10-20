import { api } from '@/api/client';
import type { components } from '@/api/schema';
import type { ErroAPI } from '@/lib/erros';

export type SlaMes = components['schemas']['SlaMesSaida'];

function lancar(erro: unknown): never {
  throw (erro ?? { codigo: 'ERRO', mensagem: 'Falha de rede.' }) as ErroAPI;
}

/** SLA do mês: percentual de chamados concluídos no prazo (F7.2). */
export async function obterSlaDoMes(): Promise<SlaMes> {
  const { data, error } = await api.GET('/api/sla/mes', {});
  if (error || !data) lancar(error);
  return data;
}
