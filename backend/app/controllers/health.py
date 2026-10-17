"""Verificações de saúde (seção 7.2, DoD do Documento 02).

- `GET /api/health`: a API está de pé (não toca em dependências).
- `GET /api/health/db`: executa `SELECT 1` para confirmar a conexão com o banco.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import obter_sessao
from app.core.errors import ErroAPI

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", summary="Vida da API")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db", summary="Conexão com o banco (SELECT 1)")
def health_db(sessao: Annotated[Session, Depends(obter_sessao)]) -> dict[str, str]:
    try:
        sessao.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ErroAPI(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            codigo="BANCO_INDISPONIVEL",
            mensagem="Banco de dados indisponível.",
        ) from exc
    return {"status": "ok", "db": "ok"}
