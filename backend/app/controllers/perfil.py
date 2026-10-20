"""Controller do Perfil — WhatsApp e preferências (F6.3, seção 7.2).

- POST   /api/perfil/whatsapp/vinculo   → gera código + link wa.me (exige consentimento)
- GET    /api/perfil/whatsapp           → status do vínculo
- DELETE /api/perfil/whatsapp           → desvincula (opt-out)
- PATCH  /api/perfil/preferencias       → notificar_email / whatsapp_opt_in

Tudo do próprio usuário autenticado (nunca recebe id de outro no corpo).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.controllers.dependencias import PerfilServiceDep, UsuarioAtualDep, usuario_atual
from app.core.errors import ErroAPI
from app.services.perfil_service import ErroPerfil, StatusVinculo

router = APIRouter(
    prefix="/api/perfil",
    tags=["perfil"],
    dependencies=[Depends(usuario_atual)],
)


class VinculoEntrada(BaseModel):
    consentimento: bool = False


class VinculoSaida(BaseModel):
    codigo: str
    link_wa: str
    expira_em_segundos: int


class StatusSaida(BaseModel):
    vinculado: bool
    numero: str | None
    opt_in: bool
    notificar_email: bool


class PreferenciasEntrada(BaseModel):
    notificar_email: bool | None = None
    whatsapp_opt_in: bool | None = None


def _status_saida(s: StatusVinculo) -> StatusSaida:
    return StatusSaida(
        vinculado=s.vinculado,
        numero=s.numero,
        opt_in=s.opt_in,
        notificar_email=s.notificar_email,
    )


@router.post("/whatsapp/vinculo", response_model=VinculoSaida, summary="Gera o vínculo do WhatsApp")
def gerar_vinculo(
    dados: VinculoEntrada,
    servico: PerfilServiceDep,
    usuario: UsuarioAtualDep,
) -> VinculoSaida:
    try:
        v = servico.gerar_vinculo(usuario, consentimento=dados.consentimento)
    except ErroPerfil as exc:
        codigo_http = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if exc.codigo == "CONSENTIMENTO_OBRIGATORIO"
            else status.HTTP_409_CONFLICT
        )
        raise ErroAPI(status_code=codigo_http, codigo=exc.codigo, mensagem=exc.mensagem) from exc
    return VinculoSaida(codigo=v.codigo, link_wa=v.link_wa, expira_em_segundos=v.expira_em_segundos)


@router.get("/whatsapp", response_model=StatusSaida, summary="Status do vínculo do WhatsApp")
def status_whatsapp(servico: PerfilServiceDep, usuario: UsuarioAtualDep) -> StatusSaida:
    return _status_saida(servico.status(usuario))


@router.delete("/whatsapp", response_model=StatusSaida, summary="Desvincula o WhatsApp (opt-out)")
def desvincular(servico: PerfilServiceDep, usuario: UsuarioAtualDep) -> StatusSaida:
    return _status_saida(servico.desvincular(usuario))


@router.patch("/preferencias", response_model=StatusSaida, summary="Preferências de notificação")
def atualizar_preferencias(
    dados: PreferenciasEntrada,
    servico: PerfilServiceDep,
    usuario: UsuarioAtualDep,
) -> StatusSaida:
    return _status_saida(
        servico.atualizar_preferencias(
            usuario,
            notificar_email=dados.notificar_email,
            whatsapp_opt_in=dados.whatsapp_opt_in,
        )
    )
