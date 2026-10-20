"""Estado efêmero do bot no Redis (seção 9.5): deduplicação de mensagens e estado
da conversa com TTL. Nada aqui é durável — se o Redis zerar, a conversa recomeça.
"""

from __future__ import annotations

import json
from typing import Any, cast

import redis

from app.core.redis import chave

TTL_DEDUP_SEGUNDOS = 24 * 60 * 60  # id de mensagem por 24 h (basta para o retry do n8n)
TTL_CONVERSA_SEGUNDOS = 30 * 60  # conversa expira em 30 min sem mensagem (seção 9.5)


class EstadoBot:
    def __init__(self, redis_cliente: redis.Redis) -> None:
        self._redis = redis_cliente

    def ja_processada(self, message_id: str) -> bool:
        """Marca a mensagem e diz se já havia sido vista (dedup, `SET NX`).

        Devolve True se a mensagem é repetida (não deve ser processada de novo).
        """
        if not message_id:
            return False
        reservado = self._redis.set(
            chave(f"wa:msg:{message_id}"), "1", nx=True, ex=TTL_DEDUP_SEGUNDOS
        )
        return not bool(reservado)

    def obter_conversa(self, chat_id: str) -> dict[str, Any]:
        bruto = cast("str | None", self._redis.get(chave(f"wa:conversa:{chat_id}")))
        if not bruto:
            return {}
        try:
            return cast("dict[str, Any]", json.loads(bruto))
        except (ValueError, TypeError):
            return {}

    def salvar_conversa(self, chat_id: str, estado: dict[str, Any]) -> None:
        self._redis.set(
            chave(f"wa:conversa:{chat_id}"),
            json.dumps(estado),
            ex=TTL_CONVERSA_SEGUNDOS,
        )

    def limpar_conversa(self, chat_id: str) -> None:
        self._redis.delete(chave(f"wa:conversa:{chat_id}"))

    # ----- sessão do WAHA (status para /admin/integracoes) -----

    def salvar_sessao(self, estado: dict[str, Any]) -> None:
        """Guarda o último status da sessão do WhatsApp (sem TTL: é o estado atual)."""
        self._redis.set(chave("wa:sessao"), json.dumps(estado))

    def obter_sessao(self) -> dict[str, Any]:
        bruto = cast("str | None", self._redis.get(chave("wa:sessao")))
        if not bruto:
            return {}
        try:
            return cast("dict[str, Any]", json.loads(bruto))
        except (ValueError, TypeError):
            return {}
