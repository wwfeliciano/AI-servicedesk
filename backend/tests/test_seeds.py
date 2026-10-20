"""Testes dos seeds (F2.3) com PostgreSQL real.

- `semear_dev`: cria os usuários esperados (1 admin + 3 analistas + 10 clientes,
  incluindo Ana Lima e Rafael Mendes) e ~60 chamados variados; é idempotente.
- `semear_performance`: insere em lote (quantidade reduzida no teste unitário).
- Marcador `performance`: mede `GET /api/chamados` com volume (RNF02 ≤ 2 s); roda
  sob demanda (`-m performance`), não no CI padrão.
"""

from __future__ import annotations

import time

import pytest
from app.entities.chamado import Chamado
from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario
from app.seeds import semear_dev, semear_performance
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _contar(sessao: Session, perfil: PerfilUsuario) -> int:
    return int(
        sessao.scalar(
            select(func.count()).select_from(Usuario).where(Usuario.tipo_perfil == perfil)
        )
        or 0
    )


def test_seed_dev_cria_usuarios_e_chamados(sessao_banco: Session) -> None:
    resultado = semear_dev(sessao_banco)
    sessao_banco.flush()

    assert _contar(sessao_banco, PerfilUsuario.ANALISTA) == 3
    assert _contar(sessao_banco, PerfilUsuario.CLIENTE) == 10
    assert _contar(sessao_banco, PerfilUsuario.ADMIN) >= 1
    # Personagens do protótipo presentes.
    emails = set(sessao_banco.scalars(select(Usuario.email)).all())
    assert "ana.lima@empresa.com.br" in emails
    assert "rafael.mendes@empresa.com.br" in emails
    # ~60 chamados variados.
    total_chamados = int(sessao_banco.scalar(select(func.count()).select_from(Chamado)) or 0)
    assert total_chamados == 60
    assert resultado.chamados_criados == 60


def test_seed_dev_idempotente(sessao_banco: Session) -> None:
    semear_dev(sessao_banco)
    sessao_banco.flush()
    total_usuarios_1 = int(sessao_banco.scalar(select(func.count()).select_from(Usuario)) or 0)
    total_chamados_1 = int(sessao_banco.scalar(select(func.count()).select_from(Chamado)) or 0)

    # Segunda execução: não duplica usuários nem chamados.
    r2 = semear_dev(sessao_banco)
    sessao_banco.flush()
    total_usuarios_2 = int(sessao_banco.scalar(select(func.count()).select_from(Usuario)) or 0)
    total_chamados_2 = int(sessao_banco.scalar(select(func.count()).select_from(Chamado)) or 0)

    assert total_usuarios_2 == total_usuarios_1
    assert total_chamados_2 == total_chamados_1
    assert r2.usuarios_criados == 0
    assert r2.chamados_criados == 0


def test_seed_performance_insere_em_lote(sessao_banco: Session) -> None:
    # Volume reduzido no teste unitário (o volume real roda via make seed-performance).
    semear_performance(sessao_banco, qtd_usuarios=20, qtd_chamados=100)
    sessao_banco.flush()

    carga = int(
        sessao_banco.scalar(
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.email.like("carga%@empresa.com.br"))
        )
        or 0
    )
    assert carga == 20
    total_chamados = int(sessao_banco.scalar(select(func.count()).select_from(Chamado)) or 0)
    assert total_chamados == 100


@pytest.mark.performance
def test_rnf02_lista_responde_em_ate_2s(app_integrado: TestClient, sessao_banco: Session) -> None:
    """RNF02: a lista responde em até 2 s com volume. Roda sob demanda (-m performance)."""
    semear_performance(sessao_banco, qtd_usuarios=200, qtd_chamados=10_000)
    sessao_banco.flush()

    # ADMIN (vê todos) para exercitar o conjunto inteiro.
    criar_usuario(
        sessao_banco, email="perf.admin@empresa.com.br", senha="perf-admin-123", perfil="ADMIN"
    )
    login = app_integrado.post(
        "/api/auth/login", json={"email": "perf.admin@empresa.com.br", "senha": "perf-admin-123"}
    )
    token = login.json()["access_token"]

    inicio = time.perf_counter()
    r = app_integrado.get(
        "/api/chamados",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": "vpn", "page": 1, "page_size": 10},
    )
    decorrido = time.perf_counter() - inicio

    assert r.status_code == status.HTTP_200_OK
    assert r.json()["total"] >= 0
    assert decorrido <= 2.0, f"Lista demorou {decorrido:.3f}s (> 2 s, RNF02)"
