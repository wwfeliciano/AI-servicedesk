"""Testes da autenticação (F1.1) com PostgreSQL real e Redis fake.

Cobre o contrato da seção 7.3 e as regras da seção 11:
- login ok (contrato, cookie de refresh), login inválido (mensagem genérica, FE01);
- TU06: senha nova < 8 ou > 72 bytes → 422; hash gravado como `$2b$`, nunca em claro;
- TU07 (parte): sem token → 401; CLIENTE sem permissão → 403 (via exigir_perfil);
- refresh com rotação; reuso de refresh revogado derruba a família;
- logout revoga o refresh; me devolve o usuário; limite de 5 tentativas → 429.

Não fixa ids (sequências IDENTITY não voltam no rollback).
"""

from __future__ import annotations

import pytest
from app.controllers.dependencias import exigir_perfil, usuario_atual
from app.core.errors import ErroAPI
from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario

EMAIL = "ana.lima@exemplo.com.br"
SENHA = "senha-super-ok-123"


def test_login_ok_devolve_contrato_e_cookie(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(
        sessao_banco, email=EMAIL, senha=SENHA, nome="Ana Lima", cargo="Analista de Marketing"
    )

    resposta = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resposta.status_code == status.HTTP_200_OK
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["expires_in"] == 30 * 60
    assert corpo["access_token"]
    assert corpo["usuario"]["email"] == EMAIL
    assert corpo["usuario"]["tipo_perfil"] == "CLIENTE"
    assert corpo["usuario"]["cargo"] == "Analista de Marketing"
    # O refresh token vai no cookie HttpOnly, nunca no corpo.
    assert "refresh_token" not in corpo
    assert "refresh_token" in resposta.cookies


def test_fe01_login_invalido_mensagem_generica(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)

    # Senha errada e e-mail inexistente devolvem exatamente a mesma resposta.
    r_senha = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": "errada-xyz"})
    r_email = app_integrado.post(
        "/api/auth/login", json={"email": "nao-existe@exemplo.com.br", "senha": SENHA}
    )

    assert r_senha.status_code == status.HTTP_401_UNAUTHORIZED
    assert r_email.status_code == status.HTTP_401_UNAUTHORIZED
    assert r_senha.json() == r_email.json()
    assert r_senha.json()["mensagem"] == "E-mail ou senha inválidos."
    assert r_senha.json()["codigo"] == "NAO_AUTENTICADO"


def test_login_usuario_inativo_tambem_generico(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA, ativo=False)

    resposta = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.json()["mensagem"] == "E-mail ou senha inválidos."


def test_tu06_senha_gravada_como_hash_bcrypt(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    hash_gravado = sessao_banco.execute(
        text("SELECT senha_hash FROM usuarios WHERE email = :e"), {"e": EMAIL}
    ).scalar_one()
    assert hash_gravado.startswith("$2b$")
    assert SENHA not in hash_gravado


def test_tu06_troca_senha_curta_rejeitada(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    token = _login(app_integrado)

    resposta = app_integrado.put(
        "/api/auth/senha",
        headers={"Authorization": f"Bearer {token}"},
        json={"senha_atual": SENHA, "senha_nova": "curta"},
    )
    assert resposta.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resposta.json()["codigo"] == "VALIDACAO"


def test_tu06_troca_senha_acima_de_72_bytes_rejeitada(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    token = _login(app_integrado)

    resposta = app_integrado.put(
        "/api/auth/senha",
        headers={"Authorization": f"Bearer {token}"},
        json={"senha_atual": SENHA, "senha_nova": "a" * 73},
    )
    assert resposta.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_troca_senha_ok_e_senha_antiga_para_de_funcionar(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    token = _login(app_integrado)
    nova = "nova-senha-forte-456"

    r_troca = app_integrado.put(
        "/api/auth/senha",
        headers={"Authorization": f"Bearer {token}"},
        json={"senha_atual": SENHA, "senha_nova": nova},
    )
    assert r_troca.status_code == status.HTTP_204_NO_CONTENT

    assert (
        app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA}).status_code
        == status.HTTP_401_UNAUTHORIZED
    )
    assert (
        app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": nova}).status_code
        == status.HTTP_200_OK
    )


def test_troca_senha_atual_errada(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    token = _login(app_integrado)

    resposta = app_integrado.put(
        "/api/auth/senha",
        headers={"Authorization": f"Bearer {token}"},
        json={"senha_atual": "nao-e-a-atual", "senha_nova": "outra-senha-123"},
    )
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_tu07_me_sem_token_401(app_integrado: TestClient) -> None:
    resposta = app_integrado.get("/api/auth/me")
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.json()["codigo"] == "NAO_AUTENTICADO"


def test_tu07_token_malformado_401(app_integrado: TestClient) -> None:
    resposta = app_integrado.get("/api/auth/me", headers={"Authorization": "Bearer nao-e-um-jwt"})
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_devolve_usuario(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA, nome="Ana Lima")
    token = _login(app_integrado)

    resposta = app_integrado.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["email"] == EMAIL
    assert resposta.json()["nome"] == "Ana Lima"


def test_refresh_rotaciona(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    login = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    cookie_antigo = login.cookies["refresh_token"]

    r_refresh = app_integrado.post("/api/auth/refresh")
    assert r_refresh.status_code == status.HTTP_200_OK
    assert r_refresh.json()["access_token"]
    # Rotação: um novo refresh é emitido.
    assert r_refresh.cookies["refresh_token"] != cookie_antigo


def test_refresh_reuso_de_token_revogado_derruba_familia(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    login = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    refresh_1 = login.cookies["refresh_token"]

    # Primeiro refresh rotaciona: refresh_1 fica revogado e surge refresh_2.
    app_integrado.cookies.set("refresh_token", refresh_1)
    r2 = app_integrado.post("/api/auth/refresh")
    assert r2.status_code == status.HTTP_200_OK
    refresh_2 = r2.cookies["refresh_token"]

    # Reusar o refresh_1 (já revogado) deve falhar e revogar a família inteira.
    app_integrado.cookies.set("refresh_token", refresh_1)
    reuso = app_integrado.post("/api/auth/refresh")
    assert reuso.status_code == status.HTTP_401_UNAUTHORIZED

    # Agora o refresh_2, da mesma família, também não vale mais.
    app_integrado.cookies.set("refresh_token", refresh_2)
    apos = app_integrado.post("/api/auth/refresh")
    assert apos.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_sem_cookie_401(app_integrado: TestClient) -> None:
    assert app_integrado.post("/api/auth/refresh").status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_revoga_refresh(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    login = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    token = login.json()["access_token"]
    refresh = login.cookies["refresh_token"]

    r_logout = app_integrado.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r_logout.status_code == status.HTTP_204_NO_CONTENT

    # O refresh revogado não serve mais.
    app_integrado.cookies.set("refresh_token", refresh)
    apos = app_integrado.post("/api/auth/refresh")
    assert apos.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_sem_token_401(app_integrado: TestClient) -> None:
    assert app_integrado.post("/api/auth/logout").status_code == status.HTTP_401_UNAUTHORIZED


def test_rnf01_limite_de_tentativas_429(app_integrado: TestClient, sessao_banco: Session) -> None:
    criar_usuario(sessao_banco, email=EMAIL, senha=SENHA)
    # 5 tentativas erradas esgotam o limite por e-mail (e por IP).
    for _ in range(5):
        r = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": "errada"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    # A 6ª (mesmo com senha certa) é barrada por excesso de tentativas.
    bloqueado = app_integrado.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert bloqueado.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert bloqueado.json()["codigo"] == "MUITAS_TENTATIVAS"


def test_tu07_exigir_perfil_admin_nega_cliente() -> None:
    """exigir_perfil(ADMIN): 403 (SEM_PERMISSAO) para CLIENTE, passa para ADMIN."""
    cliente = Usuario(
        id_usuario=1,
        nome="C",
        email="c@exemplo.com.br",
        senha_hash="x",
        tipo_perfil=PerfilUsuario.CLIENTE,
    )
    admin = Usuario(
        id_usuario=2,
        nome="A",
        email="a@exemplo.com.br",
        senha_hash="x",
        tipo_perfil=PerfilUsuario.ADMIN,
    )
    dependencia = exigir_perfil(PerfilUsuario.ADMIN)

    with pytest.raises(ErroAPI) as info:
        dependencia(cliente)
    assert info.value.status_code == 403
    assert info.value.codigo == "SEM_PERMISSAO"

    # ADMIN passa e recebe o próprio usuário de volta.
    assert dependencia(admin) is admin
    # usuario_atual é a dependência base usada pela fábrica.
    assert usuario_atual.__name__ == "usuario_atual"


def _login(cliente: TestClient, *, email: str = EMAIL, senha: str = SENHA) -> str:
    resposta = cliente.post("/api/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == status.HTTP_200_OK, resposta.text
    token: str = resposta.json()["access_token"]
    return token
