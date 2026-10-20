"""Controller de categorias (GET /api/categorias, autenticado; F2.1, RF05).

Lista as categorias ativas, ordenadas por `ordem`, para a etapa 1 do wizard de
abertura. Exige apenas estar autenticado (qualquer perfil).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.dependencias import ChamadoServiceDep, usuario_atual
from app.controllers.schemas_chamados import CategoriaSaida

router = APIRouter(
    prefix="/api/categorias",
    tags=["categorias"],
    dependencies=[Depends(usuario_atual)],
)


@router.get("", response_model=list[CategoriaSaida], summary="Categorias ativas (autenticado)")
def listar(servico: ChamadoServiceDep) -> list[CategoriaSaida]:
    return [
        CategoriaSaida(
            id_categoria=c.id_categoria,
            nome_categoria=c.nome_categoria,
            icone=c.icone,
            ordem=c.ordem,
            ativa=c.ativa,
        )
        for c in servico.listar_categorias()
    ]
