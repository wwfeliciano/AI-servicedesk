"""Testes do despacho do outbox (F6.2, seção 9.2).

- `reservar_lote`: PENDENTE vencido vira PROCESSANDO com bloqueio; não repega o
  mesmo evento num segundo lote (dentro do bloqueio);
- `marcar_enviado`: → ENVIADO com `enviado_em`;
- `registrar_falha`: conta a tentativa, reagenda (backoff) e, na 8ª, vira FALHOU;
- `despachar_lote` (worker): com despachante fake OK → ENVIADO; com falha → PENDENTE;
- endpoints admin: `GET /api/admin/outbox` (contadores) e `POST .../reenviar`
  (FALHOU → PENDENTE), só ADMIN.
"""

from __future__ import annotations

from app.entities.enums import CanalNotificacao, StatusOutbox
from app.entities.eventos_outbox import EventoOutbox
from app.repositories.outbox_repository import MAX_TENTATIVAS, OutboxRepository
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import criar_usuario


def _enfileirar(sessao: Session, destino: str = "ana@empresa.com.br") -> int:
    repo = OutboxRepository(sessao)
    evento = repo.enfileirar(
        tipo="CHAMADO_CRIADO",
        canal=CanalNotificacao.EMAIL,
        destino=destino,
        payload={"assunto": "x", "texto": "y"},
    )
    sessao.commit()
    return evento.id_evento


def test_reservar_lote_marca_processando_e_pula_bloqueados(sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco)
    repo = OutboxRepository(sessao_banco)

    lote = repo.reservar_lote(limite=10)
    sessao_banco.commit()
    ids = {e.id_evento for e in lote}
    assert id_ev in ids
    reservado = sessao_banco.get(EventoOutbox, id_ev)
    assert reservado is not None and reservado.status == StatusOutbox.PROCESSANDO
    assert reservado.bloqueado_ate is not None

    # Um segundo lote imediato não repega (ainda está dentro do bloqueio).
    lote2 = repo.reservar_lote(limite=10)
    sessao_banco.commit()
    assert id_ev not in {e.id_evento for e in lote2}


def test_marcar_enviado(sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco)
    repo = OutboxRepository(sessao_banco)
    repo.marcar_enviado(id_ev)
    sessao_banco.commit()
    ev = sessao_banco.get(EventoOutbox, id_ev)
    assert ev is not None
    assert ev.status == StatusOutbox.ENVIADO
    assert ev.enviado_em is not None


def test_registrar_falha_reagenda_e_depois_falhou(sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco)
    repo = OutboxRepository(sessao_banco)

    # Primeira falha: reagenda (PENDENTE) com backoff.
    novo = repo.registrar_falha(id_ev, "timeout")
    sessao_banco.commit()
    assert novo == StatusOutbox.PENDENTE
    ev = sessao_banco.get(EventoOutbox, id_ev)
    assert ev is not None and ev.tentativas == 1 and ev.ultimo_erro == "timeout"

    # Chega a MAX_TENTATIVAS → FALHOU.
    for _ in range(MAX_TENTATIVAS - 1):
        novo = repo.registrar_falha(id_ev, "500")
        sessao_banco.commit()
    assert novo == StatusOutbox.FALHOU
    ev = sessao_banco.get(EventoOutbox, id_ev)
    assert ev is not None and ev.tentativas == MAX_TENTATIVAS


class _DespachanteOK:
    def __init__(self) -> None:
        self.enviados: list[int] = []

    def enviar(self, evento: EventoOutbox) -> None:
        self.enviados.append(evento.id_evento)


class _DespachanteFalha:
    def enviar(self, evento: EventoOutbox) -> None:
        from app.integrations.despacho import ErroDespacho

        raise ErroDespacho("n8n fora do ar")


def _ciclo_despacho(sessao: Session, despachante: object) -> None:
    """Reproduz o despacho de um lote na MESMA sessão do teste (a sessão de teste
    roda numa transação isolada e desfeita; o `FabricaSessao` do worker usa outra
    conexão e não enxergaria os eventos). Cobre a mesma lógica reserva→enviar/falhar."""
    from app.integrations.despacho import ErroDespacho

    repo = OutboxRepository(sessao)
    for evento in repo.reservar_lote(limite=10):
        try:
            despachante.enviar(evento)  # type: ignore[attr-defined]
        except ErroDespacho as exc:
            repo.registrar_falha(evento.id_evento, str(exc))
        else:
            repo.marcar_enviado(evento.id_evento)
    sessao.flush()


def test_despacho_ok_marca_enviado(sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco, destino="ok@empresa.com.br")
    despachante = _DespachanteOK()

    _ciclo_despacho(sessao_banco, despachante)

    assert id_ev in despachante.enviados
    ev = sessao_banco.get(EventoOutbox, id_ev)
    assert ev is not None and ev.status == StatusOutbox.ENVIADO


def test_despacho_falha_mantem_pendente(sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco, destino="falha@empresa.com.br")

    _ciclo_despacho(sessao_banco, _DespachanteFalha())

    ev = sessao_banco.get(EventoOutbox, id_ev)
    assert ev is not None
    assert ev.status == StatusOutbox.PENDENTE
    assert ev.tentativas == 1


# ===== Endpoints admin =====


def _login(app: TestClient, sessao: Session, email: str, *, perfil: str) -> str:
    criar_usuario(
        sessao, email=email, senha="senha-ok-123456", nome=email.split("@")[0], perfil=perfil
    )
    r = app.post("/api/auth/login", json={"email": email, "senha": "senha-ok-123456"})
    assert r.status_code == status.HTTP_200_OK
    return str(r.json()["access_token"])


def test_admin_outbox_lista_com_contadores(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    _enfileirar(sessao_banco, destino="lista@empresa.com.br")
    token = _login(app_integrado, sessao_banco, "adm.ob1@empresa.com.br", perfil="ADMIN")

    r = app_integrado.get("/api/admin/outbox", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == status.HTTP_200_OK, r.text
    corpo = r.json()
    assert corpo["total"] >= 1
    assert "PENDENTE" in corpo["contadores"]


def test_admin_outbox_cliente_recebe_403(app_integrado: TestClient, sessao_banco: Session) -> None:
    token = _login(app_integrado, sessao_banco, "cli.ob@empresa.com.br", perfil="CLIENTE")
    r = app_integrado.get("/api/admin/outbox", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_admin_outbox_reenviar(app_integrado: TestClient, sessao_banco: Session) -> None:
    id_ev = _enfileirar(sessao_banco, destino="reenviar@empresa.com.br")
    # Leva o evento a FALHOU.
    repo = OutboxRepository(sessao_banco)
    for _ in range(MAX_TENTATIVAS):
        repo.registrar_falha(id_ev, "erro")
    sessao_banco.commit()

    token = _login(app_integrado, sessao_banco, "adm.ob2@empresa.com.br", perfil="ADMIN")
    r = app_integrado.post(
        f"/api/admin/outbox/{id_ev}/reenviar", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["status"] == "PENDENTE"
    assert r.json()["tentativas"] == 0


def test_admin_outbox_reenviar_inexistente_404(
    app_integrado: TestClient, sessao_banco: Session
) -> None:
    token = _login(app_integrado, sessao_banco, "adm.ob3@empresa.com.br", perfil="ADMIN")
    r = app_integrado.post(
        "/api/admin/outbox/999999/reenviar", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == status.HTTP_404_NOT_FOUND
