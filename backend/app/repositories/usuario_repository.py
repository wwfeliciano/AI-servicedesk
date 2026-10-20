"""Repositório de usuários (consultas da autenticação e do cadastro, F1)."""

from __future__ import annotations

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario


class UsuarioRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def buscar_por_email(self, email: str) -> Usuario | None:
        """Busca por e-mail normalizado (minúsculas). None se não existir."""
        consulta = select(Usuario).where(Usuario.email == email.strip().lower())
        return self._sessao.scalars(consulta).one_or_none()

    def buscar_por_id(self, id_usuario: int) -> Usuario | None:
        return self._sessao.get(Usuario, id_usuario)

    def atualizar_preferencias(
        self,
        usuario: Usuario,
        *,
        notificar_email: bool | None = None,
        whatsapp_opt_in: bool | None = None,
    ) -> Usuario:
        """Atualiza as preferências de notificação (F6.3).

        `whatsapp_opt_in=False` desliga o canal WhatsApp sem apagar o vínculo (o
        usuário pode religar). O opt-in só vale de fato se houver `whatsapp_chat_id`.
        """
        if notificar_email is not None:
            usuario.notificar_email = notificar_email
        if whatsapp_opt_in is not None:
            usuario.whatsapp_opt_in = whatsapp_opt_in
        self._sessao.flush()
        return usuario

    def desvincular_whatsapp(self, usuario: Usuario) -> Usuario:
        """Remove o vínculo de WhatsApp e desliga o opt-in (opt-out, seção 9.4)."""
        usuario.whatsapp_chat_id = None
        usuario.whatsapp_lid = None
        usuario.whatsapp_numero = None
        usuario.whatsapp_opt_in = False
        usuario.whatsapp_consentimento_em = None
        self._sessao.flush()
        return usuario

    def buscar_por_whatsapp(
        self, *, chat_id: str | None, lid: str | None = None, numero: str | None = None
    ) -> Usuario | None:
        """Usuário **ativo** identificado pelo WhatsApp (seção 9.3): tenta por
        `whatsapp_chat_id`, depois `whatsapp_lid`, depois `whatsapp_numero`."""
        for coluna, valor in (
            (Usuario.whatsapp_chat_id, chat_id),
            (Usuario.whatsapp_lid, lid),
            (Usuario.whatsapp_numero, numero),
        ):
            if not valor:
                continue
            achado = self._sessao.scalars(
                select(Usuario).where(coluna == valor, Usuario.ativo.is_(True))
            ).one_or_none()
            if achado is not None:
                return achado
        return None

    def vincular_whatsapp(
        self,
        usuario: Usuario,
        *,
        chat_id: str,
        lid: str | None = None,
        numero: str | None = None,
    ) -> Usuario:
        """Completa o vínculo (bot, seção 9.4): grava chat_id/lid/numero, liga o
        opt-in e registra o consentimento."""
        from datetime import UTC, datetime

        usuario.whatsapp_chat_id = chat_id
        usuario.whatsapp_lid = lid
        usuario.whatsapp_numero = numero
        usuario.whatsapp_opt_in = True
        usuario.whatsapp_consentimento_em = datetime.now(UTC)
        self._sessao.flush()
        return usuario

    def flush(self) -> None:
        """Descarrega mudanças pendentes (ex.: PATCH de usuário)."""
        self._sessao.flush()

    def ids_tecnicos_ativos(self) -> list[int]:
        """Ids dos ANALISTA e ADMIN ativos (destinatários de alertas, ex.: urgente)."""
        consulta = select(Usuario.id_usuario).where(
            Usuario.ativo.is_(True),
            Usuario.tipo_perfil.in_([PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN]),
        )
        return [int(i) for i in self._sessao.scalars(consulta).all()]

    def buscar_tecnico_ativo(self, id_usuario: int) -> Usuario | None:
        """Usuário ANALISTA ou ADMIN **ativo** pelo id (RN03). None caso contrário."""
        consulta = select(Usuario).where(
            Usuario.id_usuario == id_usuario,
            Usuario.ativo.is_(True),
            Usuario.tipo_perfil.in_([PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN]),
        )
        return self._sessao.scalars(consulta).one_or_none()

    def listar_tecnicos_ativos(self) -> list[Usuario]:
        """ANALISTA e ADMIN ativos, ordenados por nome (para a tela de atribuição)."""
        consulta = (
            select(Usuario)
            .where(
                Usuario.ativo.is_(True),
                Usuario.tipo_perfil.in_([PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN]),
            )
            .order_by(Usuario.nome.asc())
        )
        return list(self._sessao.scalars(consulta).all())

    def existe_email(self, email: str) -> bool:
        """True se já há usuário com o e-mail (normalizado), ativo ou não (RN07)."""
        consulta = (
            select(func.count()).select_from(Usuario).where(Usuario.email == email.strip().lower())
        )
        return bool(self._sessao.scalar(consulta))

    def criar(
        self,
        *,
        nome: str,
        email: str,
        senha_hash: str,
        tipo_perfil: PerfilUsuario,
        cargo: str | None = None,
    ) -> Usuario:
        """Insere um usuário. O e-mail é gravado sempre em minúsculas (RN07)."""
        usuario = Usuario(
            nome=nome.strip(),
            email=email.strip().lower(),
            senha_hash=senha_hash,
            tipo_perfil=tipo_perfil,
            cargo=cargo.strip() if cargo and cargo.strip() else None,
        )
        self._sessao.add(usuario)
        self._sessao.flush()
        return usuario

    def _condicoes(
        self,
        *,
        q: str | None,
        perfil: PerfilUsuario | None,
        ativo: bool | None,
    ) -> list[ColumnElement[bool]]:
        condicoes: list[ColumnElement[bool]] = []
        if q:
            termo = f"%{q.strip().lower()}%"
            condicoes.append(
                func.lower(Usuario.nome).like(termo) | func.lower(Usuario.email).like(termo)
            )
        if perfil is not None:
            condicoes.append(Usuario.tipo_perfil == perfil)
        if ativo is not None:
            condicoes.append(Usuario.ativo.is_(ativo))
        return condicoes

    def listar(
        self,
        *,
        q: str | None = None,
        perfil: PerfilUsuario | None = None,
        ativo: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Usuario], int]:
        """Lista paginada com filtros `q` (nome/e-mail), `perfil` e `ativo`.

        Devolve `(itens, total)`. Ordena por nome e, em empate, por id.
        """
        condicoes = self._condicoes(q=q, perfil=perfil, ativo=ativo)

        total_consulta = select(func.count()).select_from(Usuario).where(*condicoes)
        total = int(self._sessao.scalar(total_consulta) or 0)

        itens_consulta = (
            select(Usuario)
            .where(*condicoes)
            .order_by(Usuario.nome.asc(), Usuario.id_usuario.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        itens = list(self._sessao.scalars(itens_consulta).all())
        return itens, total
