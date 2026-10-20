"""Testes do SLA do mês (F7.2, decisão B20).

- a abertura grava `prazo_sla = data_criacao + prazo_horas` da severidade
  (CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h);
- `GET /api/sla/mes`: entre os concluídos no mês, o percentual dentro do prazo —
  um concluído no prazo e outro fora resultam em 50%.
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(app: TestClient, sessao: Session, email: str) -> str:
    criar_usuario(sessao, email=email, senha="senha-ok-123456", nome=email.split("@")[0])
    r = app.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def _id_categoria(sessao: Session) -> int:
    return int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )


def _abrir(app: TestClient, token: str, id_cat: int, *, severidade: str) -> int:
    r = app.post(
        "/api/chamados",
        headers=_auth(token),
        json={
            "id_categoria": id_cat,
            "titulo": "SLA",
            "descricao": "x",
            "severidade": severidade,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return int(r.json()["id_chamado"])


def test_abertura_grava_prazo_sla(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "sla.prazo@empresa.com.br")
    id_cat = _id_categoria(sessao_banco)
    idc = _abrir(app_integrado, token, id_cat, severidade="ALTA")  # 8 h

    sessao_banco.expire_all()
    linha = sessao_banco.execute(
        text(
            "SELECT EXTRACT(EPOCH FROM (prazo_sla - data_criacao)) / 3600 AS horas "
            "FROM chamados WHERE id_chamado = :id"
        ),
        {"id": idc},
    ).scalar_one()
    assert round(float(linha)) == 8


def test_sla_do_mes_percentual(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "sla.mes@empresa.com.br")
    id_cat = _id_categoria(sessao_banco)
    no_prazo = _abrir(app_integrado, token, id_cat, severidade="ALTA")
    fora = _abrir(app_integrado, token, id_cat, severidade="ALTA")

    # Conclui os dois agora: um dentro do prazo, outro depois do prazo.
    # (atribui um técnico para satisfazer o CHECK RN03 ao sair de NOVO/PENDENTE)
    tecnico = sessao_banco.execute(
        text("SELECT id_usuario FROM usuarios WHERE email = 'sla.mes@empresa.com.br'")
    ).scalar_one()
    sessao_banco.execute(
        text(
            "UPDATE chamados SET status_chamado='CONCLUIDO', id_tecnico_responsavel = :t, "
            "data_conclusao = now() WHERE id_chamado = :id"
        ),
        {"id": no_prazo, "t": tecnico},
    )
    sessao_banco.execute(
        text(
            "UPDATE chamados SET status_chamado='CONCLUIDO', id_tecnico_responsavel = :t, "
            "data_conclusao = prazo_sla + interval '1 hour' WHERE id_chamado = :id"
        ),
        {"id": fora, "t": tecnico},
    )
    sessao_banco.flush()

    r = app_integrado.get("/api/sla/mes", headers=_auth(token))
    assert r.status_code == status.HTTP_200_OK, r.text
    corpo = r.json()
    assert corpo["total"] >= 2
    assert corpo["no_prazo"] >= 1
    # Com exatamente estes dois, seria 50%; como a suíte é isolada por transação,
    # são os únicos concluídos no mês.
    assert corpo["percentual"] == 50.0


def test_sla_mes_exige_autenticacao(app_integrado: TestClient) -> None:
    r = app_integrado.get("/api/sla/mes")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
