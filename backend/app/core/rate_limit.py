"""Limite de tentativas de login (seção 11, RNF01).

Conta tentativas falhas por IP e por e-mail no Redis, com janela de 15 minutos.
Ao atingir o limite (5), o login é recusado com `429` até a janela expirar. Só o
estado efêmero fica no Redis (seção 5.5); nada importante se perde se for zerado.

Usa `redis.Redis` de forma estrutural (duck typing), o que permite `fakeredis` nos
testes sem acoplar o tipo concreto.
"""

from __future__ import annotations

from typing import cast

import redis

from app.core.redis import chave

LIMITE_TENTATIVAS = 5
JANELA_SEGUNDOS = 15 * 60


class LimiteTentativasLogin:
    def __init__(self, redis_cliente: redis.Redis) -> None:
        self._redis = redis_cliente

    @staticmethod
    def _chave_ip(ip: str) -> str:
        return chave(f"rl:login:ip:{ip}")

    @staticmethod
    def _chave_email(email: str) -> str:
        return chave(f"rl:login:email:{email.strip().lower()}")

    def _excedeu(self, nome_chave: str) -> bool:
        valor = cast("str | None", self._redis.get(nome_chave))
        try:
            return valor is not None and int(valor) >= LIMITE_TENTATIVAS
        except (TypeError, ValueError):
            return False

    def bloqueado(self, *, ip: str, email: str) -> bool:
        """True se IP ou e-mail já atingiram o limite na janela atual."""
        return self._excedeu(self._chave_ip(ip)) or self._excedeu(self._chave_email(email))

    def registrar_falha(self, *, ip: str, email: str) -> None:
        """Conta uma tentativa falha para IP e e-mail, criando a janela de TTL."""
        for nome_chave in (self._chave_ip(ip), self._chave_email(email)):
            atual = self._redis.incr(nome_chave)
            if atual == 1:
                self._redis.expire(nome_chave, JANELA_SEGUNDOS)

    def limpar(self, *, ip: str, email: str) -> None:
        """Zera os contadores após um login bem-sucedido."""
        self._redis.delete(self._chave_ip(ip), self._chave_email(email))
