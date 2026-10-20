"""Status das integrações para o ADMIN (F6.4b).

`GET /api/admin/integracoes`: último status conhecido da sessão do WhatsApp (WAHA),
alimentado por `POST /api/integracoes/whatsapp/sessao`. A fila do outbox fica em
`/api/admin/outbox` (F6.2); a tela `/admin/integracoes` junta os dois.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.controllers.dependencias import EstadoBotDep, exigir_perfil
from app.entities.enums import PerfilUsuario

router = APIRouter(
    prefix="/api/admin/integracoes",
    tags=["admin-integracoes"],
    dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN))],
)


class SessaoWhatsappSaida(BaseModel):
    status: str
    detalhe: str | None = None
    atualizado_em: str | None = None


@router.get("", response_model=SessaoWhatsappSaida, summary="Status da sessão do WhatsApp (ADMIN)")
def status_integracoes(estado: EstadoBotDep) -> SessaoWhatsappSaida:
    sessao = estado.obter_sessao()
    return SessaoWhatsappSaida(
        status=sessao.get("status", "DESCONHECIDO"),
        detalhe=sessao.get("detalhe"),
        atualizado_em=sessao.get("atualizado_em"),
    )
