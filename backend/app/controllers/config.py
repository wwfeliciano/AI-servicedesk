"""Controller da configuração pública (GET /api/config/publica, seção 7.2).

Rota pública (sem autenticação) consumida pela tela de login: informa os canais
de suporte, se o login com Google está disponível e a versão da API. Não expõe
nenhum segredo — só valores já destinados à interface.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import obter_configuracao

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigPublica(BaseModel):
    whatsapp_suporte: str | None
    email_suporte: str | None
    google_sso: bool
    versao: str


@router.get("/publica", response_model=ConfigPublica, summary="Config pública (tela de login)")
def config_publica() -> ConfigPublica:
    config = obter_configuracao()
    whatsapp = config.whatsapp_numero_suporte.strip() or None
    email = config.email_suporte.strip() or None
    return ConfigPublica(
        whatsapp_suporte=whatsapp,
        email_suporte=email,
        google_sso=config.google_sso,
        versao=config.versao,
    )
