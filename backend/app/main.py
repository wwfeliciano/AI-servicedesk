"""Montagem da aplicação FastAPI (`create_app`).

Responsabilidades da F0.2: configurar logs JSON, propagar o `X-Request-ID`,
registrar os handlers de erro (formato único) e incluir o router de health.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.controllers import (
    admin_integracoes,
    admin_outbox,
    anexos,
    auth,
    base_conhecimento,
    categorias,
    chamados,
    health,
    integracoes,
    notificacoes,
    perfil,
    sla,
    usuarios,
)
from app.controllers import config as config_publica
from app.core.config import Configuracao, obter_configuracao
from app.core.errors import registrar_handlers_erro
from app.core.logging import configurar_logs, request_id_var

CABECALHO_REQUEST_ID = "X-Request-ID"


def _garantir_buckets(config: Configuracao) -> None:
    """Cria os buckets de anexos/backups no MinIO se não existirem (seção 5.6).
    Resiliente: uma falha de conexão não derruba a API. Pulado em testes."""
    import logging

    from app.core.storage import criar_storage

    if config.ambiente.lower() == "test":
        return
    try:
        storage = criar_storage(config)
        storage.garantir_buckets(config.s3_bucket_anexos, config.s3_bucket_backups)
    except Exception:  # pragma: no cover - depende do MinIO no ar
        logging.getLogger("mentory").warning("Não foi possível garantir os buckets do S3.")


def create_app() -> FastAPI:
    config: Configuracao = obter_configuracao()
    configurar_logs(config.log_level)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        _garantir_buckets(config)
        yield

    app = FastAPI(
        title="Mentory Help Desk API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs" if config.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if config.docs_habilitado else None,
    )

    # CORS só em desenvolvimento (seção 11): em produção, front e API têm a mesma origem.
    if not config.em_producao and config.lista_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.lista_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
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
    app.include_router(config_publica.router)
    app.include_router(auth.router)
    app.include_router(usuarios.router_tecnicos)
    app.include_router(usuarios.router)
    app.include_router(categorias.router)
    app.include_router(chamados.router)
    app.include_router(chamados.router_solucoes)
    app.include_router(anexos.router)
    app.include_router(notificacoes.router)
    app.include_router(perfil.router)
    app.include_router(integracoes.router)
    app.include_router(sla.router)
    app.include_router(base_conhecimento.router)
    app.include_router(base_conhecimento.router_escrita)
    app.include_router(admin_outbox.router)
    app.include_router(admin_integracoes.router)

    return app


app = create_app()
