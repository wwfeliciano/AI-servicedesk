"""Testes do ciclo de vida — solução, aprovação, follow-ups e PATCH usuário (F4.2).

- TU11 (RN01): concluir exige solução; só do técnico responsável/ADMIN; só de ATRIBUIDO.
- TU12 (RN02): solicitante aprova → FECHADO + data_fechamento + solução APROVADO.
- TU13 (RN02): solicitante reprova (motivo obrigatório) → ATRIBUIDO + solução REJEITADO
  + motivo vira follow-up.
- TU14: follow-ups por participantes; chamado FECHADO bloqueia novo follow-up.
- PATCH /api/usuarios/{id}: ativar/desativar (exclusão lógica); ADMIN não desativa a si.
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


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


def _abrir(app: TestClient, token: str, id_cat: int) -> int:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={"id_categoria": id_cat, "titulo": "Fluxo F4.2", "descricao": "Do início ao fim."},
    )
    assert r.status_code == status.HTTP_201_CREATED
    return int(r.json()["id_chamado"])


def _ate_atribuido(app: TestClient, sessao: Session) -> tuple[str, str, int]:
    """Abre, tria e atribui ao analista; devolve (token_cliente, token_analista, id_chamado)."""
    t_cli, _ = _login(app, sessao, "cli@exemplo.com.br")
    t_an, id_an = _login(app, sessao, "analista@exemplo.com.br", perfil="ANALISTA")
    id_ch = _abrir(app, t_cli, _id_categoria(sessao))
    assert (
        app.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_an), json={}).status_code == 200
    )
    r = app.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_an), json={"id_tecnico": id_an}
    )
    assert r.status_code == 200
    return t_cli, t_an, id_ch


# ===== TU11 — Conclusão / RN01 =====


def test_tu11_concluir_registra_solucao(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/solucoes",
        headers=_auth(t_an),
        json={"descricao_solucao": "Reinstalei o cliente VPN e validei o acesso."},
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    assert r.json()["status_chamado"] == "CONCLUIDO"

    sols = app_integrado.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_cli)).json()
    assert len(sols) == 1
    assert sols[0]["status_aprovacao"] == "PENDENTE_APROVACAO"


def test_tu11_concluir_exige_descricao(app_integrado: TestClient, sessao_banco: Session) -> None:
    _, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_an), json={"descricao_solucao": "   "}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r.json()["codigo"] == "VALIDACAO"


def test_tu11_cliente_nao_conclui(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, _t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_cli), json={"descricao_solucao": "x"}
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# ===== TU12 / TU13 — Resposta do solicitante =====


def _concluir(app: TestClient, t_an: str, id_ch: int) -> int:
    app.post(
        f"/api/chamados/{id_ch}/solucoes",
        headers=_auth(t_an),
        json={"descricao_solucao": "Solução aplicada."},
    )
    sols = app.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_an)).json()
    return int(sols[0]["id_solucao"])


def test_tu12_aprovar_fecha(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    id_sol = _concluir(app_integrado, t_an, id_ch)

    r = app_integrado.post(
        f"/api/solucoes/{id_sol}/resposta", headers=_auth(t_cli), json={"aprovada": True}
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["status_chamado"] == "FECHADO"
    assert r.json()["status_grupo"] == "encerrados"

    # Solução ficou APROVADO; data_fechamento preenchida.
    sols = app_integrado.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_cli)).json()
    assert sols[0]["status_aprovacao"] == "APROVADO"
    df = sessao_banco.execute(
        text("SELECT data_fechamento FROM chamados WHERE id_chamado = :id"), {"id": id_ch}
    ).scalar_one()
    assert df is not None


def test_tu13_reprovar_volta_para_atribuido(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    id_sol = _concluir(app_integrado, t_an, id_ch)

    r = app_integrado.post(
        f"/api/solucoes/{id_sol}/resposta",
        headers=_auth(t_cli),
        json={"aprovada": False, "motivo": "O problema voltou a ocorrer."},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["status_chamado"] == "ATRIBUIDO"

    # Solução REJEITADO e o motivo virou follow-up.
    sols = app_integrado.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_cli)).json()
    assert sols[0]["status_aprovacao"] == "REJEITADO"
    fups = app_integrado.get(f"/api/chamados/{id_ch}/followups", headers=_auth(t_cli)).json()
    assert any("O problema voltou a ocorrer." in f["mensagem"] for f in fups)


def test_tu13_reprovar_exige_motivo(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    id_sol = _concluir(app_integrado, t_an, id_ch)
    r = app_integrado.post(
        f"/api/solucoes/{id_sol}/resposta", headers=_auth(t_cli), json={"aprovada": False}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r.json()["codigo"] == "VALIDACAO"


def test_so_solicitante_responde(app_integrado: TestClient, sessao_banco: Session) -> None:
    _t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    id_sol = _concluir(app_integrado, t_an, id_ch)
    # O analista (não solicitante) tenta responder → 403.
    r = app_integrado.post(
        f"/api/solucoes/{id_sol}/resposta", headers=_auth(t_an), json={"aprovada": True}
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# ===== TU14 — Follow-ups =====


def test_tu14_followup_participantes_e_fechado(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    t_cli, t_an, id_ch = _ate_atribuido(app_integrado, sessao_banco)
    # Um terceiro (não participante) não vê nem posta.
    t_outro, _ = _login(app_integrado, sessao_banco, "outro@exemplo.com.br")
    assert (
        app_integrado.get(f"/api/chamados/{id_ch}/followups", headers=_auth(t_outro)).status_code
        == status.HTTP_404_NOT_FOUND
    )

    # Solicitante posta um follow-up.
    r = app_integrado.post(
        f"/api/chamados/{id_ch}/followups",
        headers=_auth(t_cli),
        json={"mensagem": "Alguma novidade?"},
    )
    assert r.status_code == status.HTTP_201_CREATED

    # Conclui e aprova → FECHADO; novo follow-up é bloqueado.
    id_sol = _concluir(app_integrado, t_an, id_ch)
    app_integrado.post(
        f"/api/solucoes/{id_sol}/resposta", headers=_auth(t_cli), json={"aprovada": True}
    )
    r2 = app_integrado.post(
        f"/api/chamados/{id_ch}/followups", headers=_auth(t_cli), json={"mensagem": "mais uma"}
    )
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert r2.json()["codigo"] == "TRANSICAO_INVALIDA"


# ===== PATCH /api/usuarios/{id} =====


def test_patch_usuario_desativa_e_reativa(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_adm, _ = _login(app_integrado, sessao_banco, "admin2@exemplo.com.br", perfil="ADMIN")
    _, id_cli = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")

    r = app_integrado.patch(
        f"/api/usuarios/{id_cli}",
        headers=_auth(t_adm),
        json={"ativo": False, "cargo": "Ex-cliente"},
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["ativo"] is False
    assert r.json()["cargo"] == "Ex-cliente"

    r2 = app_integrado.patch(f"/api/usuarios/{id_cli}", headers=_auth(t_adm), json={"ativo": True})
    assert r2.json()["ativo"] is True


def test_patch_admin_nao_desativa_a_si(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_adm, id_adm = _login(app_integrado, sessao_banco, "admin2@exemplo.com.br", perfil="ADMIN")
    r = app_integrado.patch(f"/api/usuarios/{id_adm}", headers=_auth(t_adm), json={"ativo": False})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "ativo" in r.json()["campos"]


def test_patch_exige_admin(app_integrado: TestClient, sessao_banco: Session) -> None:
    t_cli, id_cli = _login(app_integrado, sessao_banco, "cli@exemplo.com.br")
    r = app_integrado.patch(f"/api/usuarios/{id_cli}", headers=_auth(t_cli), json={"nome": "X"})
    assert r.status_code == status.HTTP_403_FORBIDDEN
