"""Testes da Base de Conhecimento (F5.1, TU15) com PostgreSQL real.

- RN05: publica só a partir de uma solução **APROVADA**; não duplica por solução.
- escrita (publicar/editar) só ANALISTA/ADMIN; leitura por qualquer autenticado.
- busca full-text encontra por termo **sem acento**; filtro por categoria.
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


def _categorias(sessao: Session) -> list[int]:
    return [
        int(r[0])
        for r in sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem")
        ).all()
    ]


def _solucao_aprovada(
    app: TestClient, sessao: Session, *, id_categoria: int, titulo_chamado: str
) -> tuple[int, str]:
    """Percorre o fluxo até FECHADO. Devolve (id_solucao_APROVADA, token_admin)."""
    t_cli, _ = _login(app, sessao, "cli.kb@exemplo.com.br")
    t_adm, id_adm = _login(app, sessao, "adm.kb@exemplo.com.br", perfil="ADMIN")
    r = app.post(
        "/api/chamados",
        headers=_auth(t_cli),
        json={"id_categoria": id_categoria, "titulo": titulo_chamado, "descricao": "x"},
    )
    id_ch = int(r.json()["id_chamado"])
    app.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_adm), json={})
    app.post(f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_adm), json={"id_tecnico": id_adm})
    app.post(
        f"/api/chamados/{id_ch}/solucoes",
        headers=_auth(t_adm),
        json={"descricao_solucao": "Passo a passo da solução."},
    )
    sols = app.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_cli)).json()
    id_sol = int(sols[0]["id_solucao"])
    app.post(f"/api/solucoes/{id_sol}/resposta", headers=_auth(t_cli), json={"aprovada": True})
    return id_sol, t_adm


def test_leitura_exige_autenticacao(app_integrado: TestClient) -> None:
    assert app_integrado.get("/api/base-conhecimento").status_code == status.HTTP_401_UNAUTHORIZED


def test_tu15_publica_de_solucao_aprovada(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _categorias(sessao_banco)
    id_sol, t_adm = _solucao_aprovada(
        app_integrado, sessao_banco, id_categoria=cats[0], titulo_chamado="VPN"
    )

    r = app_integrado.post(
        "/api/base-conhecimento",
        headers=_auth(t_adm),
        json={
            "id_solucao": id_sol,
            "titulo": "Como resolver a conexão de VPN",
            "conteudo": "Reinstale o cliente e valide o MFA.",
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    assert r.json()["categoria"]["nome_categoria"] == "TI"

    # Não duplica.
    r2 = app_integrado.post(
        "/api/base-conhecimento",
        headers=_auth(t_adm),
        json={"id_solucao": id_sol, "titulo": "Outra", "conteudo": "y"},
    )
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert r2.json()["codigo"] == "DUPLICADO"


def test_tu15_rn05_so_de_solucao_aprovada(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _categorias(sessao_banco)
    # Cria uma solução PENDENTE (conclui mas não aprova).
    t_cli, _ = _login(app_integrado, sessao_banco, "cli.kb@exemplo.com.br")
    t_adm, id_adm = _login(app_integrado, sessao_banco, "adm.kb@exemplo.com.br", perfil="ADMIN")
    id_ch = int(
        app_integrado.post(
            "/api/chamados",
            headers=_auth(t_cli),
            json={"id_categoria": cats[0], "titulo": "Pendente", "descricao": "x"},
        ).json()["id_chamado"]
    )
    app_integrado.post(f"/api/chamados/{id_ch}/triagem", headers=_auth(t_adm), json={})
    app_integrado.post(
        f"/api/chamados/{id_ch}/atribuicao", headers=_auth(t_adm), json={"id_tecnico": id_adm}
    )
    app_integrado.post(
        f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_adm), json={"descricao_solucao": "sol"}
    )
    id_sol = int(
        app_integrado.get(f"/api/chamados/{id_ch}/solucoes", headers=_auth(t_adm)).json()[0][
            "id_solucao"
        ]
    )

    r = app_integrado.post(
        "/api/base-conhecimento",
        headers=_auth(t_adm),
        json={"id_solucao": id_sol, "titulo": "T", "conteudo": "C"},
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["codigo"] == "SOLUCAO_NAO_APROVADA"


def test_tu15_escrita_so_analista_admin(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _categorias(sessao_banco)
    id_sol, _t_adm = _solucao_aprovada(
        app_integrado, sessao_banco, id_categoria=cats[0], titulo_chamado="VPN"
    )
    # cli.kb já existe (criado no fluxo); apenas autentica.
    t_cli = str(
        app_integrado.post(
            "/api/auth/login", json={"email": "cli.kb@exemplo.com.br", "senha": "senha-ok-123456"}
        ).json()["access_token"]
    )

    r = app_integrado.post(
        "/api/base-conhecimento",
        headers=_auth(t_cli),
        json={"id_solucao": id_sol, "titulo": "T", "conteudo": "C"},
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_tu15_busca_sem_acento_e_filtro_categoria(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    cats = _categorias(sessao_banco)
    id_sol, t_adm = _solucao_aprovada(
        app_integrado, sessao_banco, id_categoria=cats[0], titulo_chamado="VPN"
    )
    app_integrado.post(
        "/api/base-conhecimento",
        headers=_auth(t_adm),
        json={
            "id_solucao": id_sol,
            "titulo": "Configuração da impressão",
            "conteudo": "Ajuste a impressão de relatórios.",
        },
    )

    # Busca por termo sem acento encontra "Configuração"/"impressão".
    r = app_integrado.get(
        "/api/base-conhecimento", headers=_auth(t_adm), params={"q": "configuracao"}
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["total"] == 1
    assert "Configuração" in r.json()["items"][0]["titulo"]

    # Filtro por categoria: a certa (cats[0]) acha; outra não.
    r_cat = app_integrado.get(
        "/api/base-conhecimento", headers=_auth(t_adm), params={"id_categoria": cats[0]}
    )
    assert r_cat.json()["total"] == 1
    r_outra = app_integrado.get(
        "/api/base-conhecimento", headers=_auth(t_adm), params={"id_categoria": cats[1]}
    )
    assert r_outra.json()["total"] == 0


def test_tu15_editar_artigo(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _categorias(sessao_banco)
    id_sol, t_adm = _solucao_aprovada(
        app_integrado, sessao_banco, id_categoria=cats[0], titulo_chamado="VPN"
    )
    id_base = int(
        app_integrado.post(
            "/api/base-conhecimento",
            headers=_auth(t_adm),
            json={"id_solucao": id_sol, "titulo": "Antigo", "conteudo": "C"},
        ).json()["id_base"]
    )

    r = app_integrado.patch(
        f"/api/base-conhecimento/{id_base}", headers=_auth(t_adm), json={"titulo": "Novo título"}
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["titulo"] == "Novo título"
