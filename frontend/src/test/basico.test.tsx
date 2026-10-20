import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StatusBadge } from '@/components/StatusBadge';
import { iniciais, saudacao } from '@/lib/formato';

describe('StatusBadge (seção 6.1)', () => {
  it('mostra "Aberto" para NOVO e PENDENTE', () => {
    const { rerender } = render(<StatusBadge status="NOVO" />);
    expect(screen.getByText('Aberto')).toBeInTheDocument();
    rerender(<StatusBadge status="PENDENTE" />);
    expect(screen.getByText('Aberto')).toBeInTheDocument();
  });

  it('mapeia ATRIBUIDO, CONCLUIDO e FECHADO aos rótulos da tela', () => {
    const { rerender } = render(<StatusBadge status="ATRIBUIDO" />);
    expect(screen.getByText('Em andamento')).toBeInTheDocument();
    rerender(<StatusBadge status="CONCLUIDO" />);
    expect(screen.getByText('Resolvido')).toBeInTheDocument();
    rerender(<StatusBadge status="FECHADO" />);
    expect(screen.getByText('Encerrado')).toBeInTheDocument();
  });
});

describe('formato', () => {
  it('gera iniciais a partir do nome', () => {
    expect(iniciais('Ana Lima')).toBe('AL');
    expect(iniciais('Rafael')).toBe('R');
  });

  it('sauda conforme o horário', () => {
    expect(saudacao(new Date('2026-10-17T09:00:00'))).toBe('Bom dia');
    expect(saudacao(new Date('2026-10-17T14:00:00'))).toBe('Boa tarde');
    expect(saudacao(new Date('2026-10-17T21:00:00'))).toBe('Boa noite');
  });
});
