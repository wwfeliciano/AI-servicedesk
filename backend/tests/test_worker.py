"""Teste do heartbeat do worker (F0.2) usando fakeredis."""

from __future__ import annotations

import fakeredis
from app.worker import CHAVE_HEARTBEAT, TTL_HEARTBEAT_SEGUNDOS


def test_heartbeat_grava_chave_com_ttl() -> None:
    cliente = fakeredis.FakeRedis(decode_responses=True)

    # Reproduz o passo de heartbeat do laço do worker.
    chave = f"mentory:{CHAVE_HEARTBEAT}"
    cliente.set(chave, "2026-10-17T00:00:00Z", ex=TTL_HEARTBEAT_SEGUNDOS)

    assert cliente.get(chave) == "2026-10-17T00:00:00Z"
    ttl = cliente.ttl(chave)
    assert 0 < ttl <= TTL_HEARTBEAT_SEGUNDOS
