"""Testes do ciclo de vida — triagem e atribuição (F4.1; TU09, TU10) com PG real.

- TU09 (triagem): NOVO → PENDENTE por ANALISTA/ADMIN; CLIENTE não pode (403);
  pode ajustar categoria/severidade; grava histórico.
- TU10 (atribuição, RN03): atribuir exige técnico ANALISTA/ADMIN **ativo**;
  técnico CLIENTE → 409; analista só a si mesmo; transição inválida → 409.
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(
    app: TestClient, sessao: Session, email: str, *, perfil: str = "CLIENTE"
) -> tuple[str, int]:
    uid = criar_usuario(
        sessao, email=email, senha="senha-ok-123456", nome=email.split("@")[0], perfil=perfil
    )
    r = app.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"]), uid


def _id_categoria(sessao: Session) -> int:
    return int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )


def _abrir(app: TestClient, token: str, id_cat: int, *, severidade: str = "BAIXA") -> int:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={
            "id_categoria": id_cat,
            "titulo": "Para o ciclo de vida",
            "descricao": "Deve ser triado e atribuído.",
            "severidade": severidade,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return int(r.json()["id_chamado"])


# ===== TU09 — Triagem =====


def test_tu09_triagem_novo_para_pendente(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_an, _ = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    r = app_integrado.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_an), json={})
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["status_chamado"] == "PENDENTE"
    assert r.json()["status_grupo"] == "abertos"

    # Histórico tem o evento NOVO→PENDENTE.
    hist = app_integrado.get(f"/api/chamados/{id_ch}/historico", headers=_auth(t_an)).json()
    assert any(e["status_novo"] == "PENDENTE" and e["status_anterior"] == "NOVO" for e in hist)


def test_tu09_triagem_ajusta_severidade(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_an, _ = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco), severidade="BAIXA")

    r = app_integrado.post(
        f"/api/chamados/{id_ch}/triagem", headers=_auth(t_an), json={"severidade": "ALTA"}
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["severidade"] == "ALTA"


def test_tu09_cliente_nao_pode_triar_403(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    r = app_integrado.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_cli), json={})
    assert r.status_code == status.HTTP_403_FORBIDDEN
    assert r.json()["codigo"] == "SEM_PERMISSAO"


def test_tu09_triagem_so_de_novo(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_an, _ = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    assert (
        app_integrado.post(
            f"/api/chamados/{id_ch}/triagem", headers=_auth(t_an), json={}
        ).status_code
        == status.HTTP_200_OK
    )
    # Triar de novo (já PENDENTE) → transição inválida.
    r2 = app_integrado.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_an), json={})
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert r2.json()["codigo"] == "TRANSICAO_INVALIDA"


# ===== TU10 — Atribuição (RN03) =====


def test_tu10_admin_atribui_a_analista(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_admin, _ = _login(app_integrado, sessao_banco, "admin2@exemplo.com.br", perfil="ADMIN")
    _, id_an = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    r = app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_admin), json={"id_tecnico": id_an}
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["status_chamado"] == "ATRIBUIDO"
    assert r.json()["tecnico_responsavel"]["id_usuario"] == id_an


def test_tu10_rn03_tecnico_cliente_rejeitado(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    t_cli, id_cli = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_admin, _ = _login(app_integrado, sessao_banco, "admin2@exemplo.com.br", perfil="ADMIN")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    # Tentar atribuir a um CLIENTE → RN03 recusa.
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_admin), json={"id_tecnico": id_cli}
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["codigo"] == "RN03_TECNICO_INVALIDO"


def test_tu10_rn03_tecnico_inativo_rejeitado(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_admin, _ = _login(app_integrado, sessao_banco, "admin2@exemplo.com.br", perfil="ADMIN")
    _, id_an = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    # Inativa o analista.
    sessao_banco.execute(
        text("UPDATE usuarios SET ativo = false WHERE id_usuario = :id"), {"id": id_an}
    )
    sessao_banco.flush()
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    r = app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_admin), json={"id_tecnico": id_an}
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["codigo"] == "RN03_TECNICO_INVALIDO"


def test_tu10_analista_so_atribui_a_si(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_an, id_an = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")
    _, id_outro = _login(app_integrado, sessao_banco, "outro@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app_integrado, t_cli, _id_categoria(sessao_banco))

    # Analista tenta atribuir a OUTRO analista → 403.
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_an), json={"id_tecnico": id_outro}
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN
    # A si mesmo → ok.
    r_ok = app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_an), json={"id_tecnico": id_an}
    )
    assert r_ok.status_code == status.HTTP_200_OK


def test_tecnicos_endpoint_analista_ve(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _ = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    t_an, _ = _login(app_integrado, sessao_banco, "analista@exemplo.com.br", perfil="ANALISTA")

    # CLIENTE não pode listar técnicos (403); ANALISTA pode.
    assert (
        app_integrado.get("/api/usuarios/tecnicos", headers=_auth(t_cli)).status_code
        == status.HTTP_403_FORBIDDEN
    )
    r = app_integrado.get("/api/usuarios/tecnicos", headers=_auth(t_an))
    assert r.status_code == status.HTTP_200_OK
    nomes = {t["nome"] for t in r.json()}
    assert "analista" in nomes
