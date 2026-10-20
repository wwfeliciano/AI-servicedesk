"""Schemas (Pydantic v2) do cadastro e da consulta de usuários (seção 7.1, 7.3)."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, EmailStr, Field

from app.entities.enums import PerfilUsuario


class UsuarioCriar(BaseModel):
    """Corpo de POST /api/usuarios. A validação da força da senha fica no service (TU06)."""

    nome: str = Field(min_length=1, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=1)
    tipo_perfil: PerfilUsuario
    cargo: str | None = Field(default=None, max_length=100)


class UsuarioDetalhe(BaseModel):
    """Representação de leitura de um usuário (nunca inclui a senha)."""

    id_usuario: int
    nome: str
    email: str
    tipo_perfil: PerfilUsuario
    cargo: str | None = None
    ativo: bool
    data_cadastro: datetime.datetime


class PaginaUsuariosSaida(BaseModel):
    """Envelope de paginação da seção 7.1: items, total, page, page_size."""

    items: list[UsuarioDetalhe]
    total: int
    page: int
    page_size: int


class TecnicoSaida(BaseModel):
    """Técnico (ANALISTA/ADMIN ativo) para a atribuição de chamados (RN03)."""

    id_usuario: int
    nome: str
    tipo_perfil: PerfilUsuario


class UsuarioAtualizar(BaseModel):
    """Corpo de PATCH /api/usuarios/{id} (ADMIN). Campos ausentes não mudam."""

    nome: str | None = Field(default=None, max_length=150)
    cargo: str | None = Field(default=None, max_length=100)
    tipo_perfil: PerfilUsuario | None = None
    ativo: bool | None = None
