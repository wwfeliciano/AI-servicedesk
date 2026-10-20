"""Testes dos canais externos — outbox (F6.1).

Cobrem a matriz de canais (seção 9.6) e as preferências de cada destinatário:

- `CHAMADO_CRIADO`: portal + e-mail (sempre, enquanto `notificar_email`) + WhatsApp
  (só com vínculo e opt-in);
- e-mail respeita `notificar_email`; WhatsApp exige `whatsapp_chat_id` + opt-in;
- `STATUS_ALTERADO` (triagem) não gera outbox (só portal);
- tudo na mesma transação da abertura (o chamado e as linhas do outbox coexistem).
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
            "titulo": "Evento de outbox",
            "descricao": "Deve gerar linhas no outbox.",
            "severidade": severidade,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return int(r.json()["id_chamado"])


def _vincular_whatsapp(sessao: Session, id_usuario: int, chat_id: str) -> None:
    sessao.execute(
        text(
            "UPDATE usuarios SET whatsapp_chat_id = :cid, whatsapp_numero = :num, "
            "whatsapp_opt_in = true WHERE id_usuario = :id"
        ),
        {"cid": chat_id, "num": chat_id.split("@")[0], "id": id_usuario},
    )
    sessao.flush()


def _outbox(sessao: Session, id_chamado: int) -> list[tuple[str, str, str]]:
    """(tipo, canal, destino) das linhas do outbox de um chamado (via link no payload)."""
    linhas = sessao.execute(
        text(
            "SELECT tipo, canal::text, destino FROM eventos_outbox "
            "WHERE payload::text LIKE :p ORDER BY id_evento"
        ),
        {"p": f"%/chamados/{id_chamado}%"},
    ).all()
    return [(t, c, d) for (t, c, d) in linhas]


# ===== TU — matriz de canais na abertura =====


def test_tu17_chamado_criado_email_e_whatsapp(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    """Solicitante vinculado e com e-mail: a abertura gera e-mail + WhatsApp no outbox."""
    token, uid = _login(app_integrado, sessao_banco, "cli.outbox1@empresa.com.br")
    _vincular_whatsapp(sessao_banco, uid, "5515999990000@c.us")
    id_cat = _id_categoria(sessao_banco)

    id_chamado = _abrir(app_integrado, token, id_cat)

    linhas = _outbox(sessao_banco, id_chamado)
    canais = {(t, c) for (t, c, _d) in linhas}
    assert ("CHAMADO_CRIADO", "EMAIL") in canais
    assert ("CHAMADO_CRIADO", "WHATSAPP") in canais
    # Destino correto por canal.
    for _tipo, canal, destino in linhas:
        if canal == "EMAIL":
            assert destino == "cli.outbox1@empresa.com.br"
        if canal == "WHATSAPP":
            assert destino == "5515999990000@c.us"


def test_tu17_sem_whatsapp_so_email(app_integrado: TestClient, sessao_banco: Session) -> None:
    """Sem vínculo de WhatsApp: só e-mail (não há linha WhatsApp)."""
    token, _uid = _login(app_integrado, sessao_banco, "cli.outbox2@empresa.com.br")
    id_cat = _id_categoria(sessao_banco)

    id_chamado = _abrir(app_integrado, token, id_cat)

    canais = {c for (_t, c, _d) in _outbox(sessao_banco, id_chamado)}
    assert canais == {"EMAIL"}


def test_tu17_email_desligado_nao_enfileira_email(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    """Com `notificar_email=false` e sem WhatsApp: nenhum evento de outbox."""
    token, uid = _login(app_integrado, sessao_banco, "cli.outbox3@empresa.com.br")
    sessao_banco.execute(
        text("UPDATE usuarios SET notificar_email = false WHERE id_usuario = :id"),
        {"id": uid},
    )
    sessao_banco.flush()
    id_cat = _id_categoria(sessao_banco)

    id_chamado = _abrir(app_integrado, token, id_cat)

    assert _outbox(sessao_banco, id_chamado) == []


def test_tu17_triagem_nao_gera_outbox(app_integrado: TestClient, sessao_banco: Session) -> None:
    """STATUS_ALTERADO (triagem) é só portal — não entra no outbox (matriz 9.6)."""
    token_cli, uid = _login(app_integrado, sessao_banco, "cli.outbox4@empresa.com.br")
    _vincular_whatsapp(sessao_banco, uid, "5515999990001@c.us")
    token_adm, _ = _login(app_integrado, sessao_banco, "adm.outbox4@empresa.com.br", perfil="ADMIN")
    id_cat = _id_categoria(sessao_banco)
    id_chamado = _abrir(app_integrado, token_cli, id_cat)

    # Zera o que a abertura gerou para medir só a triagem.
    sessao_banco.execute(
        text("DELETE FROM eventos_outbox WHERE payload::text LIKE :p"),
        {"p": f"%/chamados/{id_chamado}%"},
    )
    sessao_banco.flush()

    r = app_integrado.post(f"/api/chamados/{id_chamado}/triagem", headers=_auth(token_adm), json={})
    assert r.status_code == status.HTTP_200_OK, r.text

    assert _outbox(sessao_banco, id_chamado) == []


def test_tu17_urgente_alerta_tecnico_no_outbox(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    """Abertura CRITICO: o técnico ativo (vinculado + e-mail) recebe CHAMADO_URGENTE."""
    _token_adm, id_adm = _login(
        app_integrado, sessao_banco, "adm.urgente@empresa.com.br", perfil="ADMIN"
    )
    _vincular_whatsapp(sessao_banco, id_adm, "5515999990002@c.us")
    token_cli, _ = _login(app_integrado, sessao_banco, "cli.urgente@empresa.com.br")
    id_cat = _id_categoria(sessao_banco)

    id_chamado = _abrir(app_integrado, token_cli, id_cat, severidade="CRITICO")

    tipos = {t for (t, _c, _d) in _outbox(sessao_banco, id_chamado)}
    assert "CHAMADO_URGENTE" in tipos
    # O alerta urgente foi para o chat do técnico também.
    destinos_wa = {d for (_t, c, d) in _outbox(sessao_banco, id_chamado) if c == "WHATSAPP"}
    assert "5515999990002@c.us" in destinos_wa
