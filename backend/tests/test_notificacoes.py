"""Testes das notificações no portal (F3.2, TU17 — parte portal) com PostgreSQL real.

- a abertura de chamado gera `CHAMADO_CRIADO` para o solicitante;
- chamado CRITICO gera `CHAMADO_URGENTE` para ANALISTA/ADMIN ativos;
- a lista e a contagem são só do próprio usuário (escopo);
- marcar uma e todas como lidas; marcar notificação de outro → 404.
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(app: TestClient, sessao: Session, email: str, *, perfil: str = "CLIENTE") -> str:
    criar_usuario(
        sessao, email=email, senha="senha-ok-123456", nome=email.split("@")[0], perfil=perfil
    )
    r = app.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def _id_categoria(sessao: Session) -> int:
    return int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )


def _abrir(app: TestClient, token: str, id_cat: int, *, severidade: str = "BAIXA") -> None:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={
            "id_categoria": id_cat,
            "titulo": "Chamado com evento",
            "descricao": "Gera notificação.",
            "severidade": severidade,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text


def test_abertura_gera_notificacao_ao_solicitante(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, _id_categoria(sessao_banco))

    r = app_integrado.get("/api/notificacoes", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK
    corpo = r.json()
    assert corpo["total"] == 1
    assert corpo["nao_lidas"] == 1
    assert corpo["items"][0]["tipo"] == "CHAMADO_CRIADO"
    assert corpo["items"][0]["lida"] is False


def test_contagem_nao_lidas(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    id_cat = _id_categoria(sessao_banco)
    _abrir(app_integrado, token, id_cat)
    _abrir(app_integrado, token, id_cat)

    r = app_integrado.get("/api/notificacoes/contagem", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["nao_lidas"] == 2


def test_chamado_urgente_notifica_analista(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    # Um analista ativo precisa existir para receber o alerta.
    t_analista = _login(app_integrado, sessao_banco, "tec@exemplo.com.br", perfil="ANALISTA")
    t_cliente = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")

    _abrir(app_integrado, t_cliente, _id_categoria(sessao_banco), severidade="CRITICO")

    # O analista recebeu um CHAMADO_URGENTE.
    r_an = app_integrado.get("/api/notificacoes", headers=_auth(t_analista)).json()
    assert r_an["total"] == 1
    assert r_an["items"][0]["tipo"] == "CHAMADO_URGENTE"
    # O cliente recebeu o CHAMADO_CRIADO (não o urgente).
    r_cli = app_integrado.get("/api/notificacoes", headers=_auth(t_cliente)).json()
    assert r_cli["total"] == 1
    assert r_cli["items"][0]["tipo"] == "CHAMADO_CRIADO"


def test_escopo_lista_so_do_usuario(app_integrado: TestClient, sessao_banco: Session) -> None:
    id_cat = _id_categoria(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno@exemplo.com.br")
    _abrir(app_integrado, t_ana, id_cat)
    _abrir(app_integrado, t_bruno, id_cat)

    # Cada um vê só a sua notificação.
    assert app_integrado.get("/api/notificacoes", headers=_auth(t_ana)).json()["total"] == 1
    assert app_integrado.get("/api/notificacoes", headers=_auth(t_bruno)).json()["total"] == 1


def test_marcar_uma_lida(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, _id_categoria(sessao_banco))
    lista = app_integrado.get("/api/notificacoes", headers=_auth(token)).json()
    id_notif = lista["items"][0]["id_notificacao"]

    r = app_integrado.post(f"/api/notificacoes/{id_notif}/lida", headers=_auth(token))
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert (
        app_integrado.get("/api/notificacoes/contagem", headers=_auth(token)).json()["nao_lidas"]
        == 0
    )


def test_marcar_todas_lidas(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    id_cat = _id_categoria(sessao_banco)
    _abrir(app_integrado, token, id_cat)
    _abrir(app_integrado, token, id_cat)

    r = app_integrado.post("/api/notificacoes/lidas", headers=_auth(token))
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert (
        app_integrado.get("/api/notificacoes/contagem", headers=_auth(token)).json()["nao_lidas"]
        == 0
    )


def test_marcar_lida_de_outro_404(app_integrado: TestClient, sessao_banco: Session) -> None:
    id_cat = _id_categoria(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno@exemplo.com.br")
    _abrir(app_integrado, t_bruno, id_cat)
    id_do_bruno = app_integrado.get("/api/notificacoes", headers=_auth(t_bruno)).json()["items"][0][
        "id_notificacao"
    ]

    # Ana tenta marcar a notificação do Bruno → 404.
    r = app_integrado.post(f"/api/notificacoes/{id_do_bruno}/lida", headers=_auth(t_ana))
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert r.json()["codigo"] == "NAO_ENCONTRADO"


def test_notificacoes_sem_token_401(app_integrado: TestClient) -> None:
    assert app_integrado.get("/api/notificacoes").status_code == status.HTTP_401_UNAUTHORIZED
