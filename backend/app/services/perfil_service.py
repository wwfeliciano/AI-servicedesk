"""Service do Perfil — vínculo de WhatsApp e preferências de notificação (F6.3).

Seção 9.4: o vínculo exige **consentimento** explícito. A API gera um código de
6 dígitos (Redis, TTL 10 min, guardado como hash) e devolve o link `wa.me` com o
texto `VINCULAR <codigo>`; o bot (F6.4) completa o vínculo ao receber a mensagem.
Opt-out a qualquer momento (desvincular).

Não conhece HTTP: levanta `ErroPerfil` com código estável.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.core.vinculo_whatsapp import TTL_SEGUNDOS, VinculoWhatsApp
from app.entities.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository


class ErroPerfil(Exception):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass(frozen=True)
class VinculoGerado:
    codigo: str
    link_wa: str
    expira_em_segundos: int


@dataclass(frozen=True)
class StatusVinculo:
    vinculado: bool
    numero: str | None
    opt_in: bool
    notificar_email: bool


class PerfilService:
    def __init__(
        self,
        *,
        usuarios: UsuarioRepository,
        vinculo: VinculoWhatsApp,
        numero_suporte: str,
    ) -> None:
        self._usuarios = usuarios
        self._vinculo = vinculo
        self._numero_suporte = numero_suporte.strip()

    def gerar_vinculo(self, usuario: Usuario, *, consentimento: bool) -> VinculoGerado:
        """Gera o código e o link `wa.me` (exige consentimento; seção 9.4)."""
        if not consentimento:
            raise ErroPerfil(
                "CONSENTIMENTO_OBRIGATORIO",
                "É necessário aceitar receber notificações e atender pelo WhatsApp.",
            )
        if not self._numero_suporte:
            raise ErroPerfil(
                "SUPORTE_SEM_WHATSAPP",
                "O WhatsApp de suporte não está configurado. Contate o TI.",
            )
        # Marca o consentimento já na geração (o vínculo efetivo é o bot, F6.4).
        usuario.whatsapp_opt_in = True
        self._usuarios.flush()
        codigo = self._vinculo.gerar(usuario.id_usuario)
        texto = quote(f"VINCULAR {codigo}")
        link = f"https://wa.me/{self._numero_suporte}?text={texto}"
        return VinculoGerado(codigo=codigo, link_wa=link, expira_em_segundos=TTL_SEGUNDOS)

    def status(self, usuario: Usuario) -> StatusVinculo:
        return StatusVinculo(
            vinculado=usuario.whatsapp_chat_id is not None,
            numero=usuario.whatsapp_numero,
            opt_in=usuario.whatsapp_opt_in,
            notificar_email=usuario.notificar_email,
        )

    def desvincular(self, usuario: Usuario) -> StatusVinculo:
        self._usuarios.desvincular_whatsapp(usuario)
        return self.status(usuario)

    def atualizar_preferencias(
        self,
        usuario: Usuario,
        *,
        notificar_email: bool | None = None,
        whatsapp_opt_in: bool | None = None,
    ) -> StatusVinculo:
        self._usuarios.atualizar_preferencias(
            usuario, notificar_email=notificar_email, whatsapp_opt_in=whatsapp_opt_in
        )
        return self.status(usuario)
