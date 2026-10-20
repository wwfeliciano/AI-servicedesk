"""Primitivas de segurança da autenticação (seção 11).

- Senha: BCrypt (biblioteca `bcrypt`), custo configurável (`BCRYPT_CUSTO`), mínimo
  de 8 caracteres e máximo de 72 bytes. A senha nunca aparece em log nem é devolvida.
- Access token: JWT HS256 com `JWT_SECRET` (>= 32 bytes), claims `sub`, `perfil`,
  `exp`, `iat` e `jti`.
- Refresh token: opaco (256 bits aleatórios), entregue ao cliente em claro e guardado
  no banco apenas como hash SHA-256.

Este módulo não conhece HTTP nem banco: só transforma valores. As regras de uso
(rotação, revogação de família, limite de tentativas) ficam no service.
"""

from __future__ import annotations

import datetime
import hashlib
import secrets
import uuid

import bcrypt
import jwt

from app.core.config import obter_configuracao

ALGORITMO_JWT = "HS256"
SENHA_MIN_CARACTERES = 8
SENHA_MAX_BYTES = 72  # limite do BCrypt
JWT_SECRET_MIN_BYTES = 32


class SenhaInvalida(ValueError):
    """Senha fora dos limites (seção 11): < 8 caracteres ou > 72 bytes."""


class TokenInvalido(Exception):
    """Access token ausente, malformado, expirado ou com assinatura inválida."""


def validar_forca_senha(senha: str) -> None:
    """Valida o tamanho da senha (TU06). Levanta `SenhaInvalida` se fora dos limites."""
    if len(senha) < SENHA_MIN_CARACTERES:
        raise SenhaInvalida("A senha deve ter ao menos 8 caracteres.")
    if len(senha.encode("utf-8")) > SENHA_MAX_BYTES:
        raise SenhaInvalida("A senha deve ter no máximo 72 bytes.")


def gerar_hash_senha(senha: str) -> str:
    """Gera o hash BCrypt da senha (prefixo `$2b$`). Valida a força antes."""
    validar_forca_senha(senha)
    custo = obter_configuracao().bcrypt_custo
    hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=custo))
    return hashed.decode("utf-8")


def conferir_senha(senha: str, hash_armazenado: str) -> bool:
    """Confere a senha contra o hash. Retorna False em qualquer inconsistência."""
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))
    except ValueError:
        # Hash malformado no banco: trata como não conferido, sem vazar o motivo.
        return False


def _agora() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


def gerar_access_token(*, id_usuario: int, perfil: str) -> tuple[str, int]:
    """Gera o access token JWT. Retorna (token, expires_in_segundos)."""
    config = obter_configuracao()
    expira_segundos = config.jwt_access_minutos * 60
    agora = _agora()
    claims = {
        "sub": str(id_usuario),
        "perfil": perfil,
        "iat": int(agora.timestamp()),
        "exp": int((agora + datetime.timedelta(seconds=expira_segundos)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(claims, config.jwt_secret, algorithm=ALGORITMO_JWT)
    return token, expira_segundos


def decodificar_access_token(token: str) -> dict[str, object]:
    """Decodifica e valida o access token. Levanta `TokenInvalido` se inválido."""
    config = obter_configuracao()
    try:
        payload: dict[str, object] = jwt.decode(
            token, config.jwt_secret, algorithms=[ALGORITMO_JWT]
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalido(str(exc)) from exc
    return payload


def gerar_refresh_token() -> str:
    """Gera um refresh token opaco (256 bits aleatórios) em hexadecimal."""
    return secrets.token_hex(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 (hex, 64 caracteres) do refresh token, como guardado no banco."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def nova_familia() -> uuid.UUID:
    """Novo identificador de família para a cadeia de rotação."""
    return uuid.uuid4()
