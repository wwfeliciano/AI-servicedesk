"""Schemas (Pydantic v2) de entrada e saída da autenticação (contratos da seção 7.3)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class UsuarioPublico(BaseModel):
    id_usuario: int
    nome: str
    email: str
    tipo_perfil: str
    cargo: str | None = None
    # Canais externos (F6.3): preferências e status do vínculo de WhatsApp.
    notificar_email: bool = True
    whatsapp_opt_in: bool = False
    whatsapp_vinculado: bool = False


class LoginSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioPublico


class TrocaSenhaEntrada(BaseModel):
    senha_atual: str = Field(min_length=1)
    senha_nova: str = Field(min_length=1)


class EsqueciSenhaEntrada(BaseModel):
    email: EmailStr


class RedefinirSenhaEntrada(BaseModel):
    token: str = Field(min_length=1)
    senha_nova: str = Field(min_length=1)


class MensagemSaida(BaseModel):
    mensagem: str
