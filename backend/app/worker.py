"""Worker (esqueleto da F0.2).

Roda como `python -m app.worker`. Por enquanto só mantém vivo o `worker:heartbeat`
no Redis (TTL de 30 s, seção 5.5), usado no healthcheck do serviço `worker`. O
despacho do outbox (seção 9.2) entra na F6, sem mudar este laço base.
"""

from __future__ import annotations

import logging
import signal
import time
from datetime import UTC, datetime
from types import FrameType

from app.core.config import obter_configuracao
from app.core.logging import configurar_logs
from app.core.redis import chave, criar_cliente_redis

logger = logging.getLogger("app.worker")

CHAVE_HEARTBEAT = "worker:heartbeat"
TTL_HEARTBEAT_SEGUNDOS = 30
INTERVALO_SEGUNDOS = 10

_parar = False


def _tratar_sinal(_signum: int, _frame: FrameType | None) -> None:
    global _parar
    _parar = True


def main() -> None:
    config = obter_configuracao()
    configurar_logs(config.log_level)

    signal.signal(signal.SIGTERM, _tratar_sinal)
    signal.signal(signal.SIGINT, _tratar_sinal)

    cliente = criar_cliente_redis()
    logger.info("worker iniciado")

    while not _parar:
        agora = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        cliente.set(chave(CHAVE_HEARTBEAT), agora, ex=TTL_HEARTBEAT_SEGUNDOS)
        # Dorme em passos curtos para responder rápido ao SIGTERM.
        for _ in range(INTERVALO_SEGUNDOS):
            if _parar:
                break
            time.sleep(1)

    logger.info("worker encerrado")


if __name__ == "__main__":
    main()
