"""Formato único de erro da API (seção 7.1).

Toda resposta de erro tem o corpo:

    {
      "codigo": "VALIDACAO",
      "mensagem": "Mensagem em PT-BR.",
      "campos": { "email": "..." }   // opcional
    }

`ErroAPI` é a exceção de domínio levantada pelos services/controllers. Os handlers
registrados em `app.main` convertem também os erros do FastAPI/Pydantic e qualquer
exceção não tratada para este mesmo formato.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Mapa de status HTTP → código padrão de erro (seção 7.1).
CODIGO_POR_STATUS: dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: "NAO_AUTENTICADO",
    status.HTTP_403_FORBIDDEN: "SEM_PERMISSAO",
    status.HTTP_404_NOT_FOUND: "NAO_ENCONTRADO",
    status.HTTP_409_CONFLICT: "CONFLITO",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "ARQUIVO_GRANDE",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "TIPO_ARQUIVO_INVALIDO",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDACAO",
    status.HTTP_429_TOO_MANY_REQUESTS: "MUITAS_TENTATIVAS",
}

MENSAGEM_PADRAO: dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: "Não autenticado.",
    status.HTTP_403_FORBIDDEN: "Você não tem permissão para esta ação.",
    status.HTTP_404_NOT_FOUND: "Recurso não encontrado.",
    status.HTTP_409_CONFLICT: "Conflito com o estado atual.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Dados inválidos.",
    status.HTTP_429_TOO_MANY_REQUESTS: "Muitas tentativas. Aguarde alguns minutos.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Erro interno. Tente novamente mais tarde.",
}

# Detalhes padrão em inglês do Starlette/FastAPI: devem ceder à mensagem PT-BR.
_DETALHES_GENERICOS: frozenset[str] = frozenset(
    {"Not Found", "Method Not Allowed", "Forbidden", "Unauthorized", "Internal Server Error"}
)


class ErroAPI(Exception):
    """Erro de domínio com o contrato da seção 7.1."""

    def __init__(
        self,
        *,
        status_code: int,
        codigo: str,
        mensagem: str,
        campos: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.campos = campos


def _corpo(codigo: str, mensagem: str, campos: dict[str, str] | None) -> dict[str, Any]:
    corpo: dict[str, Any] = {"codigo": codigo, "mensagem": mensagem}
    if campos:
        corpo["campos"] = campos
    return corpo


def registrar_handlers_erro(app: FastAPI) -> None:
    """Registra os handlers que normalizam todos os erros para o formato único."""

    @app.exception_handler(ErroAPI)
    async def _tratar_erro_api(_: Request, exc: ErroAPI) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_corpo(exc.codigo, exc.mensagem, exc.campos),
        )

    @app.exception_handler(RequestValidationError)
    async def _tratar_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
        campos: dict[str, str] = {}
        for erro in exc.errors():
            # Pula o primeiro elemento do loc ("body", "query"...) para nomear o campo.
            partes = [str(p) for p in erro.get("loc", ()) if p not in ("body", "query", "path")]
            nome = ".".join(partes) or "corpo"
            campos[nome] = erro.get("msg", "Valor inválido.")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_corpo("VALIDACAO", "Dados inválidos.", campos or None),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _tratar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo = CODIGO_POR_STATUS.get(exc.status_code, "ERRO")
        # Detalhes genéricos em inglês do próprio framework viram a mensagem PT-BR padrão.
        detail = exc.detail if isinstance(exc.detail, str) else ""
        detail_customizado = bool(detail) and detail not in _DETALHES_GENERICOS
        mensagem = detail if detail_customizado else MENSAGEM_PADRAO.get(exc.status_code, "Erro.")
        return JSONResponse(status_code=exc.status_code, content=_corpo(codigo, mensagem, None))

    @app.exception_handler(Exception)
    async def _tratar_inesperado(_: Request, exc: Exception) -> JSONResponse:
        # Não vaza detalhes internos ao cliente; o traceback vai para o log.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_corpo(
                "ERRO_INTERNO",
                MENSAGEM_PADRAO[status.HTTP_500_INTERNAL_SERVER_ERROR],
                None,
            ),
        )
