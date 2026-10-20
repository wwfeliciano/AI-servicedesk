import { useEffect, useState } from 'react';

/** Retorna o valor após `ms` de inatividade (busca em tempo real, seção 8.4). */
export function useDebounce<T>(valor: T, ms = 300): T {
  const [debounced, setDebounced] = useState(valor);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(valor), ms);
    return () => clearTimeout(id);
  }, [valor, ms]);
  return debounced;
}
