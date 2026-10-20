"""Service de cadastro e consulta de usuários (UC01, RF01, RN07; seção 11).

Regras implementadas:
- `cadastrar` (RN07, TU05, TU06): e-mail único (normalizado em minúsculas) e senha
  válida (8..72 bytes, gravada só como hash BCrypt). E-mail duplicado →
  `EMAIL_DUPLICADO`; senha fraca → `VALIDACAO`.
- `listar` (UC01): lista paginada com filtros `q`, `perfil` e `ativo`.
- `obter` (UC01): detalhe por id; `NAO_ENCONTRADO` quando não existe.

O service não conhece HTTP: recebe o repositório por injeção e levanta
`ErroUsuario` (código estável) para o controller traduzir ao formato único (7.1).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.seguranca import SenhaInvalida, gerar_hash_senha
from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository


class ErroUsuario(Exception):
    """Erro de domínio do cadastro/consulta de usuário, com código estável."""

    def __init__(self, codigo: str, mensagem: str, campo: str | None = None) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.campo = campo


@dataclass(frozen=True)
class PaginaUsuarios:
    items: list[Usuario]
    total: int
    page: int
    page_size: int


class UsuarioService:
    def __init__(self, *, usuarios: UsuarioRepository) -> None:
        self._usuarios = usuarios

    def cadastrar(
        self,
        *,
        nome: str,
        email: str,
        senha: str,
        tipo_perfil: PerfilUsuario,
        cargo: str | None = None,
    ) -> Usuario:
        """Cadastra um usuário (RN07, TU05, TU06). Só o ADMIN usa esta operação (UC01)."""
        email_normalizado = email.strip().lower()
        # RN07 / TU05: e-mail único. Checagem explícita para a mensagem de contrato;
        # o UNIQUE do banco continua sendo a última barreira.
        if self._usuarios.existe_email(email_normalizado):
            raise ErroUsuario("EMAIL_DUPLICADO", "Este e-mail já está cadastrado.", campo="email")
        # TU06: valida a senha e gera o hash (a senha nunca é persistida em claro).
        try:
            senha_hash = gerar_hash_senha(senha)
        except SenhaInvalida as exc:
            raise ErroUsuario("VALIDACAO", str(exc), campo="senha") from exc

        return self._usuarios.criar(
            nome=nome,
            email=email_normalizado,
            senha_hash=senha_hash,
            tipo_perfil=tipo_perfil,
            cargo=cargo,
        )

    def listar(
        self,
        *,
        q: str | None = None,
        perfil: PerfilUsuario | None = None,
        ativo: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginaUsuarios:
        itens, total = self._usuarios.listar(
            q=q, perfil=perfil, ativo=ativo, page=page, page_size=page_size
        )
        return PaginaUsuarios(items=itens, total=total, page=page, page_size=page_size)

    def obter(self, id_usuario: int) -> Usuario:
        usuario = self._usuarios.buscar_por_id(id_usuario)
        if usuario is None:
            raise ErroUsuario("NAO_ENCONTRADO", "Usuário não encontrado.")
        return usuario

    def atualizar(
        self,
        *,
        id_usuario: int,
        id_ator: int,
        nome: str | None = None,
        cargo: str | None = None,
        tipo_perfil: PerfilUsuario | None = None,
        ativo: bool | None = None,
    ) -> Usuario:
        """Atualiza nome, cargo, perfil e `ativo` (exclusão lógica). Só o ADMIN usa.

        Salvaguarda: o ADMIN não pode **desativar nem rebaixar a si mesmo** (evita
        perder o próprio acesso / ficar sem administrador). Campos nulos não mudam.
        """
        usuario = self._usuarios.buscar_por_id(id_usuario)
        if usuario is None:
            raise ErroUsuario("NAO_ENCONTRADO", "Usuário não encontrado.")

        if id_usuario == id_ator:
            if ativo is False:
                raise ErroUsuario("VALIDACAO", "Você não pode desativar a si mesmo.", campo="ativo")
            if tipo_perfil is not None and tipo_perfil != PerfilUsuario.ADMIN:
                raise ErroUsuario(
                    "VALIDACAO", "Você não pode rebaixar o próprio perfil.", campo="tipo_perfil"
                )

        if nome is not None:
            nome_limpo = nome.strip()
            if not nome_limpo:
                raise ErroUsuario("VALIDACAO", "O nome não pode ficar vazio.", campo="nome")
            usuario.nome = nome_limpo
        if cargo is not None:
            usuario.cargo = cargo.strip() or None
        if tipo_perfil is not None:
            usuario.tipo_perfil = tipo_perfil
        if ativo is not None:
            usuario.ativo = ativo
        self._usuarios.flush()
        return usuario
