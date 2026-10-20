"""Regressão do defeito de sessão (F1.3): a dependência `obter_sessao` precisa
fazer `commit()` ao fim de uma requisição bem-sucedida e `rollback()` quando o
handler levanta exceção. Sem isso, os `flush()` dos services não persistem.

Usa um dublê de sessão (sem banco), exercitando o gerador da dependência como o
FastAPI faz: consome o `yield` e, no erro, usa `throw` para simular a exceção do
handler.
"""

from __future__ import annotations

import pytest
from app.core.database import obter_sessao


class _SessaoFalsa:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.fechada = False

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.fechada = True


def test_obter_sessao_commita_no_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    falsa = _SessaoFalsa()
    monkeypatch.setattr("app.core.database.FabricaSessao", lambda: falsa)

    gen = obter_sessao()
    sessao = next(gen)
    assert sessao is falsa
    # Fim normal da dependência (requisição sem erro).
    with pytest.raises(StopIteration):
        next(gen)

    assert falsa.commits == 1
    assert falsa.rollbacks == 0
    assert falsa.fechada is True


def test_obter_sessao_rollback_no_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    falsa = _SessaoFalsa()
    monkeypatch.setattr("app.core.database.FabricaSessao", lambda: falsa)

    gen = obter_sessao()
    next(gen)
    # Simula a exceção do handler sendo propagada para a dependência.
    with pytest.raises(ValueError, match="falha no handler"):
        gen.throw(ValueError("falha no handler"))

    assert falsa.commits == 0
    assert falsa.rollbacks == 1
    assert falsa.fechada is True
