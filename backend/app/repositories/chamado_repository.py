"""Repositório de chamados (abertura na F2.1; lista, contadores, resumo e detalhe na F2.2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import ColumnElement, Select, case, func, select
from sqlalchemy.orm import Session

from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.enums import CanalOrigem, SeveridadeChamado, StatusChamado
from app.entities.usuario import Usuario

# Status de cada grupo das abas/indicadores (seção 6.1).
STATUS_POR_GRUPO: dict[str, tuple[StatusChamado, ...]] = {
    "abertos": (StatusChamado.NOVO, StatusChamado.PENDENTE),
    "em_andamento": (StatusChamado.ATRIBUIDO,),
    "resolvidos": (StatusChamado.CONCLUIDO,),
    "encerrados": (StatusChamado.FECHADO,),
}

# Status "ainda não resolvidos" (para o critério de urgência e da ordenação, 6.5).
_NAO_RESOLVIDOS = (StatusChamado.NOVO, StatusChamado.PENDENTE, StatusChamado.ATRIBUIDO)

# Termo com forma de protocolo: TK-0051, tk51, 0051, 51 (sem diferenciar caixa).
_RE_PROTOCOLO = re.compile(r"^(?:tk-?)?0*(\d+)$", re.IGNORECASE)


def _numero_protocolo(q: str) -> int | None:
    """Extrai o id do chamado quando o termo tem forma de protocolo (6.5)."""
    m = _RE_PROTOCOLO.match(q.strip())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _escapar_like(termo: str) -> str:
    """Escapa `\\`, `%` e `_` para o LIKE (a busca é por substring literal)."""
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@dataclass(frozen=True)
class LinhaChamado:
    """Chamado + entidades relacionadas + qtd_mensagens, para montar a resposta."""

    chamado: Chamado
    categoria: Categoria
    solicitante: Usuario
    tecnico: Usuario | None
    qtd_mensagens: int


class ChamadoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    # ----- Abertura (F2.1) -----
    def criar(
        self,
        *,
        id_usuario_abertura: int,
        id_categoria: int,
        titulo: str,
        descricao: str,
        severidade: SeveridadeChamado,
        canal_origem: CanalOrigem = CanalOrigem.PORTAL,
    ) -> Chamado:
        chamado = Chamado(
            id_usuario_abertura=id_usuario_abertura,
            id_categoria=id_categoria,
            titulo=titulo.strip(),
            descricao=descricao.strip(),
            severidade=severidade,
            canal_origem=canal_origem,
        )
        self._sessao.add(chamado)
        self._sessao.flush()
        self._sessao.refresh(chamado)
        return chamado

    def buscar_categoria(self, id_categoria: int) -> Categoria | None:
        return self._sessao.get(Categoria, id_categoria)

    def buscar_solicitante(self, id_usuario: int) -> Usuario | None:
        return self._sessao.get(Usuario, id_usuario)

    def buscar_por_id(self, id_chamado: int) -> Chamado | None:
        """Chamado por id (sem escopo), para o ciclo de vida (F4)."""
        return self._sessao.get(Chamado, id_chamado)

    def flush(self) -> None:
        """Descarrega as mudanças pendentes (ex.: transições que mutam o Chamado)."""
        self._sessao.flush()

    # ----- Consulta (F2.2) -----
    def _condicoes(
        self,
        *,
        id_solicitante: int | None,
        q: str | None,
        grupo: str | None,
        id_categoria: int | None,
    ) -> list[ColumnElement[bool]]:
        cond: list[ColumnElement[bool]] = []
        # Escopo por perfil (RN06): CLIENTE só os seus.
        if id_solicitante is not None:
            cond.append(Chamado.id_usuario_abertura == id_solicitante)
        if id_categoria is not None:
            cond.append(Chamado.id_categoria == id_categoria)
        if q and q.strip():
            termo = q.strip()
            like = f"%{_escapar_like(termo.lower())}%"
            busca_titulo = func.f_unaccent(func.lower(Chamado.titulo)).like(
                func.f_unaccent(like), escape="\\"
            )
            numero = _numero_protocolo(termo)
            cond.append(
                busca_titulo | (Chamado.id_chamado == numero)
                if numero is not None
                else busca_titulo
            )
        if grupo and grupo in STATUS_POR_GRUPO:
            cond.append(Chamado.status_chamado.in_(STATUS_POR_GRUPO[grupo]))
        return cond

    def listar(
        self,
        *,
        id_solicitante: int | None,
        q: str | None = None,
        grupo: str | None = None,
        id_categoria: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[LinhaChamado], int]:
        """Lista paginada no escopo dado (None = todos; int = só do solicitante).

        Ordem (6.5): CRITICO ainda não resolvido primeiro, depois `data_criacao` desc.
        `qtd_mensagens` é 0 na F2.2 (a tabela de follow-ups chega na F4).
        """
        cond = self._condicoes(
            id_solicitante=id_solicitante, q=q, grupo=grupo, id_categoria=id_categoria
        )

        total = int(
            self._sessao.scalar(select(func.count()).select_from(Chamado).where(*cond)) or 0
        )

        urgente_primeiro = case(
            (
                (Chamado.severidade == SeveridadeChamado.CRITICO)
                & Chamado.status_chamado.in_(_NAO_RESOLVIDOS),
                0,
            ),
            else_=1,
        )
        consulta: Select[tuple[Chamado, Categoria, Usuario]] = (
            select(Chamado, Categoria, Usuario)
            .join(Categoria, Chamado.id_categoria == Categoria.id_categoria)
            .join(Usuario, Chamado.id_usuario_abertura == Usuario.id_usuario)
            .where(*cond)
            .order_by(
                urgente_primeiro.asc(), Chamado.data_criacao.desc(), Chamado.id_chamado.desc()
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        linhas: list[LinhaChamado] = []
        for chamado, categoria, solicitante in self._sessao.execute(consulta).all():
            tecnico = (
                self._sessao.get(Usuario, chamado.id_tecnico_responsavel)
                if chamado.id_tecnico_responsavel is not None
                else None
            )
            linhas.append(
                LinhaChamado(
                    chamado=chamado,
                    categoria=categoria,
                    solicitante=solicitante,
                    tecnico=tecnico,
                    qtd_mensagens=0,
                )
            )
        return linhas, total

    def contadores(
        self,
        *,
        id_solicitante: int | None,
        q: str | None = None,
        id_categoria: int | None = None,
    ) -> dict[str, int]:
        """Contadores das abas (6.5): respeitam busca e categoria, **ignoram** o grupo.
        Calculados numa única consulta com `count(*) FILTER (WHERE ...)`."""
        cond = self._condicoes(
            id_solicitante=id_solicitante, q=q, grupo=None, id_categoria=id_categoria
        )

        def filtro_grupo(grupo: str) -> ColumnElement[int]:
            return func.count().filter(Chamado.status_chamado.in_(STATUS_POR_GRUPO[grupo]))

        consulta = select(
            func.count().label("todos"),
            filtro_grupo("abertos").label("abertos"),
            filtro_grupo("em_andamento").label("em_andamento"),
            filtro_grupo("resolvidos").label("resolvidos"),
            filtro_grupo("encerrados").label("encerrados"),
        ).where(*cond)
        linha = self._sessao.execute(consulta).one()
        return {
            "todos": int(linha.todos),
            "abertos": int(linha.abertos),
            "em_andamento": int(linha.em_andamento),
            "resolvidos": int(linha.resolvidos),
            "encerrados": int(linha.encerrados),
        }

    def resumo(self, *, id_solicitante: int | None) -> dict[str, int]:
        """Indicadores do Dashboard (seção 7.3): abertos, em_andamento, resolvidos,
        encerrados e urgentes (CRITICO ainda não resolvido)."""
        cond = self._condicoes(id_solicitante=id_solicitante, q=None, grupo=None, id_categoria=None)

        def filtro_grupo(grupo: str) -> ColumnElement[int]:
            return func.count().filter(Chamado.status_chamado.in_(STATUS_POR_GRUPO[grupo]))

        urgentes = func.count().filter(
            (Chamado.severidade == SeveridadeChamado.CRITICO)
            & Chamado.status_chamado.in_(_NAO_RESOLVIDOS)
        )
        consulta = select(
            filtro_grupo("abertos").label("abertos"),
            filtro_grupo("em_andamento").label("em_andamento"),
            filtro_grupo("resolvidos").label("resolvidos"),
            filtro_grupo("encerrados").label("encerrados"),
            urgentes.label("urgentes"),
        ).where(*cond)
        linha = self._sessao.execute(consulta).one()
        return {
            "abertos": int(linha.abertos),
            "em_andamento": int(linha.em_andamento),
            "resolvidos": int(linha.resolvidos),
            "encerrados": int(linha.encerrados),
            "urgentes": int(linha.urgentes),
        }

    def obter(self, id_chamado: int, *, id_solicitante: int | None) -> LinhaChamado | None:
        """Detalhe por id no escopo dado. None se não existe ou está fora do escopo
        (o controller converte em 404 — RN06, seção 6.4)."""
        cond: list[ColumnElement[bool]] = [Chamado.id_chamado == id_chamado]
        if id_solicitante is not None:
            cond.append(Chamado.id_usuario_abertura == id_solicitante)
        consulta = (
            select(Chamado, Categoria, Usuario)
            .join(Categoria, Chamado.id_categoria == Categoria.id_categoria)
            .join(Usuario, Chamado.id_usuario_abertura == Usuario.id_usuario)
            .where(*cond)
        )
        linha = self._sessao.execute(consulta).one_or_none()
        if linha is None:
            return None
        chamado, categoria, solicitante = linha
        tecnico = (
            self._sessao.get(Usuario, chamado.id_tecnico_responsavel)
            if chamado.id_tecnico_responsavel is not None
            else None
        )
        return LinhaChamado(
            chamado=chamado,
            categoria=categoria,
            solicitante=solicitante,
            tecnico=tecnico,
            qtd_mensagens=0,
        )
