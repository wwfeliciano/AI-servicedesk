"""Cliente Redis para estado efêmero (seção 5.5).

Na F0.2 é usado só pelo worker, para gravar o `worker:heartbeat`. As chaves de
negócio (rate limit, conversa do bot etc.) entram nas fases seguintes, sempre com
o prefixo `REDIS_PREFIXO` e com TTL.
"""

from __future__ import annotations

import redis

from app.core.config import obter_configuracao


def criar_cliente_redis() -> redis.Redis:
    config = obter_configuracao()
    return redis.Redis.from_url(config.redis_url, decode_responses=True)


def chave(nome: str) -> str:
    """Aplica o prefixo configurado a uma chave do Redis."""
    return f"{obter_configuracao().redis_prefixo}{nome}"
