"""Controller das integrações do WhatsApp (F6.4, seção 9.3).

`POST /api/integracoes/whatsapp/mensagens`: o n8n repassa a mensagem recebida do
WAHA e a API devolve as respostas do bot. Autenticação pela chave compartilhada
no header `X-Integracao-Chave` (não é usuário logado).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, status
from pydantic import BaseModel

from app.controllers.dependencias import BotServiceDep, EstadoBotDep
from app.core.config import obter_configuracao
from app.core.errors import ErroAPI
from app.services.bot_service import MensagemRecebida

router = APIRouter(prefix="/api/integracoes/whatsapp", tags=["integracoes"])


class MensagemEntrada(BaseModel):
    message_id: str
    chat_id: str
    lid: str | None = None
    numero: str | None = None
    texto: str = ""
    tem_midia: bool = False
    timestamp: int | None = None


class RespostaBot(BaseModel):
    texto: str


class RespostasSaida(BaseModel):
    respostas: list[RespostaBot]


def _exigir_chave(x_integracao_chave: str | None) -> None:
    esperada = obter_configuracao().integracao_api_key
    # Sem chave configurada, o endpoint fica indisponível (evita bot aberto).
    if not esperada or x_integracao_chave != esperada:
        raise ErroAPI(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="NAO_AUTENTICADO",
            mensagem="Chave de integração inválida.",
        )


@router.post("/mensagens", response_model=RespostasSaida, summary="Mensagem recebida → bot")
def mensagens_recebidas(
    dados: MensagemEntrada,
    servico: BotServiceDep,
    x_integracao_chave: str | None = Header(default=None),
) -> RespostasSaida:
    _exigir_chave(x_integracao_chave)
    respostas = servico.processar(
        MensagemRecebida(
            message_id=dados.message_id,
            chat_id=dados.chat_id,
            lid=dados.lid,
            numero=dados.numero,
            texto=dados.texto,
            tem_midia=dados.tem_midia,
        )
    )
    return RespostasSaida(respostas=[RespostaBot(texto=t) for t in respostas])


class SessaoEntrada(BaseModel):
    status: str
    detalhe: str | None = None


class SessaoAceita(BaseModel):
    ok: bool = True


@router.post("/sessao", response_model=SessaoAceita, summary="Status da sessão do WAHA")
def sessao(
    dados: SessaoEntrada,
    estado: EstadoBotDep,
    x_integracao_chave: str | None = Header(default=None),
) -> SessaoAceita:
    """O n8n repassa o `session.status` do WAHA; guardamos para `/admin/integracoes`."""
    _exigir_chave(x_integracao_chave)
    import datetime

    estado.salvar_sessao(
        {
            "status": dados.status,
            "detalhe": dados.detalhe,
            "atualizado_em": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    )
    return SessaoAceita()
