"""Testes da consulta de chamados (F2.2) com PostgreSQL real.

Cobre a seção 7.3, a RN06 (escopo por perfil) e a 6.5 (ordenação/busca/contadores):
- lista paginada no escopo do perfil; CLIENTE só os seus;
- TU07 (RN06): CLIENTE pedindo o chamado de outro → 404; sem token → 401;
- TU08: filtro por grupo e categoria, busca por título e por protocolo, paginação
  e contadores (que ignoram o grupo);
- `/resumo` com os indicadores;
- ordenação: CRITICO ainda não resolvido vem primeiro.

Não fixa ids (sequências IDENTITY não voltam no rollback).
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


def _id_categorias(sessao: Session) -> list[int]:
    return [
        int(r[0])
        for r in sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem")
        ).all()
    ]


def _abrir(
    app: TestClient,
    token: str,
    *,
    id_categoria: int,
    titulo: str,
    descricao: str = "Descrição do chamado.",
    severidade: str = "BAIXA",
) -> dict[str, object]:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={
            "id_categoria": id_categoria,
            "titulo": titulo,
            "descricao": descricao,
            "severidade": severidade,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return dict(r.json())


# ===== Escopo e autenticação (RN06, TU07) =====


def test_lista_sem_token_401(app_integrado: TestClient) -> None:
    r = app_integrado.get("/api/chamados")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_cliente_ve_so_os_seus(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _id_categorias(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno@exemplo.com.br")

    _abrir(app_integrado, t_ana, id_categoria=cats[0], titulo="Problema da Ana")
    _abrir(app_integrado, t_bruno, id_categoria=cats[0], titulo="Problema do Bruno")

    r_ana = app_integrado.get("/api/chamados", headers=_auth(t_ana)).json()
    assert r_ana["total"] == 1
    assert r_ana["items"][0]["titulo"] == "Problema da Ana"
    assert r_ana["items"][0]["solicitante"]["nome"] == "ana"


def test_tu07_cliente_nao_ve_chamado_de_outro_404(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    cats = _id_categorias(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno@exemplo.com.br")
    do_bruno = _abrir(app_integrado, t_bruno, id_categoria=cats[0], titulo="Do Bruno")

    # Ana pede o chamado do Bruno → 404 (não revela que existe).
    r = app_integrado.get(f"/api/chamados/{do_bruno['id_chamado']}", headers=_auth(t_ana))
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert r.json()["codigo"] == "NAO_ENCONTRADO"
    # Bruno vê o seu.
    r_ok = app_integrado.get(f"/api/chamados/{do_bruno['id_chamado']}", headers=_auth(t_bruno))
    assert r_ok.status_code == status.HTTP_200_OK


def test_analista_ve_todos(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _id_categorias(sessao_banco)
    t_ana = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    t_bruno = _login(app_integrado, sessao_banco, "bruno@exemplo.com.br")
    t_tec = _login(app_integrado, sessao_banco, "tec@exemplo.com.br", perfil="ANALISTA")

    _abrir(app_integrado, t_ana, id_categoria=cats[0], titulo="Da Ana")
    _abrir(app_integrado, t_bruno, id_categoria=cats[0], titulo="Do Bruno")

    r = app_integrado.get("/api/chamados", headers=_auth(t_tec)).json()
    assert r["total"] == 2  # analista vê a fila inteira


# ===== Busca, filtros, contadores, paginação (TU08) =====


def test_tu08_busca_por_titulo_e_protocolo(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    c1 = _abrir(app_integrado, token, id_categoria=cats[0], titulo="VPN não conecta")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Impressora sem tinta")

    # Busca por título (sem acento, substring).
    r_titulo = app_integrado.get("/api/chamados", headers=_auth(token), params={"q": "vpn"}).json()
    assert r_titulo["total"] == 1
    assert r_titulo["items"][0]["titulo"] == "VPN não conecta"

    # Busca por protocolo (ex.: TK-0001 ou só o número).
    protocolo = str(c1["protocolo"])
    r_prot = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"q": protocolo}
    ).json()
    assert r_prot["total"] == 1
    assert r_prot["items"][0]["protocolo"] == protocolo


def test_tu08_filtro_grupo_e_categoria(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Na categoria 0")
    _abrir(app_integrado, token, id_categoria=cats[1], titulo="Na categoria 1")

    # Filtro por categoria.
    r_cat = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"id_categoria": cats[1]}
    ).json()
    assert r_cat["total"] == 1
    assert r_cat["items"][0]["categoria"]["id_categoria"] == cats[1]

    # Todos nascem NOVO → grupo "abertos" tem 2, "resolvidos" tem 0.
    r_abertos = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"grupo": "abertos"}
    ).json()
    assert r_abertos["total"] == 2
    r_resolv = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"grupo": "resolvidos"}
    ).json()
    assert r_resolv["total"] == 0


def test_tu08_contadores_ignoram_grupo_mas_respeitam_busca(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Alpha um")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Alpha dois")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Beta três")

    # Mesmo filtrando por grupo, os contadores refletem o conjunto sem o grupo,
    # mas respeitam a busca `q`.
    r = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"q": "alpha", "grupo": "resolvidos"}
    ).json()
    assert r["total"] == 0  # nenhum "alpha" está resolvido
    assert r["contadores"]["todos"] == 2  # os dois "alpha" (ignora o grupo)
    assert r["contadores"]["abertos"] == 2


def test_tu08_paginacao(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    for i in range(3):
        _abrir(app_integrado, token, id_categoria=cats[0], titulo=f"Chamado {i}")

    r = app_integrado.get(
        "/api/chamados", headers=_auth(token), params={"page": 1, "page_size": 2}
    ).json()
    assert r["total"] == 3
    assert len(r["items"]) == 2
    assert r["page_size"] == 2


def test_ordenacao_critico_nao_resolvido_primeiro(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Baixa antiga", severidade="BAIXA")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Urgente nova", severidade="CRITICO")

    r = app_integrado.get("/api/chamados", headers=_auth(token)).json()
    # O CRITICO (não resolvido) vem primeiro, apesar de ambos serem recentes.
    assert r["items"][0]["titulo"] == "Urgente nova"
    assert r["items"][0]["severidade"] == "CRITICO"


# ===== Resumo =====


def test_resumo_indicadores(app_integrado: TestClient, sessao_banco: Session) -> None:
    cats = _id_categorias(sessao_banco)
    token = _login(app_integrado, sessao_banco, "ana@exemplo.com.br")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Normal", severidade="MEDIA")
    _abrir(app_integrado, token, id_categoria=cats[0], titulo="Crítico", severidade="CRITICO")

    r = app_integrado.get("/api/chamados/resumo", headers=_auth(token)).json()
    assert r["abertos"] == 2  # ambos NOVO
    assert r["em_andamento"] == 0
    assert r["resolvidos"] == 0
    assert r["encerrados"] == 0
    assert r["urgentes"] == 1  # o CRITICO ainda não resolvido
