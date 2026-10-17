"""Logs estruturados em JSON (seção 11).

Cada linha é um objeto JSON com `timestamp`, `level`, `logger`, `mensagem` e, quando
disponível, o `request_id` da requisição em curso. O `request_id` é propagado por um
`ContextVar` preenchido pelo middleware (`app.main`).

Dados sensíveis (e-mail, telefone, chat_id, tokens) nunca devem ser logados; este
módulo não registra corpo de requisição nem credenciais.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from contextvars import ContextVar

# Preenchido pelo middleware a cada requisição; vazio fora de um request (ex.: worker).
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class FormatadorJson(logging.Formatter):
    """Formata cada registro de log como uma linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        momento = dt.datetime.fromtimestamp(record.created, tz=dt.UTC)
        dados: dict[str, object] = {
            "timestamp": momento.isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "mensagem": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id is not None:
            dados["request_id"] = request_id

        # Campos extras passados via `logger.info(..., extra={...})`.
        for chave, valor in getattr(record, "extra_campos", {}).items():
            dados[chave] = valor

        if record.exc_info:
            dados["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(dados, ensure_ascii=False)


def configurar_logs(nivel: str = "INFO") -> None:
    """Configura o root logger para emitir JSON em stdout (idempotente)."""
    raiz = logging.getLogger()
    raiz.setLevel(nivel.upper())

    # Remove handlers anteriores para não duplicar linhas (reconfiguração/testes).
    for handler in list(raiz.handlers):
        raiz.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(FormatadorJson())
    raiz.addHandler(handler)

    # Uvicorn: deixa os logs de acesso/erro passarem pelo root (sem formato próprio).
    for nome in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger_uvicorn = logging.getLogger(nome)
        logger_uvicorn.handlers.clear()
        logger_uvicorn.propagate = True
