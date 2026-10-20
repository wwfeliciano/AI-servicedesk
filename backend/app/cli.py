"""CLI de operações do backend (Typer).

Comandos:
- `criar-admin`: cria o primeiro usuário ADMIN a partir de `ADMIN_NOME`,
  `ADMIN_EMAIL` e `ADMIN_SENHA` do ambiente (`.env`). É idempotente.
- `seed`: popula o ambiente de **desenvolvimento** com usuários fictícios e ~60
  chamados variados (seção 5.7). Idempotente pelo e-mail.
- `seed-performance`: insere em lote 200 usuários e 10.000 chamados para medir o
  RNF02 (lista ≤ 2 s).

Rodar: `python -m app.cli <comando>` (dentro da imagem do backend). Os `make seed*`
executam no serviço `api` do Compose. `seed` e `seed-performance` **só rodam em
desenvolvimento** (guarda por `AMBIENTE`).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import typer
from sqlalchemy.orm import Session

from app.core.config import Configuracao, obter_configuracao
from app.core.database import FabricaSessao
from app.entities.enums import PerfilUsuario
from app.repositories.usuario_repository import UsuarioRepository
from app.seeds import semear_dev, semear_performance
from app.services.usuario_service import ErroUsuario, UsuarioService

app = typer.Typer(help="Operações do backend Mentory Help Desk.", add_completion=False)


@app.callback()
def _raiz() -> None:
    """Agrupa os comandos (criar-admin e, depois, seeds). O callback força o Typer
    a manter a interface de subcomandos mesmo havendo um só comando."""


@dataclass(frozen=True)
class ResultadoCriarAdmin:
    criado: bool
    id_usuario: int | None
    mensagem: str


class ErroCLI(Exception):
    """Falha de operação da CLI (ex.: senha do admin fraca no .env)."""


def criar_admin_na_sessao(sessao: Session, config: Configuracao) -> ResultadoCriarAdmin:
    """Lógica idempotente de `criar-admin`, sem I/O de terminal nem commit.

    Devolve o resultado; o chamador decide sobre `commit`. Reaproveitado pelo teste.
    """
    email = config.admin_email.strip().lower()
    repositorio = UsuarioRepository(sessao)
    if repositorio.existe_email(email):
        return ResultadoCriarAdmin(
            criado=False,
            id_usuario=None,
            mensagem=f"Admin já existe para o e-mail informado ({email}). Nada a fazer.",
        )

    servico = UsuarioService(usuarios=repositorio)
    try:
        usuario = servico.cadastrar(
            nome=config.admin_nome,
            email=email,
            senha=config.admin_senha,
            tipo_perfil=PerfilUsuario.ADMIN,
        )
    except ErroUsuario as exc:
        # Senha fraca no .env, por exemplo. Não vaza a senha.
        raise ErroCLI(f"Não foi possível criar o admin: {exc.mensagem}") from exc

    return ResultadoCriarAdmin(
        criado=True,
        id_usuario=usuario.id_usuario,
        mensagem=f"Admin criado (id={usuario.id_usuario}, e-mail={email}).",
    )


@app.command("criar-admin")
def criar_admin() -> None:
    """Cria o primeiro ADMIN a partir do `.env` (idempotente, não duplica)."""
    config = obter_configuracao()
    with FabricaSessao() as sessao:
        try:
            resultado = criar_admin_na_sessao(sessao, config)
        except ErroCLI as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        if resultado.criado:
            sessao.commit()
        typer.echo(resultado.mensagem)


def _exigir_dev() -> None:
    """Impede rodar seeds fora de desenvolvimento (dados fictícios em massa)."""
    if obter_configuracao().em_producao:
        typer.echo("Seeds são apenas para desenvolvimento (AMBIENTE=prod bloqueia).", err=True)
        raise typer.Exit(code=1)


@app.command("seed")
def seed() -> None:
    """Popula o ambiente de dev (idempotente): usuários fictícios e ~60 chamados."""
    _exigir_dev()
    with FabricaSessao() as sessao:
        resultado = semear_dev(sessao)
        sessao.commit()
        typer.echo(resultado.mensagem)


@app.command("seed-performance")
def seed_performance(
    usuarios: int = typer.Option(200, help="Quantidade de usuários de carga."),
    chamados: int = typer.Option(10_000, help="Quantidade de chamados de carga."),
) -> None:
    """Insere em lote usuários e chamados para medir o RNF02 (só dev)."""
    _exigir_dev()
    with FabricaSessao() as sessao:
        resultado = semear_performance(sessao, qtd_usuarios=usuarios, qtd_chamados=chamados)
        sessao.commit()
        typer.echo(resultado.mensagem)


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(app())
