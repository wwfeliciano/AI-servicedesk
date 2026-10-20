"""Testes de anexos (F3.1, TU16) com PostgreSQL real e storage em memória.

Cobre RF02 (anexos) e as decisões B9/B10:
- upload ok (PNG/JPG/PDF por magic bytes) e download em stream, no escopo;
- tipo não permitido → 415; arquivo acima do limite → 413;
- mais de 5 anexos por chamado → 409 (limite, B9);
- escopo (RN06): não anexa/baixa em chamado de outro → 404.

Não fixa ids (sequências IDENTITY não voltam no rollback).
"""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PDF = b"%PDF-1.7\n" + b"%fake pdf\n" * 8
SENHA = "senha-anexo-ok-123"


def _login(app: TestClient, sessao: Session, email: str) -> str:
    criar_usuario(sessao, email=email, senha=SENHA, nome=email.split("@")[0])
    r = app.post("/api/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _id_categoria(sessao: Session) -> int:
    return int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )


def _abrir_chamado(app: TestClient, token: str, id_cat: int) -> int:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "Com anexo", "descricao": "Preciso anexar algo."},
    )
    assert r.status_code == status.HTTP_201_CREATED
    return int(r.json()["id_chamado"])


def _enviar(app: TestClient, token: str, id_chamado: int, nome: str, conteudo: bytes, mime: str):
    return app.post(
        f"/api/chamados/{id_chamado}/anexos",
        headers=_auth(token),
        files={"arquivo": (nome, conteudo, mime)},
    )


def test_tu16_upload_ok_lista_e_download(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.anexo@exemplo.com.br")
    id_chamado = _abrir_chamado(app_integrado, token, _id_categoria(sessao_banco))

    r = _enviar(app_integrado, token, id_chamado, "captura.png", PNG, "image/png")
    assert r.status_code == status.HTTP_201_CREATED, r.text
    corpo = r.json()
    assert corpo["mime_type"] == "image/png"
    assert corpo["nome_original"] == "captura.png"
    id_anexo = corpo["id_anexo"]

    # Lista.
    r_lista = app_integrado.get(f"/api/chamados/{id_chamado}/anexos", headers=_auth(token))
    assert r_lista.status_code == status.HTTP_200_OK
    assert len(r_lista.json()) == 1

    # Download devolve o conteúdo.
    r_dl = app_integrado.get(f"/api/anexos/{id_anexo}/download", headers=_auth(token))
    assert r_dl.status_code == status.HTTP_200_OK
    assert r_dl.content == PNG
    assert r_dl.headers["content-type"].startswith("image/png")


def test_tu16_jpeg_e_pdf_aceitos(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.anexo@exemplo.com.br")
    id_chamado = _abrir_chamado(app_integrado, token, _id_categoria(sessao_banco))
    assert (
        _enviar(app_integrado, token, id_chamado, "foto.jpg", JPG, "image/jpeg").status_code
        == status.HTTP_201_CREATED
    )
    assert (
        _enviar(app_integrado, token, id_chamado, "doc.pdf", PDF, "application/pdf").status_code
        == status.HTTP_201_CREATED
    )


def test_tu16_tipo_invalido_415(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.anexo@exemplo.com.br")
    id_chamado = _abrir_chamado(app_integrado, token, _id_categoria(sessao_banco))
    # Conteúdo de texto (não é PNG/JPG/PDF) — mesmo mentindo o content-type.
    r = _enviar(app_integrado, token, id_chamado, "malicioso.png", b"texto puro", "image/png")
    assert r.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert r.json()["codigo"] == "TIPO_ARQUIVO_INVALIDO"


@pytest.mark.lento
def test_tu16_arquivo_grande_413(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.anexo@exemplo.com.br")
    id_chamado = _abrir_chamado(app_integrado, token, _id_categoria(sessao_banco))
    grande = b"\x89PNG\r\n\x1a\n" + b"\x00" * (10 * 1024 * 1024 + 1)
    r = _enviar(app_integrado, token, id_chamado, "grande.png", grande, "image/png")
    assert r.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert r.json()["codigo"] == "ARQUIVO_GRANDE"


def test_tu16_limite_de_5_por_chamado(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.anexo@exemplo.com.br")
    id_chamado = _abrir_chamado(app_integrado, token, _id_categoria(sessao_banco))
    for i in range(5):
        r = _enviar(app_integrado, token, id_chamado, f"a{i}.png", PNG, "image/png")
        assert r.status_code == status.HTTP_201_CREATED
    # O sexto é recusado (B9).
    r6 = _enviar(app_integrado, token, id_chamado, "a6.png", PNG, "image/png")
    assert r6.status_code == status.HTTP_409_CONFLICT
    assert r6.json()["codigo"] == "LIMITE_ANEXOS"


def test_tu16_escopo_nao_anexa_em_chamado_de_outro(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    id_cat = _id_categoria(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana.anexo@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno.anexo@exemplo.com.br")
    chamado_bruno = _abrir_chamado(app_integrado, t_bruno, id_cat)

    # Ana tenta anexar no chamado do Bruno → 404 (não revela que existe).
    r = _enviar(app_integrado, t_ana, chamado_bruno, "x.png", PNG, "image/png")
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert r.json()["codigo"] == "NAO_ENCONTRADO"
