"""Repositório de anexos (F3.1)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entities.anexo import Anexo


class AnexoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def contar_do_chamado(self, id_chamado: int) -> int:
        return int(
            self._sessao.scalar(
                select(func.count()).select_from(Anexo).where(Anexo.id_chamado == id_chamado)
            )
            or 0
        )

    def criar(
        self,
        *,
        id_chamado: int,
        id_autor: int,
        nome_original: str,
        chave_objeto: str,
        mime_type: str,
        tamanho_bytes: int,
        sha256: str,
    ) -> Anexo:
        anexo = Anexo(
            id_chamado=id_chamado,
            id_autor=id_autor,
            nome_original=nome_original,
            chave_objeto=chave_objeto,
            mime_type=mime_type,
            tamanho_bytes=tamanho_bytes,
            sha256=sha256,
        )
        self._sessao.add(anexo)
        self._sessao.flush()
        self._sessao.refresh(anexo)
        return anexo

    def listar_do_chamado(self, id_chamado: int) -> list[Anexo]:
        consulta = (
            select(Anexo)
            .where(Anexo.id_chamado == id_chamado)
            .order_by(Anexo.data_envio.asc(), Anexo.id_anexo.asc())
        )
        return list(self._sessao.scalars(consulta).all())

    def obter(self, id_anexo: int) -> Anexo | None:
        return self._sessao.get(Anexo, id_anexo)
