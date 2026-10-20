"""Worker (F0.2 heartbeat + F6.2 despacho do outbox).

Roda como `python -m app.worker`. Responsabilidades:

- manter o `worker:heartbeat` no Redis (TTL 30 s, seção 5.5) para o healthcheck;
- quando `OUTBOX_HABILITADO=true`, a cada 2 s reservar um lote do `eventos_outbox`
  (seção 9.2) e despachar ao n8n, marcando ENVIADO (2xx) ou aplicando backoff/
  retentativa na falha (até 8 tentativas → FALHOU).

Com `OUTBOX_HABILITADO=false` (padrão) o laço só mantém o heartbeat; os eventos
ficam PENDENTE até a integração ser ligada.
"""

from __future__ import annotations

import logging
import signal
import time
from datetime import UTC, datetime
from types import FrameType

from app.core.config import Configuracao, obter_configuracao
from app.core.database import FabricaSessao
from app.core.logging import configurar_logs
from app.core.redis import chave, criar_cliente_redis
from app.integrations.despacho import Despachante, DespachanteN8N, ErroDespacho
from app.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger("app.worker")

CHAVE_HEARTBEAT = "worker:heartbeat"
TTL_HEARTBEAT_SEGUNDOS = 30
INTERVALO_HEARTBEAT_SEGUNDOS = 10
INTERVALO_DESPACHO_SEGUNDOS = 2
LOTE = 20

_parar = False


def _tratar_sinal(_signum: int, _frame: FrameType | None) -> None:
    global _parar
    _parar = True


def _construir_despachante(config: Configuracao) -> Despachante | None:
    """Despachante n8n quando a integração está ligada e configurada; senão None."""
    if not config.outbox_habilitado:
        return None
    if not config.n8n_webhook_notificacoes_url:
        logger.warning(
            "OUTBOX_HABILITADO=true, mas N8N_WEBHOOK_NOTIFICACOES_URL vazio; sem despacho"
        )
        return None
    return DespachanteN8N(
        url=config.n8n_webhook_notificacoes_url,
        token=config.n8n_webhook_token,
    )


def despachar_lote(despachante: Despachante, *, lote: int = LOTE) -> int:
    """Reserva e despacha um lote. Devolve quantos eventos foram processados.

    Cada evento é confirmado (ENVIADO) ou tem a falha registrada (backoff/FALHOU)
    em sua própria transação, para que uma falha não desfaça os sucessos do lote.
    """
    sessao = FabricaSessao()
    try:
        repo = OutboxRepository(sessao)
        eventos = repo.reservar_lote(limite=lote)
        sessao.commit()  # confirma a reserva (PROCESSANDO) antes de sair despachando
    except Exception:
        sessao.rollback()
        sessao.close()
        raise

    processados = 0
    for evento in eventos:
        id_evento = evento.id_evento
        try:
            despachante.enviar(evento)
        except ErroDespacho as exc:
            novo = repo.registrar_falha(id_evento, str(exc))
            sessao.commit()
            logger.warning("evento %s falhou (%s): %s", id_evento, novo.value, exc)
        else:
            repo.marcar_enviado(id_evento)
            sessao.commit()
            logger.info("evento %s enviado", id_evento)
        processados += 1
    sessao.close()
    return processados


def main() -> None:
    config = obter_configuracao()
    configurar_logs(config.log_level)

    signal.signal(signal.SIGTERM, _tratar_sinal)
    signal.signal(signal.SIGINT, _tratar_sinal)

    cliente = criar_cliente_redis()
    despachante = _construir_despachante(config)
    logger.info("worker iniciado (outbox_habilitado=%s)", config.outbox_habilitado)

    ultimo_heartbeat = 0.0
    while not _parar:
        agora_mono = time.monotonic()
        if agora_mono - ultimo_heartbeat >= INTERVALO_HEARTBEAT_SEGUNDOS:
            marca = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            cliente.set(chave(CHAVE_HEARTBEAT), marca, ex=TTL_HEARTBEAT_SEGUNDOS)
            ultimo_heartbeat = agora_mono

        if despachante is not None:
            try:
                despachar_lote(despachante)
            except Exception:  # nunca derruba o laço por causa de um ciclo
                logger.exception("erro no ciclo de despacho do outbox")

        # Dorme em passos de 1 s para responder rápido ao SIGTERM.
        for _ in range(INTERVALO_DESPACHO_SEGUNDOS):
            if _parar:
                break
            time.sleep(1)

    logger.info("worker encerrado")


if __name__ == "__main__":
    main()
