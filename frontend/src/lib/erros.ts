/** Formato único de erro da API (seção 7.1 do prompt). */
export interface ErroAPI {
  codigo: string;
  mensagem: string;
  campos?: Record<string, string>;
}

/** Type guard: o corpo tem o formato de erro da API. */
export function ehErroAPI(valor: unknown): valor is ErroAPI {
  return (
    typeof valor === 'object' &&
    valor !== null &&
    'codigo' in valor &&
    'mensagem' in valor &&
    typeof (valor as ErroAPI).codigo === 'string'
  );
}

/** Mensagem amigável a partir de um erro desconhecido (fallback em PT-BR). */
export function mensagemDeErro(erro: unknown, padrao = 'Algo deu errado. Tente novamente.'): string {
  if (ehErroAPI(erro)) return erro.mensagem;
  if (erro instanceof Error && erro.message) return erro.message;
  return padrao;
}
