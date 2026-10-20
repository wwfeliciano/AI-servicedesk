"""Testes do contrato do despachante e do gating do worker (F6.2), sem rede."""

from __future__ import annotations

from app.core.config import Configuracao
from app.entities.enums import CanalNotificacao, StatusOutbox
from app.entities.eventos_outbox import EventoOutbox
from app.integrations.despacho import montar_contrato
from app.worker import _construir_despachante


def test_montar_contrato_segue_a_secao_9_2() -> None:
    evento = EventoOutbox(
        tipo="SOLUCAO_REGISTRADA",
        canal=CanalNotificacao.WHATSAPP,
        destino="5515999990000@c.us",
        payload={"texto": "responda 1 ou 2"},
        status=StatusOutbox.PENDENTE,
    )
    evento.id_evento = 981
    contrato = montar_contrato(evento)
    assert contrato == {
        "id_evento": 981,
        "tipo": "SOLUCAO_REGISTRADA",
        "canal": "WHATSAPP",
        "destino": "5515999990000@c.us",
        "mensagem": {"texto": "responda 1 ou 2"},
    }


def test_despachante_desligado_quando_outbox_off() -> None:
    config = Configuracao(outbox_habilitado=False, n8n_webhook_notificacoes_url="http://n8n/x")
    assert _construir_despachante(config) is None


def test_despachante_desligado_sem_url() -> None:
    config = Configuracao(outbox_habilitado=True, n8n_webhook_notificacoes_url="")
    assert _construir_despachante(config) is None


def test_despachante_ligado_com_url() -> None:
    config = Configuracao(outbox_habilitado=True, n8n_webhook_notificacoes_url="http://n8n/x")
    assert _construir_despachante(config) is not None
