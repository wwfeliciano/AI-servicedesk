"""Despachante do outbox → n8n (seção 9.2, F6.2).

Monta o contrato enviado ao n8n e faz o POST com timeout de 10 s e os headers
`X-Mentory-Token` (chave compartilhada) e `X-Evento-Id` (idempotência: o n8n
descarta ids repetidos). Resposta 2xx → sucesso; qualquer outra coisa → falha,
tratada pelo worker com backoff.

O n8n é só transporte: nenhuma regra de negócio aqui.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from app.entities.eventos_outbox import EventoOutbox

TIMEOUT_SEGUNDOS = 10.0


def montar_contrato(evento: EventoOutbox) -> dict[str, Any]:
    """Corpo enviado ao n8n (seção 9.2)."""
    return {
        "id_evento": evento.id_evento,
        "tipo": evento.tipo,
        "canal": evento.canal.value,
        "destino": evento.destino,
        "mensagem": evento.payload,
    }


class ErroDespacho(Exception):
    """Falha ao entregar um evento ao n8n (rede, timeout ou status != 2xx)."""


class Despachante(Protocol):
    def enviar(self, evento: EventoOutbox) -> None: ...


class DespachanteN8N:
    """Despachante HTTP real (produção/dev com a integração ligada)."""

    def __init__(self, *, url: str, token: str, timeout: float = TIMEOUT_SEGUNDOS) -> None:
        self._url = url
        self._token = token
        self._timeout = timeout

    def enviar(self, evento: EventoOutbox) -> None:
        cabecalhos = {
            "X-Mentory-Token": self._token,
            "X-Evento-Id": str(evento.id_evento),
        }
        try:
            resposta = httpx.post(
                self._url,
                json=montar_contrato(evento),
                headers=cabecalhos,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:  # rede/timeout
            raise ErroDespacho(f"erro de rede ao enviar ao n8n: {exc}") from exc
        if resposta.status_code // 100 != 2:
            raise ErroDespacho(f"n8n respondeu {resposta.status_code}: {resposta.text[:200]}")
