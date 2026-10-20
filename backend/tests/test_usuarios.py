"""Testes do cadastro e da consulta de usuários (F1.2) e da config pública.

Cobre a seção 7.2/7.3 e as regras da seção 11:
- TU05 (RN07): e-mail duplicado → 409 EMAIL_DUPLICADO (inclui diferença só de caixa);
- TU06: senha < 8 → 422; a senha é gravada como hash `$2b$`, nunca em claro;
- cadastro ok (201) com o contrato e normalização do e-mail;
- lista paginada com filtros (`q`, `perfil`, `ativo`) e envelope de paginação;
- detalhe por id e 404 para inexistente;
- TU07 (RN06): rotas de /api/usuarios sem token → 401; CLIENTE → 403; ADMIN → ok;
- GET /api/config/publica é público e devolve o contrato esperado.

Não fixa ids (sequências IDENTITY não voltam no rollback).
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario

ADMIN_EMAIL = "admin.helpdesk@exemplo.com.br"
ADMIN_SENHA = "senha-admin-super-ok"


def _token_admin(app_integrado: TestClient, sessao_banco: Session) -> str:
    """Cria um ADMIN, faz login e devolve o access token para o header Bearer."""
    criar_usuario(sessao_banco, email=ADMIN_EMAIL, senha=ADMIN_SENHA, nome="Admin", perfil="ADMIN")
    resposta = app_integrado.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_SENHA}
    )
    assert resposta.status_code == status.HTTP_200_OK
    return str(resposta.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ===== Cadastro (POST /api/usuarios) =====


def test_cadastro_ok_devolve_201_e_normaliza_email(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    resposta = app_integrado.post(
        "/api/usuarios",
        headers=_auth(token),
        json={
            "nome": "Rafael Mendes",
            "email": "Rafael.Mendes@Exemplo.Com.BR",
            "senha": "senha-forte-123",
            "tipo_perfil": "ANALISTA",
            "cargo": "Analista de Suporte",
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    corpo = resposta.json()
    assert corpo["email"] == "rafael.mendes@exemplo.com.br"  # normalizado em minúsculas
    assert corpo["tipo_perfil"] == "ANALISTA"
    assert corpo["cargo"] == "Analista de Suporte"
    assert corpo["ativo"] is True
    assert corpo["id_usuario"] > 0
    assert "senha" not in corpo and "senha_hash" not in corpo


def test_tu05_email_duplicado_rejeitado(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    criar_usuario(sessao_banco, email="dup@exemplo.com.br", senha="qualquer-ok-123")

    resposta = app_integrado.post(
        "/api/usuarios",
        headers=_auth(token),
        json={
            "nome": "Outro",
            "email": "dup@exemplo.com.br",
            "senha": "senha-forte-123",
            "tipo_perfil": "CLIENTE",
        },
    )

    assert resposta.status_code == status.HTTP_409_CONFLICT
    corpo = resposta.json()
    assert corpo["codigo"] == "EMAIL_DUPLICADO"
    assert corpo["campos"]["email"] == "Este e-mail já está cadastrado."


def test_tu05_email_duplicado_ignora_caixa(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    criar_usuario(sessao_banco, email="pessoa@exemplo.com.br", senha="qualquer-ok-123")

    # Mesmo e-mail em outra caixa também é duplicado (RN07, e-mail normalizado).
    resposta = app_integrado.post(
        "/api/usuarios",
        headers=_auth(token),
        json={
            "nome": "Pessoa",
            "email": "PESSOA@EXEMPLO.COM.BR",
            "senha": "senha-forte-123",
            "tipo_perfil": "CLIENTE",
        },
    )
    assert resposta.status_code == status.HTTP_409_CONFLICT
    assert resposta.json()["codigo"] == "EMAIL_DUPLICADO"


def test_tu06_senha_curta_rejeitada(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    resposta = app_integrado.post(
        "/api/usuarios",
        headers=_auth(token),
        json={
            "nome": "Curta",
            "email": "curta@exemplo.com.br",
            "senha": "1234567",  # 7 caracteres
            "tipo_perfil": "CLIENTE",
        },
    )

    assert resposta.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    corpo = resposta.json()
    assert corpo["codigo"] == "VALIDACAO"
    assert "senha" in corpo["campos"]
    # O usuário não foi gravado.
    existe = sessao_banco.execute(
        text("SELECT count(*) FROM usuarios WHERE email = :e"), {"e": "curta@exemplo.com.br"}
    ).scalar_one()
    assert existe == 0


def test_tu06_senha_gravada_como_hash(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    senha = "senha-em-claro-do-teste"
    resposta = app_integrado.post(
        "/api/usuarios",
        headers=_auth(token),
        json={
            "nome": "Com Hash",
            "email": "hash@exemplo.com.br",
            "senha": senha,
            "tipo_perfil": "CLIENTE",
        },
    )
    assert resposta.status_code == status.HTTP_201_CREATED

    hash_gravado = sessao_banco.execute(
        text("SELECT senha_hash FROM usuarios WHERE email = :e"), {"e": "hash@exemplo.com.br"}
    ).scalar_one()
    assert hash_gravado.startswith("$2b$")
    assert senha not in hash_gravado


# ===== Lista e detalhe (GET /api/usuarios, GET /api/usuarios/{id}) =====


def test_lista_paginada_com_filtros(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    criar_usuario(sessao_banco, email="ana@exemplo.com.br", senha="x-ok-123456", nome="Ana Souza")
    criar_usuario(
        sessao_banco,
        email="bruno@exemplo.com.br",
        senha="x-ok-123456",
        nome="Bruno Dias",
        perfil="ANALISTA",
    )
    criar_usuario(
        sessao_banco,
        email="carla@exemplo.com.br",
        senha="x-ok-123456",
        nome="Carla Lima",
        ativo=False,
    )

    # Sem filtro: admin + 3 criados = 4.
    r_todos = app_integrado.get("/api/usuarios", headers=_auth(token))
    assert r_todos.status_code == status.HTTP_200_OK
    corpo = r_todos.json()
    assert corpo["total"] == 4
    assert corpo["page"] == 1
    assert corpo["page_size"] == 10
    assert {"items", "total", "page", "page_size"} == set(corpo)

    # Filtro por perfil ANALISTA → só Bruno.
    r_perfil = app_integrado.get(
        "/api/usuarios", headers=_auth(token), params={"perfil": "ANALISTA"}
    )
    assert r_perfil.json()["total"] == 1
    assert r_perfil.json()["items"][0]["nome"] == "Bruno Dias"

    # Filtro ativo=false → só Carla.
    r_inativos = app_integrado.get("/api/usuarios", headers=_auth(token), params={"ativo": "false"})
    assert r_inativos.json()["total"] == 1
    assert r_inativos.json()["items"][0]["email"] == "carla@exemplo.com.br"

    # Busca por nome (q) → Ana.
    r_q = app_integrado.get("/api/usuarios", headers=_auth(token), params={"q": "ana"})
    emails = {u["email"] for u in r_q.json()["items"]}
    assert "ana@exemplo.com.br" in emails


def test_lista_respeita_page_size(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    for i in range(3):
        criar_usuario(
            sessao_banco, email=f"u{i}@exemplo.com.br", senha="x-ok-123456", nome=f"User {i}"
        )

    r = app_integrado.get("/api/usuarios", headers=_auth(token), params={"page": 1, "page_size": 2})
    corpo = r.json()
    assert corpo["total"] == 4  # admin + 3
    assert len(corpo["items"]) == 2
    assert corpo["page_size"] == 2


def test_detalhe_ok_e_inexistente(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _token_admin(app_integrado, sessao_banco)
    id_usuario = criar_usuario(
        sessao_banco, email="detalhe@exemplo.com.br", senha="x-ok-123456", nome="Detalhe"
    )

    r_ok = app_integrado.get(f"/api/usuarios/{id_usuario}", headers=_auth(token))
    assert r_ok.status_code == status.HTTP_200_OK
    assert r_ok.json()["email"] == "detalhe@exemplo.com.br"

    r_404 = app_integrado.get("/api/usuarios/99999999", headers=_auth(token))
    assert r_404.status_code == status.HTTP_404_NOT_FOUND
    assert r_404.json()["codigo"] == "NAO_ENCONTRADO"


# ===== TU07 (RN06): autenticação e perfil nas rotas de usuários =====


def test_tu07_usuarios_sem_token_401(app_integrado: TestClient) -> None:
    r_lista = app_integrado.get("/api/usuarios")
    r_post = app_integrado.post("/api/usuarios", json={})
    assert r_lista.status_code == status.HTTP_401_UNAUTHORIZED
    assert r_post.status_code == status.HTTP_401_UNAUTHORIZED
    assert r_lista.json()["codigo"] == "NAO_AUTENTICADO"


def test_tu07_cliente_nao_acessa_usuarios_403(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(
        sessao_banco, email="cliente@exemplo.com.br", senha="cliente-ok-123", perfil="CLIENTE"
    )
    login = app_integrado.post(
        "/api/auth/login", json={"email": "cliente@exemplo.com.br", "senha": "cliente-ok-123"}
    )
    token = login.json()["access_token"]

    r = app_integrado.get("/api/usuarios", headers=_auth(token))
    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert r.json()["codigo"] == "SEM_PERMISSAO"


# ===== Config pública (GET /api/config/publica) =====


def test_config_publica_e_publica_e_tem_contrato(client: TestClient) -> None:
    resposta = client.get("/api/config/publica")
    assert resposta.status_code == status.HTTP_200_OK
    corpo = resposta.json()
    assert set(corpo) == {"whatsapp_suporte", "email_suporte", "google_sso", "versao"}
    assert isinstance(corpo["google_sso"], bool)
    assert isinstance(corpo["versao"], str) and corpo["versao"]


# ===== CLI: make criar-admin (idempotente) =====


def test_cli_criar_admin_idempotente(sessao_banco: Session) -> None:
    from app.cli import criar_admin_na_sessao
    from app.core.config import Configuracao

    config = Configuracao(
        admin_nome="Administrador do Teste",
        admin_email="Primeiro.Admin@Exemplo.Com.BR",
        admin_senha="senha-admin-super-ok",
    )

    # Primeira execução: cria o ADMIN.
    r1 = criar_admin_na_sessao(sessao_banco, config)
    assert r1.criado is True
    assert r1.id_usuario is not None
    sessao_banco.flush()

    # Grava como ADMIN e com e-mail normalizado.
    perfil, email = sessao_banco.execute(
        text("SELECT tipo_perfil, email FROM usuarios WHERE id_usuario = :id"),
        {"id": r1.id_usuario},
    ).one()
    assert perfil == "ADMIN"
    assert email == "primeiro.admin@exemplo.com.br"

    # Segunda execução: não duplica (idempotente).
    r2 = criar_admin_na_sessao(sessao_banco, config)
    assert r2.criado is False
    total = sessao_banco.execute(
        text("SELECT count(*) FROM usuarios WHERE email = :e"),
        {"e": "primeiro.admin@exemplo.com.br"},
    ).scalar_one()
    assert total == 1
