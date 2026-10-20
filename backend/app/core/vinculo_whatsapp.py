"""Código de vínculo do WhatsApp no Redis (seção 9.4, F6.3).

Prova de posse: a API gera um código de 6 dígitos e guarda, no Redis, o mapa
`sha256(codigo) → id_usuario` com TTL de 10 minutos (chave `wa:vinculo:{hash}`).
O código em claro só volta uma vez, para a tela montar o link `wa.me`. Quando o
bot receber `VINCULAR <codigo>` (F6.4), ele consulta e consome esse mapa.

Guardamos só o hash: se o Redis for inspecionado, o código não fica em claro.
Nada aqui é durável — se o Redis zerar, o usuário gera outro código.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import cast

import redis

from app.core.redis import chave

TTL_SEGUNDOS = 10 * 60


def _hash(codigo: str) -> str:
    return hashlib.sha256(codigo.strip().encode("utf-8")).hexdigest()


def _chave(codigo: str) -> str:
    return chave(f"wa:vinculo:{_hash(codigo)}")


class VinculoWhatsApp:
    def __init__(self, redis_cliente: redis.Redis) -> None:
        self._redis = redis_cliente

    def gerar(self, id_usuario: int) -> str:
        """Gera um código de 6 dígitos e guarda `hash → id_usuario` com TTL. Devolve o código."""
        codigo = f"{secrets.randbelow(1_000_000):06d}"
        self._redis.set(_chave(codigo), str(id_usuario), ex=TTL_SEGUNDOS)
        return codigo

    def consultar(self, codigo: str) -> int | None:
        """Id do usuário dono do código, se válido e não expirado (não consome)."""
        valor = cast("str | None", self._redis.get(_chave(codigo)))
        if valor is None:
            return None
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None

    def consumir(self, codigo: str) -> int | None:
        """Como `consultar`, mas apaga o código (uso único, chamado pelo bot em F6.4)."""
        id_usuario = self.consultar(codigo)
        if id_usuario is not None:
            self._redis.delete(_chave(codigo))
        return id_usuario
