import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

/** Data curta dos cards: dd/MM/yy (seção 8.1). */
export function dataCurta(data: Date | string): string {
  const d = typeof data === 'string' ? new Date(data) : data;
  return format(d, 'dd/MM/yy', { locale: ptBR });
}

/** Tempo relativo curto do Dashboard: agora, 5 min atrás, 2 h atrás, 15 d atrás. */
export function tempoRelativoCurto(data: Date | string, agora: Date = new Date()): string {
  const d = typeof data === 'string' ? new Date(data) : data;
  const seg = Math.max(0, Math.floor((agora.getTime() - d.getTime()) / 1000));
  if (seg < 60) return 'agora';
  const min = Math.floor(seg / 60);
  if (min < 60) return `${min} min atrás`;
  const horas = Math.floor(min / 60);
  if (horas < 24) return `${horas} h atrás`;
  const dias = Math.floor(horas / 24);
  return `${dias} d atrás`;
}

/** Iniciais do bloco de usuário do menu (ex.: "Ana Lima" → "AL"). */
export function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return '?';
  const primeira = partes[0]?.[0] ?? '';
  const ultima = partes.length > 1 ? (partes[partes.length - 1]?.[0] ?? '') : '';
  return (primeira + ultima).toUpperCase();
}

/** Saudação por faixa de horário (Dashboard, seção 8.4). */
export function saudacao(agora: Date = new Date()): string {
  const h = agora.getHours();
  if (h >= 5 && h < 12) return 'Bom dia';
  if (h >= 12 && h < 18) return 'Boa tarde';
  return 'Boa noite';
}

/** Primeiro nome. */
export function primeiroNome(nome: string): string {
  return nome.trim().split(/\s+/)[0] ?? nome;
}

/** Junta classes, descartando valores falsos. */
export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}
