"""Testes da abertura de chamados (F2.1) com PostgreSQL real.

Cobre a seção 7.3 e a RN04:
- GET /api/categorias: ativas, ordenadas; exige autenticação (TU07 parcial).
- TU01 (RN04): sem categoria (422 do schema) e categoria inexistente/inativa (409).
- TU02 (RN04): solicitante inativo → recusado (via token de usuário inativado).
- TU03: chamado válido nasce NOVO, ligado ao usuário do token, com a severidade
  informada e o protocolo gerado (TK-####).
- TU04: título/descrição vazios e descrição > 500 → 422.

Não fixa ids (sequências IDENTITY não voltam no rollback).
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario

EMAIL = "cliente.f2@exemplo.com.br"
SENHA = "senha-cliente-ok-123"


def _login(app: TestClient, sessao: Session, *, ativo: bool = True) -> str:
    criar_usuario(sessao, email=EMAIL, senha=SENHA, nome="Cliente F2", ativo=ativo)
    r = app.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _id_categoria_ativa(sessao: Session) -> int:
    return int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )


# ===== GET /api/categorias =====


def test_categorias_exige_autenticacao(app_integrado: TestClient) -> None:
    r = app_integrado.get("/api/categorias")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_categorias_lista_ativas_ordenadas(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _login(app_integrado, sessao_banco)
    r = app_integrado.get("/api/categorias", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK
    itens = r.json()
    assert len(itens) == 7  # as 7 categorias do seed (migration 0001)
    ordens = [c["ordem"] for c in itens]
    assert ordens == sorted(ordens)
    assert all(c["ativa"] for c in itens)
    assert itens[0]["nome_categoria"] == "TI"


# ===== POST /api/chamados =====


def test_tu03_chamado_valido_nasce_novo_com_protocolo(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)

    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={
            "id_categoria": id_cat,
            "severidade": "ALTA",
            "titulo": "VPN não conecta",
            "descricao": "Desde a atualização o cliente VPN falha.",
        },
    )

    assert r.status_code == status.HTTP_201_CREATED
    corpo = r.json()
    assert corpo["status_chamado"] == "NOVO"
    assert corpo["status_grupo"] == "abertos"
    assert corpo["severidade"] == "ALTA"
    assert corpo["protocolo"].startswith("TK-") and len(corpo["protocolo"]) >= 7
    assert corpo["categoria"]["id_categoria"] == id_cat
    assert corpo["solicitante"]["nome"] == "Cliente F2"
    assert corpo["tecnico_responsavel"] is None
    assert corpo["qtd_mensagens"] == 0


def test_tu03_severidade_padrao_baixa(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "Sem severidade", "descricao": "Texto."},
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.json()["severidade"] == "BAIXA"


def test_tu01_categoria_inexistente_rejeitada(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _login(app_integrado, sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": 999999, "titulo": "X", "descricao": "Y"},
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["codigo"] == "CATEGORIA_INVALIDA"


def test_tu01_categoria_inativa_rejeitada(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    # Desativa uma categoria dentro da transação do teste.
    id_cat = _id_categoria_ativa(sessao_banco)
    sessao_banco.execute(
        text("UPDATE categorias SET ativa = false WHERE id_categoria = :id"), {"id": id_cat}
    )
    sessao_banco.flush()

    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "X", "descricao": "Y"},
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["codigo"] == "CATEGORIA_INVALIDA"


def test_tu01_sem_categoria_422(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"titulo": "X", "descricao": "Y"},
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r.json()["codigo"] == "VALIDACAO"


def test_tu02_solicitante_inativo_rejeitado(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    # Loga e, em seguida, inativa o próprio usuário: o token ainda decodifica, mas
    # a abertura deve recusar o solicitante inativo (RN04). Como `usuario_atual` já
    # recusaria o inativo com 401, o efeito observável é a não criação do chamado.
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)
    sessao_banco.execute(text("UPDATE usuarios SET ativo = false WHERE email = :e"), {"e": EMAIL})
    sessao_banco.flush()

    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "X", "descricao": "Y"},
    )
    # Usuário inativo não abre chamado (401 pela dependência de sessão/perfil).
    assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_409_CONFLICT)
    total = sessao_banco.execute(text("SELECT count(*) FROM chamados")).scalar_one()
    assert total == 0


def test_tu04_titulo_vazio_422(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "   ", "descricao": "ok"},
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "titulo" in r.json()["campos"]


def test_tu04_descricao_vazia_422(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "ok", "descricao": "   "},
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "descricao" in r.json()["campos"]


def test_tu04_descricao_acima_de_500_422(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco)
    id_cat = _id_categoria_ativa(sessao_banco)
    r = app_integrado.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "ok", "descricao": "a" * 501},
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "descricao" in r.json()["campos"]
