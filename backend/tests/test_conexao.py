"""Testes da API base (F0.2): health, X-Request-ID e formato único de erro."""

from __future__ import annotations

import uuid

from app.core.database import obter_sessao
from app.main import create_app
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


def test_health_responde_ok(client: TestClient) -> None:
    resposta = client.get("/api/health")
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json() == {"status": "ok"}


def test_health_tem_header_request_id_gerado(client: TestClient) -> None:
    resposta = client.get("/api/health")
    assert resposta.headers.get("X-Request-ID")


def test_request_id_recebido_e_propagado(client: TestClient) -> None:
    enviado = uuid.uuid4().hex
    resposta = client.get("/api/health", headers={"X-Request-ID": enviado})
    assert resposta.headers["X-Request-ID"] == enviado


def test_health_db_ok_com_sessao_substituida(client: TestClient) -> None:
    class SessaoFake:
        def execute(self, _stmt: object) -> None:
            return None

        def close(self) -> None:
            return None

    app = client.app
    app.dependency_overrides[obter_sessao] = lambda: SessaoFake()  # type: ignore[attr-defined]
    try:
        resposta = client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()  # type: ignore[attr-defined]

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json() == {"status": "ok", "db": "ok"}


def test_health_db_falha_vira_503_no_formato_unico() -> None:
    app = create_app()

    def sessao_quebrada() -> Session:
        class SessaoFake:
            def execute(self, _stmt: object) -> None:
                raise OperationalError("SELECT 1", {}, Exception("sem conexão"))

            def close(self) -> None:
                return None

        return SessaoFake()  # type: ignore[return-value]

    app.dependency_overrides[obter_sessao] = sessao_quebrada
    with TestClient(app, raise_server_exceptions=False) as cliente:
        resposta = cliente.get("/api/health/db")

    assert resposta.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    corpo = resposta.json()
    assert corpo["codigo"] == "BANCO_INDISPONIVEL"
    assert "mensagem" in corpo


def test_rota_inexistente_usa_formato_unico(client: TestClient) -> None:
    resposta = client.get("/api/nao-existe")
    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    corpo = resposta.json()
    assert corpo["codigo"] == "NAO_ENCONTRADO"
    assert corpo["mensagem"] == "Recurso não encontrado."


def test_uso_de_text_select_1_e_valido() -> None:
    # Garante que o SELECT 1 do health_db é uma expressão SQLAlchemy válida.
    assert str(text("SELECT 1")) == "SELECT 1"
