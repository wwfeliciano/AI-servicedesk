import { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';

import { MAX_BYTES, MIMES_ACEITOS } from '@/api/anexos';
import { cx } from '@/lib/formato';

interface Props {
  /** Chamado quando arquivos válidos são escolhidos. */
  onArquivos: (arquivos: File[]) => void;
  /** Desabilita a zona (ex.: limite atingido ou enviando). */
  desabilitado?: boolean;
  /** Mensagem de rodapé (ex.: "3 de 5 anexos"). */
  dica?: string;
}

const EXT_ACEITAS = '.png,.jpg,.jpeg,.pdf';

/** Valida tipo (PNG/JPG/PDF) e tamanho (≤10 MB) no cliente, espelhando B9/B10. */
function validar(arquivos: File[]): { ok: File[]; erro: string | null } {
  const ok: File[] = [];
  for (const a of arquivos) {
    if (!(MIMES_ACEITOS as readonly string[]).includes(a.type)) {
      return { ok: [], erro: `"${a.name}": tipo não permitido (use PNG, JPG ou PDF).` };
    }
    if (a.size > MAX_BYTES) {
      return { ok: [], erro: `"${a.name}": acima de 10 MB.` };
    }
    ok.push(a);
  }
  return { ok, erro: null };
}

/**
 * Zona de upload reutilizável (seção 8.3): arrastar/soltar ou clicar; valida tipo
 * e tamanho no cliente e entrega os arquivos válidos ao pai. O envio em si é
 * responsabilidade de quem usa (wizard acumula; detalhe envia na hora).
 */
export function ZonaUpload({ onArquivos, desabilitado = false, dica }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [sobre, setSobre] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function receber(lista: FileList | null) {
    setErro(null);
    if (!lista || lista.length === 0) return;
    const { ok, erro } = validar([...lista]);
    if (erro) {
      setErro(erro);
      return;
    }
    onArquivos(ok);
  }

  return (
    <div>
      <button
        type="button"
        disabled={desabilitado}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!desabilitado) setSobre(true);
        }}
        onDragLeave={() => setSobre(false)}
        onDrop={(e) => {
          e.preventDefault();
          setSobre(false);
          if (!desabilitado) receber(e.dataTransfer.files);
        }}
        className={cx(
          'flex w-full flex-col items-center gap-2 rounded-card border-2 border-dashed px-6 py-8 text-center transition',
          desabilitado
            ? 'cursor-not-allowed border-line-2 opacity-60'
            : sobre
              ? 'border-brand bg-brand-soft'
              : 'border-line-2 hover:border-brand-500',
        )}
      >
        <UploadCloud aria-hidden className="size-6 text-brand" />
        <span className="text-sm font-medium text-ink">
          Clique para adicionar arquivo ou arraste aqui
        </span>
        <span className="text-xs text-muted">PNG, JPG, PDF até 10 MB</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={EXT_ACEITAS}
        multiple
        hidden
        onChange={(e) => {
          receber(e.target.files);
          e.target.value = '';
        }}
      />
      {dica && <p className="mt-2 text-xs text-muted">{dica}</p>}
      {erro && (
        <p role="alert" className="mt-2 text-xs text-danger-ink">
          {erro}
        </p>
      )}
    </div>
  );
}
