"""Testes do bot de atendimento do WhatsApp (F6.4, seção 9.3/9.5).

- chave de integração inválida → 401;
- deduplicação: a mesma `message_id` não gera resposta de novo;
- número não vinculado recebe instruções de vínculo;
- `VINCULAR <código>` completa o vínculo (código gerado no Perfil, mesmo Redis);
- código inválido → mensagem de erro;
- menu; *2* lista os chamados em aberto do próprio; protocolo mostra o status (RN06);
- `SAIR` faz opt-out (desvincula).
"""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario

CHAVE = {"X-Integracao-Chave": "chave-de-teste"}
CHAT = "5515988887777@c.us"


def _mensagem(texto: str, *, chat_id: str = CHAT, mid: str = "m1", tem_midia: bool = False) -> dict:
    return {
        "message_id": mid,
        "chat_id": chat_id,
        "numero": chat_id.split("@")[0],
        "texto": texto,
        "tem_midia": tem_midia,
    }


def _post(app: TestClient, corpo: dict, *, chave: dict[str, str] | None = CHAVE):
    return app.post("/api/integracoes/whatsapp/mensagens", json=corpo, headers=chave or {})


def _vincular_direto(sessao: Session, id_usuario: int, chat_id: str = CHAT) -> None:
    sessao.execute(
        text(
            "UPDATE usuarios SET whatsapp_chat_id = :cid, whatsapp_numero = :num, "
            "whatsapp_opt_in = true WHERE id_usuario = :id"
        ),
        {"cid": chat_id, "num": chat_id.split("@")[0], "id": id_usuario},
    )
    sessao.flush()
    sessao.expire_all()


def test_chave_invalida_401(app_integrado: TestClient) -> None:
    r = _post(app_integrado, _mensagem("oi"), chave={"X-Integracao-Chave": "errada"})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_numero_nao_vinculado_recebe_instrucoes(app_integrado: TestClient) -> None:
    r = _post(app_integrado, _mensagem("oi", mid="nv1"))
    assert r.status_code == status.HTTP_200_OK
    texto = r.json()["respostas"][0]["texto"]
    assert "Perfil" in texto and "VINCULAR" in texto


def test_dedup_nao_responde_duas_vezes(app_integrado: TestClient) -> None:
    r1 = _post(app_integrado, _mensagem("oi", mid="dup1"))
    assert len(r1.json()["respostas"]) == 1
    r2 = _post(app_integrado, _mensagem("oi", mid="dup1"))
    assert r2.json()["respostas"] == []


def test_vincular_completa_o_vinculo(app_integrado: TestClient, sessao_banco: Session) -> None:
    # Cria o usuário e gera o código pelo Perfil (mesmo Redis do bot).
    email = "bot.vinculo@empresa.com.br"
    criar_usuario(sessao_banco, email=email, senha="senha-ok-123456", nome="Bia")
    login = app_integrado.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    token = login.json()["access_token"]
    vinc = app_integrado.post(
        "/api/perfil/whatsapp/vinculo",
        headers={"Authorization": f"Bearer {token}"},
        json={"consentimento": True},
    )
    codigo = vinc.json()["codigo"]

    r = _post(app_integrado, _mensagem(f"VINCULAR {codigo}", mid="vinc-ok"))
    assert r.status_code == status.HTTP_200_OK
    assert "vinculado" in r.json()["respostas"][0]["texto"].lower()

    # Agora o número é reconhecido: "menu" responde o menu.
    sessao_banco.expire_all()
    r2 = _post(app_integrado, _mensagem("menu", mid="vinc-ok-2"))
    assert "Mentory Help Desk" in r2.json()["respostas"][0]["texto"]


def test_vincular_codigo_invalido(app_integrado: TestClient) -> None:
    r = _post(app_integrado, _mensagem("VINCULAR 000000", mid="vinc-bad"))
    assert "inválido" in r.json()["respostas"][0]["texto"].lower()


def test_menu_e_meus_chamados(app_integrado: TestClient, sessao_banco: Session) -> None:
    uid = criar_usuario(
        sessao_banco, email="bot.menu@empresa.com.br", senha="senha-ok-123456", nome="Caio"
    )
    _vincular_direto(sessao_banco, uid)
    # Abre um chamado para esse usuário (login + POST).
    login = app_integrado.post(
        "/api/auth/login", json={"email": "bot.menu@empresa.com.br", "senha": "senha-ok-123456"}
    )
    token = login.json()["access_token"]
    id_cat = int(
        sessao_banco.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )
    app_integrado.post(
        "/api/chamados",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_categoria": id_cat,
            "titulo": "Bot lista",
            "descricao": "x",
            "severidade": "BAIXA",
        },
    )
    sessao_banco.expire_all()

    r = _post(app_integrado, _mensagem("2", mid="menu-2"))
    assert r.status_code == status.HTTP_200_OK
    assert "em aberto" in r.json()["respostas"][0]["texto"]


def test_status_do_proprio_por_protocolo(app_integrado: TestClient, sessao_banco: Session) -> None:
    uid = criar_usuario(
        sessao_banco, email="bot.status@empresa.com.br", senha="senha-ok-123456", nome="Dani"
    )
    _vincular_direto(sessao_banco, uid, chat_id="5515900000001@c.us")
    login = app_integrado.post(
        "/api/auth/login", json={"email": "bot.status@empresa.com.br", "senha": "senha-ok-123456"}
    )
    token = login.json()["access_token"]
    id_cat = int(
        sessao_banco.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )
    novo = app_integrado.post(
        "/api/chamados",
        headers={"Authorization": f"Bearer {token}"},
        json={"id_categoria": id_cat, "titulo": "Bot status", "descricao": "x"},
    )
    protocolo = novo.json()["protocolo"]
    sessao_banco.expire_all()

    r = _post(
        app_integrado,
        _mensagem(protocolo, chat_id="5515900000001@c.us", mid="st-1"),
    )
    assert protocolo in r.json()["respostas"][0]["texto"]


def test_sair_faz_opt_out(app_integrado: TestClient, sessao_banco: Session) -> None:
    uid = criar_usuario(
        sessao_banco, email="bot.sair@empresa.com.br", senha="senha-ok-123456", nome="Edu"
    )
    _vincular_direto(sessao_banco, uid, chat_id="5515900000002@c.us")

    r = _post(app_integrado, _mensagem("SAIR", chat_id="5515900000002@c.us", mid="sair-1"))
    assert "não receberá" in r.json()["respostas"][0]["texto"].lower()
    sessao_banco.expire_all()
    vinculado = sessao_banco.execute(
        text("SELECT whatsapp_chat_id FROM usuarios WHERE id_usuario = :id"), {"id": uid}
    ).scalar_one()
    assert vinculado is None


# ===== F6.4b — fluxo guiado de abertura =====


def _resposta(r) -> str:
    return r.json()["respostas"][0]["texto"]


def test_fluxo_guiado_abre_chamado(app_integrado: TestClient, sessao_banco: Session) -> None:
    chat = "5515900000010@c.us"
    uid = criar_usuario(
        sessao_banco, email="bot.abrir@empresa.com.br", senha="senha-ok-123456", nome="Fabi"
    )
    _vincular_direto(sessao_banco, uid, chat_id=chat)

    # 1 → categoria; escolhe a 1ª categoria; prioridade 2; título; descrição; confirma (1).
    r = _post(app_integrado, _mensagem("1", chat_id=chat, mid="g1"))
    assert "categoria" in _resposta(r).lower()
    r = _post(app_integrado, _mensagem("1", chat_id=chat, mid="g2"))
    assert "prioridade" in _resposta(r).lower()
    r = _post(app_integrado, _mensagem("2", chat_id=chat, mid="g3"))
    assert "título" in _resposta(r).lower()
    r = _post(app_integrado, _mensagem("VPN não conecta", chat_id=chat, mid="g4"))
    assert "descreva" in _resposta(r).lower()
    r = _post(app_integrado, _mensagem("Desde ontem a VPN cai.", chat_id=chat, mid="g5"))
    assert "Confere" in _resposta(r)
    r = _post(app_integrado, _mensagem("1", chat_id=chat, mid="g6"))
    texto = _resposta(r)
    assert "Chamado aberto" in texto and "TK-" in texto

    # O chamado nasceu com canal_origem=WHATSAPP.
    sessao_banco.expire_all()
    canal = sessao_banco.execute(
        text(
            "SELECT canal_origem FROM chamados "
            "WHERE id_usuario_abertura = :id ORDER BY id_chamado DESC LIMIT 1"
        ),
        {"id": uid},
    ).scalar_one()
    assert canal == "WHATSAPP"


def test_fluxo_guiado_cancelar(app_integrado: TestClient, sessao_banco: Session) -> None:
    chat = "5515900000011@c.us"
    uid = criar_usuario(
        sessao_banco, email="bot.cancela@empresa.com.br", senha="senha-ok-123456", nome="Gui"
    )
    _vincular_direto(sessao_banco, uid, chat_id=chat)
    _post(app_integrado, _mensagem("1", chat_id=chat, mid="c1"))
    r = _post(app_integrado, _mensagem("cancelar", chat_id=chat, mid="c2"))
    assert "cancel" in _resposta(r).lower()


# ===== F6.4b — aprovação da solução pelo WhatsApp =====


def _abrir_concluir(app: TestClient, sessao: Session, chat: str) -> tuple[int, str, int]:
    """Cria cliente+analista, abre um chamado e registra a solução (CONCLUIDO).

    Devolve (id_chamado, protocolo, id_cliente)."""
    cid = criar_usuario(sessao, email="cli.apr@empresa.com.br", senha="senha-ok-123456", nome="Cli")
    _vincular_direto(sessao, cid, chat_id=chat)
    criar_usuario(sessao, email="ana.apr@empresa.com.br", senha="senha-ok-123456", perfil="ADMIN")
    tcli = app.post(
        "/api/auth/login", json={"email": "cli.apr@empresa.com.br", "senha": "senha-ok-123456"}
    ).json()["access_token"]
    tadm = app.post(
        "/api/auth/login", json={"email": "ana.apr@empresa.com.br", "senha": "senha-ok-123456"}
    ).json()["access_token"]
    id_cat = int(
        sessao.execute(
            text("SELECT id_categoria FROM categorias WHERE ativa ORDER BY ordem LIMIT 1")
        ).scalar_one()
    )
    novo = app.post(
        "/api/chamados",
        headers={"Authorization": f"Bearer {tcli}"},
        json={"id_categoria": id_cat, "titulo": "Aprovar via wa", "descricao": "x"},
    ).json()
    idc = novo["id_chamado"]
    # Atribui a si (admin) e registra solução → CONCLUIDO.
    app.post(
        f"/api/chamados/{idc}/atribuicao",
        headers={"Authorization": f"Bearer {tadm}"},
        json={"id_tecnico": _id_de(sessao, "ana.apr@empresa.com.br")},
    )
    app.post(
        f"/api/chamados/{idc}/solucoes",
        headers={"Authorization": f"Bearer {tadm}"},
        json={"descricao_solucao": "Reinstalei o cliente VPN."},
    )
    sessao.expire_all()
    return idc, novo["protocolo"], cid


def _id_de(sessao: Session, email: str) -> int:
    return int(
        sessao.execute(
            text("SELECT id_usuario FROM usuarios WHERE email = :e"), {"e": email}
        ).scalar_one()
    )


def test_aprovar_solucao_pelo_whatsapp(app_integrado: TestClient, sessao_banco: Session) -> None:
    chat = "5515900000020@c.us"
    idc, protocolo, _cid = _abrir_concluir(app_integrado, sessao_banco, chat)

    # Consulta o protocolo (arma o estado de aprovação) e depois envia "1".
    _post(app_integrado, _mensagem(protocolo, chat_id=chat, mid="a1"))
    r = _post(app_integrado, _mensagem("1", chat_id=chat, mid="a2"))
    assert "aprovada" in _resposta(r).lower()

    sessao_banco.expire_all()
    status_final = sessao_banco.execute(
        text("SELECT status_chamado FROM chamados WHERE id_chamado = :id"), {"id": idc}
    ).scalar_one()
    assert status_final == "FECHADO"


def test_reprovar_por_comando(app_integrado: TestClient, sessao_banco: Session) -> None:
    chat = "5515900000021@c.us"
    idc, protocolo, _cid = _abrir_concluir(app_integrado, sessao_banco, chat)

    r = _post(
        app_integrado,
        _mensagem(f"REPROVAR {protocolo} não resolveu", chat_id=chat, mid="r1"),
    )
    assert "reprovada" in _resposta(r).lower()
    sessao_banco.expire_all()
    status_final = sessao_banco.execute(
        text("SELECT status_chamado FROM chamados WHERE id_chamado = :id"), {"id": idc}
    ).scalar_one()
    assert status_final == "ATRIBUIDO"


# ===== F6.4b — sessão e /admin/integracoes =====


def test_sessao_e_admin_integracoes(app_integrado: TestClient, sessao_banco: Session) -> None:
    # POST da sessão (endpoint com chave de integração).
    r = app_integrado.post(
        "/api/integracoes/whatsapp/sessao",
        headers=CHAVE,
        json={"status": "WORKING", "detalhe": "ok"},
    )
    assert r.status_code == status.HTTP_200_OK

    criar_usuario(
        sessao_banco, email="adm.int@empresa.com.br", senha="senha-ok-123456", perfil="ADMIN"
    )
    token = app_integrado.post(
        "/api/auth/login", json={"email": "adm.int@empresa.com.br", "senha": "senha-ok-123456"}
    ).json()["access_token"]
    g = app_integrado.get("/api/admin/integracoes", headers={"Authorization": f"Bearer {token}"})
    assert g.status_code == status.HTTP_200_OK
    assert g.json()["status"] == "WORKING"
