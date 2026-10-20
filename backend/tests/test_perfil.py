"""Testes do Perfil — vínculo de WhatsApp e preferências (F6.3, seção 9.4).

- gerar vínculo exige consentimento (422) e devolve código de 6 dígitos + link wa.me;
- status reflete não-vinculado por padrão;
- PATCH de preferências altera `notificar_email`/`whatsapp_opt_in`;
- DELETE desvincula (opt-out);
- `GET /api/auth/me` expõe as preferências.
"""

from __future__ import annotations

import re

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(app: TestClient, sessao: Session, email: str) -> str:
    criar_usuario(sessao, email=email, senha="senha-ok-123456", nome=email.split("@")[0])
    r = app.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def test_vinculo_exige_consentimento(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "perfil1@empresa.com.br")
    r = app_integrado.post(
        "/api/perfil/whatsapp/vinculo", headers=_auth(token), json={"consentimento": False}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r.json()["codigo"] == "CONSENTIMENTO_OBRIGATORIO"


def test_vinculo_gera_codigo_e_link(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "perfil2@empresa.com.br")
    r = app_integrado.post(
        "/api/perfil/whatsapp/vinculo", headers=_auth(token), json={"consentimento": True}
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    corpo = r.json()
    assert re.fullmatch(r"\d{6}", corpo["codigo"])
    assert corpo["link_wa"].startswith("https://wa.me/5515999999999?text=VINCULAR")
    assert corpo["codigo"] in corpo["link_wa"]
    assert corpo["expira_em_segundos"] == 600


def test_status_nao_vinculado_por_padrao(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "perfil3@empresa.com.br")
    r = app_integrado.get("/api/perfil/whatsapp", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK
    corpo = r.json()
    assert corpo["vinculado"] is False
    assert corpo["notificar_email"] is True


def test_preferencias_atualiza(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "perfil4@empresa.com.br")
    r = app_integrado.patch(
        "/api/perfil/preferencias",
        headers=_auth(token),
        json={"notificar_email": False, "whatsapp_opt_in": True},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    corpo = r.json()
    assert corpo["notificar_email"] is False
    assert corpo["opt_in"] is True
    # Reflete no /auth/me.
    me = app_integrado.get("/api/auth/me", headers=_auth(token)).json()
    assert me["notificar_email"] is False
    assert me["whatsapp_opt_in"] is True


def test_desvincular(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "perfil5@empresa.com.br")
    # Simula um vínculo direto no banco.
    sessao_banco.execute(
        text(
            "UPDATE usuarios SET whatsapp_chat_id = '5515999990000@c.us', "
            "whatsapp_numero = '5515999990000', whatsapp_opt_in = true "
            "WHERE email = 'perfil5@empresa.com.br'"
        )
    )
    sessao_banco.flush()
    sessao_banco.expire_all()

    antes = app_integrado.get("/api/perfil/whatsapp", headers=_auth(token)).json()
    assert antes["vinculado"] is True

    r = app_integrado.delete("/api/perfil/whatsapp", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["vinculado"] is False
    assert r.json()["opt_in"] is False


def test_vinculo_exige_autenticacao(app_integrado: TestClient) -> None:
    r = app_integrado.post("/api/perfil/whatsapp/vinculo", json={"consentimento": True})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
