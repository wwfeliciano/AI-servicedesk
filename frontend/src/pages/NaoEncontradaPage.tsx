import { Link } from 'react-router-dom';

export function NaoEncontradaPage() {
  return (
    <div className="grid min-h-dvh place-items-center bg-canvas px-6 text-center">
      <div>
        <p className="font-mono text-sm text-brand">404</p>
        <h1 className="mt-2 text-2xl text-ink">Página não encontrada</h1>
        <p className="mt-1 text-sm text-secondary">
          O endereço que você tentou abrir não existe.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex rounded-controle bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Voltar ao Dashboard
        </Link>
      </div>
    </div>
  );
}
