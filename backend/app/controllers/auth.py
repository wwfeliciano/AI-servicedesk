"""Controllers de autenticação (seção 7.2, F1.1).

- POST /api/auth/login   (público)      → access token + cookie de refresh
- POST /api/auth/refresh (cookie)        → novo access token; rotaciona o refresh
- POST /api/auth/logout  (autenticado)   → revoga o refresh e apaga o cookie
- GET  /api/auth/me      (autenticado)   → usuário atual
- PUT  /api/auth/senha   (autenticado)   → troca de senha (atual + nova)

O controller traduz HTTP ↔ service: lê o cookie/corpo, chama o `AuthService` e
converte `ErroAutenticacao` no formato único de erro (seção 7.1). A regra de
negócio fica no service.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.controllers.dependencias import AuthServiceDep, UsuarioAtualDep
from app.controllers.schemas_auth import (
    EsqueciSenhaEntrada,
    LoginEntrada,
    LoginSaida,
    MensagemSaida,
    RedefinirSenhaEntrada,
    TrocaSenhaEntrada,
    UsuarioPublico,
)
from app.core.config import obter_configuracao
from app.core.errors import ErroAPI
from app.entities.usuario import Usuario
from app.services.auth_service import ErroAutenticacao

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_REFRESH = "refresh_token"
COOKIE_PATH = "/api/auth"

# Mapa dos códigos de domínio → status HTTP do contrato (seção 7.1).
_STATUS_POR_CODIGO = {
    "CREDENCIAL_INVALIDA": status.HTTP_401_UNAUTHORIZED,
    "NAO_AUTENTICADO": status.HTTP_401_UNAUTHORIZED,
    "MUITAS_TENTATIVAS": status.HTTP_429_TOO_MANY_REQUESTS,
    "VALIDACAO": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "TOKEN_INVALIDO": status.HTTP_400_BAD_REQUEST,
}


def _erro_http(exc: ErroAutenticacao) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_401_UNAUTHORIZED)
    # O código NAO_AUTENTICADO e CREDENCIAL_INVALIDA usam o código padrão do status.
    codigo = "NAO_AUTENTICADO" if status_code == status.HTTP_401_UNAUTHORIZED else exc.codigo
    return ErroAPI(status_code=status_code, codigo=codigo, mensagem=exc.mensagem)


def _usuario_publico(usuario: Usuario) -> UsuarioPublico:
    return UsuarioPublico(
        id_usuario=usuario.id_usuario,
        nome=usuario.nome,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil.value,
        cargo=usuario.cargo,
        notificar_email=usuario.notificar_email,
        whatsapp_opt_in=usuario.whatsapp_opt_in,
        whatsapp_vinculado=usuario.whatsapp_chat_id is not None,
    )


def _gravar_cookie_refresh(response: Response, refresh_token: str) -> None:
    config = obter_configuracao()
    response.set_cookie(
        key=COOKIE_REFRESH,
        value=refresh_token,
        max_age=config.jwt_refresh_dias * 24 * 60 * 60,
        httponly=True,
        samesite="strict",
        secure=config.em_producao,
        path=COOKIE_PATH,
    )


@router.post("/login", response_model=LoginSaida, summary="Login (público)")
def login(
    dados: LoginEntrada, request: Request, response: Response, auth: AuthServiceDep
) -> LoginSaida:
    ip = request.client.host if request.client else "desconhecido"
    try:
        resultado = auth.login(email=str(dados.email), senha=dados.senha, ip=ip)
    except ErroAutenticacao as exc:
        raise _erro_http(exc) from exc

    _gravar_cookie_refresh(response, resultado.refresh_token)
    return LoginSaida(
        access_token=resultado.access_token,
        token_type="bearer",
        expires_in=resultado.expires_in,
        usuario=_usuario_publico(resultado.usuario),
    )


@router.post("/refresh", response_model=LoginSaida, summary="Novo access token (cookie)")
def refresh(request: Request, response: Response, auth: AuthServiceDep) -> LoginSaida:
    refresh_token = request.cookies.get(COOKIE_REFRESH, "")
    try:
        resultado = auth.refresh(refresh_token=refresh_token)
    except ErroAutenticacao as exc:
        # Em falha, remove o cookie inválido.
        response.delete_cookie(COOKIE_REFRESH, path=COOKIE_PATH)
        raise _erro_http(exc) from exc

    _gravar_cookie_refresh(response, resultado.refresh_token)
    return LoginSaida(
        access_token=resultado.access_token,
        token_type="bearer",
        expires_in=resultado.expires_in,
        usuario=_usuario_publico(resultado.usuario),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout (autenticado)")
def logout(
    request: Request, response: Response, auth: AuthServiceDep, _usuario: UsuarioAtualDep
) -> Response:
    refresh_token = request.cookies.get(COOKIE_REFRESH)
    auth.logout(refresh_token=refresh_token)
    response.delete_cookie(COOKIE_REFRESH, path=COOKIE_PATH)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UsuarioPublico, summary="Usuário atual (autenticado)")
def me(usuario: UsuarioAtualDep) -> UsuarioPublico:
    return _usuario_publico(usuario)


@router.put(
    "/senha",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Troca de senha (autenticado)",
)
def trocar_senha(
    dados: TrocaSenhaEntrada, response: Response, auth: AuthServiceDep, usuario: UsuarioAtualDep
) -> Response:
    try:
        auth.trocar_senha(
            usuario=usuario, senha_atual=dados.senha_atual, senha_nova=dados.senha_nova
        )
    except ErroAutenticacao as exc:
        raise _erro_http(exc) from exc
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# Resposta genérica do esqueci-senha: nunca revela se o e-mail existe (FA02).
_MSG_ESQUECI = "Se o e-mail estiver cadastrado, enviaremos um link para redefinir a senha."


@router.post(
    "/esqueci-senha",
    response_model=MensagemSaida,
    summary="Solicita redefinição de senha por e-mail (público)",
)
def esqueci_senha(dados: EsqueciSenhaEntrada, auth: AuthServiceDep) -> MensagemSaida:
    # Silencioso: sempre a mesma resposta, exista o e-mail ou não.
    auth.solicitar_redefinicao(email=str(dados.email))
    return MensagemSaida(mensagem=_MSG_ESQUECI)


@router.post(
    "/redefinir-senha",
    response_model=MensagemSaida,
    summary="Redefine a senha com o token do e-mail (público)",
)
def redefinir_senha(dados: RedefinirSenhaEntrada, auth: AuthServiceDep) -> MensagemSaida:
    try:
        auth.redefinir(token=dados.token, senha_nova=dados.senha_nova)
    except ErroAutenticacao as exc:
        raise _erro_http(exc) from exc
    return MensagemSaida(mensagem="Senha redefinida com sucesso. Entre com a nova senha.")
