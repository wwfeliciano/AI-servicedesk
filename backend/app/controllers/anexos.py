"""Controllers de anexos (F3.1; RF02, RN06, B9/B10).

- POST /api/chamados/{id}/anexos   → envia um arquivo (multipart) para o chamado
- GET  /api/chamados/{id}/anexos   → lista os anexos do chamado
- GET  /api/anexos/{id}/download    → baixa o arquivo (stream), respeitando o escopo

Erros (seção 7.1): tipo não permitido → 415; arquivo grande / vazio → 413; limite
de anexos → 409; chamado/anexo fora do escopo → 404.
"""

from __future__ import annotations

import datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.controllers.dependencias import AnexoServiceDep, UsuarioAtualDep
from app.core.errors import ErroAPI
from app.entities.anexo import Anexo
from app.services.anexo_service import ErroAnexo

router = APIRouter(tags=["anexos"])

_STATUS_POR_CODIGO = {
    "NAO_ENCONTRADO": status.HTTP_404_NOT_FOUND,
    "TIPO_ARQUIVO_INVALIDO": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    "ARQUIVO_GRANDE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    "ARQUIVO_VAZIO": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    "LIMITE_ANEXOS": status.HTTP_409_CONFLICT,
}


class AnexoSaida(BaseModel):
    id_anexo: int
    nome_original: str
    mime_type: str
    tamanho_bytes: int
    data_envio: datetime.datetime


def _erro_http(exc: ErroAnexo) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_400_BAD_REQUEST)
    return ErroAPI(status_code=status_code, codigo=exc.codigo, mensagem=exc.mensagem)


def _saida(anexo: Anexo) -> AnexoSaida:
    return AnexoSaida(
        id_anexo=anexo.id_anexo,
        nome_original=anexo.nome_original,
        mime_type=anexo.mime_type,
        tamanho_bytes=anexo.tamanho_bytes,
        data_envio=anexo.data_envio,
    )


@router.post(
    "/api/chamados/{id_chamado}/anexos",
    response_model=AnexoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Envia um anexo ao chamado (multipart)",
)
async def enviar(
    id_chamado: int,
    servico: AnexoServiceDep,
    usuario: UsuarioAtualDep,
    arquivo: Annotated[UploadFile, File(description="PNG, JPG ou PDF, até 10 MB.")],
) -> AnexoSaida:
    conteudo = await arquivo.read()
    try:
        anexo = servico.anexar(
            usuario=usuario,
            id_chamado=id_chamado,
            nome_original=arquivo.filename or "arquivo",
            conteudo=conteudo,
        )
    except ErroAnexo as exc:
        raise _erro_http(exc) from exc
    return _saida(anexo)


@router.get(
    "/api/chamados/{id_chamado}/anexos",
    response_model=list[AnexoSaida],
    summary="Lista os anexos do chamado",
)
def listar(id_chamado: int, servico: AnexoServiceDep, usuario: UsuarioAtualDep) -> list[AnexoSaida]:
    try:
        anexos = servico.listar(usuario=usuario, id_chamado=id_chamado)
    except ErroAnexo as exc:
        raise _erro_http(exc) from exc
    return [_saida(a) for a in anexos]


@router.get("/api/anexos/{id_anexo}/download", summary="Baixa o anexo (stream)")
def download(
    id_anexo: int, servico: AnexoServiceDep, usuario: UsuarioAtualDep
) -> StreamingResponse:
    try:
        baixado = servico.obter_para_download(usuario=usuario, id_anexo=id_anexo)
    except ErroAnexo as exc:
        raise _erro_http(exc) from exc

    anexo = baixado.anexo
    nome = quote(anexo.nome_original)
    return StreamingResponse(
        baixado.storage.abrir_stream(anexo.chave_objeto),
        media_type=anexo.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{nome}",
            "Content-Length": str(anexo.tamanho_bytes),
        },
    )
