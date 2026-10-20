"""Service de autenticação (UC01, RF01, RNF01, seção 11).

Concentra as regras de login, rotação de refresh token, logout e troca de senha.
Não conhece HTTP: recebe os repositórios e o limitador por injeção e devolve dados
ou levanta exceções de domínio (`ErroAutenticacao`). O controller traduz para HTTP.

Regras implementadas (seção 11):
- Login (RNF01, FE01): mensagem genérica em caso de e-mail inexistente, senha
  errada ou usuário inativo; limite de 5 tentativas por IP e por e-mail em 15 min
  (→ `MUITAS_TENTATIVAS`).
- Refresh: rotação a cada uso; o token antigo é revogado e um novo nasce na mesma
  família. Reuso de um token já revogado derruba a família inteira.
- Troca de senha: confere a senha atual, valida a nova (TU06) e revoga todas as
  sessões (famílias) do usuário.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from app.core.rate_limit import LimiteTentativasLogin
from app.core.seguranca import (
    SenhaInvalida,
    TokenInvalido,
    conferir_senha,
    decodificar_access_token,
    gerar_access_token,
    gerar_hash_senha,
    gerar_refresh_token,
    hash_refresh_token,
    nova_familia,
)
from app.entities.usuario import Usuario
from app.repositories.token_redefinicao_repository import TokenRedefinicaoRepository
from app.repositories.token_refresh_repository import TokenRefreshRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.evento_service import EventoService


class ErroAutenticacao(Exception):
    """Erro de domínio da autenticação, com um código estável para o controller."""

    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


# Mensagem única de credenciais inválidas (FE01): nunca diz qual campo errou.
_MSG_CREDENCIAL = "E-mail ou senha inválidos."
_MSG_SESSAO = "Sessão inválida ou expirada. Entre novamente."


@dataclass(frozen=True)
class ResultadoLogin:
    access_token: str
    expires_in: int
    refresh_token: str
    usuario: Usuario


@dataclass(frozen=True)
class ResultadoRefresh:
    access_token: str
    expires_in: int
    refresh_token: str
    usuario: Usuario


def _agora() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


class AuthService:
    def __init__(
        self,
        *,
        usuarios: UsuarioRepository,
        tokens: TokenRefreshRepository,
        limite_login: LimiteTentativasLogin,
        refresh_dias: int,
        redefinicao: TokenRedefinicaoRepository | None = None,
        eventos: EventoService | None = None,
        portal_url: str = "http://localhost:8180",
    ) -> None:
        self._usuarios = usuarios
        self._tokens = tokens
        self._limite = limite_login
        self._refresh_dias = refresh_dias
        self._redefinicao = redefinicao
        self._eventos = eventos
        self._portal_url = portal_url.rstrip("/")

    # ----- Login -----
    def login(self, *, email: str, senha: str, ip: str) -> ResultadoLogin:
        if self._limite.bloqueado(ip=ip, email=email):
            raise ErroAutenticacao(
                "MUITAS_TENTATIVAS", "Muitas tentativas. Aguarde alguns minutos."
            )

        usuario = self._usuarios.buscar_por_email(email)
        # Mesma resposta genérica para e-mail inexistente, senha errada e inativo.
        if usuario is None or not conferir_senha(senha, usuario.senha_hash) or not usuario.ativo:
            self._limite.registrar_falha(ip=ip, email=email)
            raise ErroAutenticacao("CREDENCIAL_INVALIDA", _MSG_CREDENCIAL)

        self._limite.limpar(ip=ip, email=email)
        access_token, expires_in = gerar_access_token(
            id_usuario=usuario.id_usuario, perfil=usuario.tipo_perfil.value
        )
        refresh_token = self._emitir_refresh(id_usuario=usuario.id_usuario, familia=nova_familia())
        return ResultadoLogin(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            usuario=usuario,
        )

    # ----- Refresh (rotação) -----
    def refresh(self, *, refresh_token: str) -> ResultadoRefresh:
        if not refresh_token:
            raise ErroAutenticacao("NAO_AUTENTICADO", _MSG_SESSAO)

        registro = self._tokens.buscar_por_hash(hash_refresh_token(refresh_token))
        if registro is None:
            raise ErroAutenticacao("NAO_AUTENTICADO", _MSG_SESSAO)

        agora = _agora()

        # Reuso de um token já revogado: ataque em potencial → derruba a família.
        if registro.revogado_em is not None:
            self._tokens.revogar_familia(registro.familia, agora)
            raise ErroAutenticacao("NAO_AUTENTICADO", _MSG_SESSAO)

        if registro.expira_em <= agora:
            self._tokens.revogar(registro, agora)
            raise ErroAutenticacao("NAO_AUTENTICADO", _MSG_SESSAO)

        usuario = self._usuarios.buscar_por_id(registro.id_usuario)
        if usuario is None or not usuario.ativo:
            self._tokens.revogar_familia(registro.familia, agora)
            raise ErroAutenticacao("NAO_AUTENTICADO", _MSG_SESSAO)

        # Rotação: revoga o atual e emite um novo na mesma família.
        self._tokens.revogar(registro, agora)
        novo_refresh = self._emitir_refresh(id_usuario=usuario.id_usuario, familia=registro.familia)
        access_token, expires_in = gerar_access_token(
            id_usuario=usuario.id_usuario, perfil=usuario.tipo_perfil.value
        )
        return ResultadoRefresh(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=novo_refresh,
            usuario=usuario,
        )

    # ----- Logout -----
    def logout(self, *, refresh_token: str | None) -> None:
        """Revoga a família do refresh token, se houver. Idempotente."""
        if not refresh_token:
            return
        registro = self._tokens.buscar_por_hash(hash_refresh_token(refresh_token))
        if registro is not None:
            self._tokens.revogar_familia(registro.familia, _agora())

    # ----- Usuário atual (a partir do access token) -----
    def usuario_do_access_token(self, token: str) -> Usuario:
        """Decodifica o token, recarrega o usuário do banco e recusa se inativo."""
        try:
            payload = decodificar_access_token(token)
        except TokenInvalido as exc:
            raise ErroAutenticacao("NAO_AUTENTICADO", "Não autenticado.") from exc

        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub.isdigit():
            raise ErroAutenticacao("NAO_AUTENTICADO", "Não autenticado.")

        usuario = self._usuarios.buscar_por_id(int(sub))
        if usuario is None or not usuario.ativo:
            raise ErroAutenticacao("NAO_AUTENTICADO", "Não autenticado.")
        return usuario

    # ----- Troca de senha -----
    def trocar_senha(self, *, usuario: Usuario, senha_atual: str, senha_nova: str) -> None:
        if not conferir_senha(senha_atual, usuario.senha_hash):
            raise ErroAutenticacao("CREDENCIAL_INVALIDA", "A senha atual está incorreta.")
        try:
            novo_hash = gerar_hash_senha(senha_nova)
        except SenhaInvalida as exc:
            raise ErroAutenticacao("VALIDACAO", str(exc)) from exc

        usuario.senha_hash = novo_hash
        # Revoga todas as sessões ativas do usuário (todas as famílias).
        self._tokens.revogar_do_usuario(usuario.id_usuario, _agora())

    # ----- Redefinição por e-mail (FA02, F7.1) -----
    def solicitar_redefinicao(self, *, email: str) -> None:
        """Gera um token de redefinição e enfileira o e-mail. **Sempre silencioso**:
        não revela se o e-mail existe (resposta genérica no controller). Só gera para
        usuário ativo."""
        if self._redefinicao is None:
            return
        usuario = self._usuarios.buscar_por_email(email)
        if usuario is None or not usuario.ativo:
            return  # não revela a existência da conta
        token = gerar_refresh_token()  # opaco, 256 bits
        expira_em = _agora() + datetime.timedelta(minutes=30)
        self._redefinicao.criar(
            id_usuario=usuario.id_usuario,
            token_hash=hash_refresh_token(token),
            expira_em=expira_em,
        )
        if self._eventos is not None:
            self._eventos.senha_redefinicao(usuario=usuario, token=token)

    def redefinir(self, *, token: str, senha_nova: str) -> None:
        """Valida o token (não usado, não expirado), troca a senha, marca o token
        como usado e revoga todas as sessões. Token inválido → `TOKEN_INVALIDO`."""
        if self._redefinicao is None or not token:
            raise ErroAutenticacao("TOKEN_INVALIDO", "Link de redefinição inválido ou expirado.")
        registro = self._redefinicao.buscar_por_hash(hash_refresh_token(token))
        agora = _agora()
        if registro is None or registro.usado_em is not None or registro.expira_em <= agora:
            raise ErroAutenticacao("TOKEN_INVALIDO", "Link de redefinição inválido ou expirado.")
        usuario = self._usuarios.buscar_por_id(registro.id_usuario)
        if usuario is None or not usuario.ativo:
            raise ErroAutenticacao("TOKEN_INVALIDO", "Link de redefinição inválido ou expirado.")
        try:
            novo_hash = gerar_hash_senha(senha_nova)
        except SenhaInvalida as exc:
            raise ErroAutenticacao("VALIDACAO", str(exc)) from exc
        usuario.senha_hash = novo_hash
        self._redefinicao.marcar_usado(registro, agora)
        self._tokens.revogar_do_usuario(usuario.id_usuario, agora)

    # ----- Internos -----
    def _emitir_refresh(self, *, id_usuario: int, familia: uuid.UUID) -> str:
        refresh_token = gerar_refresh_token()
        expira_em = _agora() + datetime.timedelta(days=self._refresh_dias)
        self._tokens.criar(
            id_usuario=id_usuario,
            token_hash=hash_refresh_token(refresh_token),
            familia=familia,
            expira_em=expira_em,
        )
        return refresh_token
