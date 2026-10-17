"""Montagem da aplicação FastAPI (`create_app`).

Responsabilidades da F0.2: configurar logs JSON, propagar o `X-Request-ID`,
registrar os handlers de erro (formato único) e incluir o router de health.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.controllers import health
from app.core.config import Configuracao, obter_configuracao
from app.core.errors import registrar_handlers_erro
from app.core.logging import configurar_logs, request_id_var

CABECALHO_REQUEST_ID = "X-Request-ID"


def create_app() -> FastAPI:
    config: Configuracao = obter_configuracao()
    configurar_logs(config.log_level)

    app = FastAPI(
        title="Mentory Help Desk API",
        version="0.0.0",
        docs_url="/api/docs" if config.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if config.docs_habilitado else None,
    )

    @app.middleware("http")
    async def middleware_request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Propaga o X-Request-ID recebido ou gera um novo; fica disponível nos logs.
        request_id = request.headers.get(CABECALHO_REQUEST_ID) or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[CABECALHO_REQUEST_ID] = request_id
        return response

    registrar_handlers_erro(app)
    app.include_router(health.router)
    return app


app = create_app()
