"""Testes da redefinição de senha por e-mail (F7.1 / FA02).

- `esqueci-senha` é **silencioso**: mesma resposta para e-mail existente ou não,
  e para e-mail inexistente não gera evento no outbox;
- para e-mail existente, gera um e-mail `SENHA_REDEFINICAO` no outbox com o link
  `/redefinir-senha?token=...` (ignora `notificar_email`);
- `redefinir-senha` com o token troca a senha (login com a nova funciona) e invalida
  o token (reuso → 400); token inválido/expirado → 400.
"""

from __future__ import annotations

import re

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _token_do_outbox(sessao: Session, email: str) -> str | None:
    """Extrai o token do link no payload do e-mail de redefinição (mais recente)."""
    bruto = sessao.execute(
        text(
            "SELECT payload::text FROM eventos_outbox "
            "WHERE tipo = 'SENHA_REDEFINICAO' AND destino = :e "
            "ORDER BY id_evento DESC LIMIT 1"
        ),
        {"e": email},
    ).scalar_one_or_none()
    if not bruto:
        return None
    m = re.search(r"redefinir-senha\?token=([a-zA-Z0-9_\-]+)", bruto)
    return m.group(1) if m else None


def test_esqueci_senha_resposta_generica_e_silenciosa(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    # E-mail inexistente: resposta 200 genérica, sem evento no outbox.
    r = app_integrado.post("/api/auth/esqueci-senha", json={"email": "ninguem@empresa.com.br"})
    assert r.status_code == status.HTTP_200_OK
    assert "Se o e-mail" in r.json()["mensagem"]
    sessao_banco.expire_all()
    assert _token_do_outbox(sessao_banco, "ninguem@empresa.com.br") is None


def test_fluxo_completo_redefinicao(app_integrado: TestClient, sessao_banco: Session) -> None:
    email = "reset.ok@empresa.com.br"
    criar_usuario(sessao_banco, email=email, senha="senha-antiga-123", nome="Rita")

    r = app_integrado.post("/api/auth/esqueci-senha", json={"email": email})
    assert r.status_code == status.HTTP_200_OK
    sessao_banco.expire_all()
    token = _token_do_outbox(sessao_banco, email)
    assert token is not None and len(token) > 20

    # Redefine com o token.
    r = app_integrado.post(
        "/api/auth/redefinir-senha", json={"token": token, "senha_nova": "senha-nova-456"}
    )
    assert r.status_code == status.HTTP_200_OK, r.text

    # Login com a nova senha funciona; com a antiga, não.
    ok = app_integrado.post("/api/auth/login", json={"email": email, "senha": "senha-nova-456"})
    assert ok.status_code == status.HTTP_200_OK
    velho = app_integrado.post(
        "/api/auth/login", json={"email": email, "senha": "senha-antiga-123"}
    )
    assert velho.status_code == status.HTTP_401_UNAUTHORIZED

    # Reuso do token: 400.
    reuso = app_integrado.post(
        "/api/auth/redefinir-senha", json={"token": token, "senha_nova": "outra-senha-789"}
    )
    assert reuso.status_code == status.HTTP_400_BAD_REQUEST
    assert reuso.json()["codigo"] == "TOKEN_INVALIDO"


def test_token_invalido(app_integrado: TestClient) -> None:
    r = app_integrado.post(
        "/api/auth/redefinir-senha", json={"token": "nao-existe", "senha_nova": "senha-nova-456"}
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["codigo"] == "TOKEN_INVALIDO"


def test_senha_fraca_rejeitada(app_integrado: TestClient, sessao_banco: Session) -> None:
    email = "reset.fraca@empresa.com.br"
    criar_usuario(sessao_banco, email=email, senha="senha-antiga-123", nome="Rui")
    app_integrado.post("/api/auth/esqueci-senha", json={"email": email})
    sessao_banco.expire_all()
    token = _token_do_outbox(sessao_banco, email)
    assert token is not None

    r = app_integrado.post(
        "/api/auth/redefinir-senha", json={"token": token, "senha_nova": "curta"}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r.json()["codigo"] == "VALIDACAO"
