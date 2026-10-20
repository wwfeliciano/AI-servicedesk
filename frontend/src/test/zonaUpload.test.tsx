import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ZonaUpload } from '@/components/ZonaUpload';

function arquivo(nome: string, tipo: string, tamanho = 10): File {
  const f = new File([new Uint8Array(tamanho)], nome, { type: tipo });
  return f;
}

function soltar(elemento: Element, arquivos: File[]) {
  fireEvent.drop(elemento, { dataTransfer: { files: arquivos } });
}

describe('ZonaUpload (F3.3)', () => {
  it('entrega arquivos válidos (PNG) ao pai', async () => {
    const onArquivos = vi.fn();
    render(<ZonaUpload onArquivos={onArquivos} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, arquivo('ok.png', 'image/png'));
    expect(onArquivos).toHaveBeenCalledTimes(1);
    expect(onArquivos.mock.calls[0][0][0].name).toBe('ok.png');
  });

  it('rejeita tipo não permitido (via drop) e não chama o pai', async () => {
    const onArquivos = vi.fn();
    render(<ZonaUpload onArquivos={onArquivos} />);
    const zona = screen.getByRole('button', { name: /adicionar arquivo/i });
    soltar(zona, [arquivo('x.txt', 'text/plain')]);
    expect(onArquivos).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent(/tipo não permitido/i);
  });

  it('rejeita arquivo acima de 10 MB (via drop)', async () => {
    const onArquivos = vi.fn();
    render(<ZonaUpload onArquivos={onArquivos} />);
    const zona = screen.getByRole('button', { name: /adicionar arquivo/i });
    soltar(zona, [arquivo('grande.pdf', 'application/pdf', 10 * 1024 * 1024 + 1)]);
    expect(onArquivos).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent(/10 MB/);
  });
});
